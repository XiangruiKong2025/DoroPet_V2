from asyncio import new_event_loop, Event, run_coroutine_threadsafe, all_tasks, gather, current_task
from os import path
from contextlib import AsyncExitStack
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from threading import Thread
from platform import version, release

# msf 

def get_windows_version():
    # 获取系统版本信息
    version = platform.version()
    release = platform.release()
    
    # 获取详细的版本号
    major, minor, build = version.split('.')
    
    # 根据内部版本号判断
    build_number = int(build)
    
    if build_number >= 22000:
        return "Windows 11"
    elif build_number >= 10240:
        return "Windows 10"
    else:
        return "Windows 8.1 或更早版本"

class MCPClient:
    def __init__(self):
        """初始化 MCP 客户端"""
        self.exit_stack = AsyncExitStack()
        self.session = None
        self.sessions = []
        self.tools = None     
        self.loop = new_event_loop()
        self._initialized = Event()   # 初始化完成标志

        # 异步初始化（不阻塞主线程）
        run_coroutine_threadsafe(self._async_init(), self.loop)

        # 启动事件循环的线程（关键修复）
        self.loop_thread = Thread(target=self._run_loop, daemon=True)
        self.loop_thread.start()

        # theargs = ["--ignore-robots-txt", "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"]
        # self.loop.run_until_complete(self.connect_to_server3("MCP/mcp-server-fetch.exe", theargs))  

        # self.loop.run_until_complete(self.connect_to_server("MCP/bilibili-mcp-main/bilibili_mcp.py"))  
        # self.loop.run_until_complete(self.connect_to_server("MCP/fetch/src/mcp_server_fetch/server.py"))

        
    def _run_loop(self):
        """运行事件循环的主线程（在独立线程中执行）"""
        try:
            self.loop.run_forever()  # 持续运行循环，执行提交的任务
        finally:
            # 循环退出时清理
            # pass
            self.loop.close()

    async def _async_init(self):
        """真正的异步初始化逻辑"""
        print("MCP初始化")
        # await self.connect_to_server("MCP/fetch/src/mcp_server_fetch/server.py")

        theargs = ["-m", "mcp_server_fetch","--ignore-robots-txt", "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"]
        # result = get_windows_version()
        # print(f"当前系统: {result}")
        # if result == "Windows 10":
        #     await self.connect_to_server3("MCP/mcp-server-fetch-win10.exe", theargs)
        # if result == "Windows 11":
        #     await self.connect_to_server3("MCP/mcp-server-fetch-win11.exe", theargs)
        try:
            await self.connect_to_server3( theargs)
        except Exception as e:
                # 处理异常情况
                error_msg = f"MCP初始化 Error: {str(e)}"
                print(error_msg)
                return

        self._initialized.set()  # 标记初始化完成


    async def connect_to_server(self, server_script_path: str):
        """连接到 MCP 服务器并列出可用工具"""
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("服务器脚本必须是 .py 或 .js 文件")

        command = "python"if is_python else"node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        # 启动 MCP 服务器并建立通信
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # 列出 MCP 服务器上的工具
        response = await self.session.list_tools()
        self.tools = response.tools
        print("已连接到服务器，支持以下工具:", [tool.name for tool in self.tools])     
        
    async def connect_to_server2(self,  _args=[], _env=None):

        server_params = StdioServerParameters(
            command="uv",
            args=_args,
            env=_env
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        self.tools = response.tools
        print("已连接到MCP服务器，支持以下工具:", [tool.name for tool in self.tools])


    async def connect_to_server3(self, _args=[], _env=None):

        server_params = StdioServerParameters(
            command="uvx",
            args=_args,
            env=_env
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

        await self.session.initialize()

        response = await self.session.list_tools()
        self.tools = response.tools
        print("已连接到MCP服务器，支持以下工具:", [tool.name for tool in self.tools])

    def getAvailable_tools(self):
        if not self._initialized.is_set():
            print("MCP工具获取失败")
            return None
        coro = self.session.list_tools()
        future = run_coroutine_threadsafe(coro, self.loop)
        response = future.result()
        # response = self.loop.run_until_complete( self.session.list_tools())
        self.tools = response.tools
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
        } for tool in self.tools]
        # print(available_tools)
        return available_tools


    def getToolCall(self, tool_name, tool_args):
        coro = self.session.call_tool(tool_name, tool_args)
        future = run_coroutine_threadsafe(coro, self.loop)
        return future.result()  # 阻塞等待结果（可加 timeout）
        # return self.loop.run_until_complete( self.session.call_tool(tool_name, tool_args))
    
    # async def cleanup(self):
    #         # 取消所有未完成的任务
    #         tasks = [t for t in all_tasks(self.loop) if not t.done()]
    #         for task in tasks:
    #             task.cancel()
    #         await gather(*tasks, return_exceptions=True)

    #         # 关闭资源栈
    #         await self.exit_stack.aclose()

    #         # 停止并关闭事件循环
    #         if self.loop.is_running():
    #             self.loop.stop()
    #         self.loop.close()


    async def cleanup(self):
        tasks = [task for task in all_tasks() if task is not current_task()]
        for task in tasks:
            task.cancel()
        await gather(*tasks, return_exceptions=True)
        await self.exit_stack.aclose()



MCPClient_client = None

def get_MCPClient():
    global MCPClient_client
    if MCPClient_client is None:
        MCPClient_client = MCPClient()
    return MCPClient_client
       
