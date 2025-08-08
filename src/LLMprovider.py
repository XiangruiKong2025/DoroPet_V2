from PyQt5.QtCore import *
from openai import OpenAI
from .MCPclent import get_MCPClient
import json

# OpenAI接口实现
class ChatThread_DefOpenAI(QThread):
    response_received = pyqtSignal(str)
    stream_response_received = pyqtSignal(str)
    def __init__(self, messages, stream=False, base_url="", api_key="", model = ""):
        super().__init__()
        self.messages = messages
        self.stream = stream
        self.baseurl = base_url
        self.apikey = api_key
        self.dmodel = model
        self.client = OpenAI(api_key=self.apikey, base_url=self.baseurl)
        # self.client = OpenAI(api_key=self.apikey, base_url=self.baseurl, http_client=httpx.Client(proxy="http://127.0.0.1:7890"))
    
    def run(self):
        try:
            self.MCPclient = get_MCPClient()
            available_tools = self.MCPclient.getAvailable_tools()

            print(f"available_tools : {available_tools}")
            if available_tools:
                # 创建 OpenAI 客户端实例
                print([self.messages[-1]])
                try:
                    response = self.client.chat.completions.create(
                        model=self.dmodel,
                        messages=[self.messages[-1]],
                        stream=False,
                        tools=available_tools
                    )
                    # 处理返回的内容
                    content = response.choices[0]
                    if content.finish_reason == "tool_calls":
                        # 如何是需要使用工具，就解析工具
                        tool_call = content.message.tool_calls[0]
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        # 执行工具
                        print(f"\n[Calling tool {tool_name} with args {tool_args}]\n")
                        result = self.MCPclient.getToolCall(tool_name, tool_args)
    
                        print(f"res:{result}")
                        # print(self.messages)
                        # 将模型返回的调用哪个工具数据和工具执行完成后的数据都存入messages中
                        self.messages.append(content.message.model_dump())
                        self.messages.append({
                            "role": "tool",
                            "content": result.content[0].text,
                            "tool_call_id": tool_call.id,
                        })
                except Exception as e:
                    # 处理异常情况
                    error_msg = f"API Error: {str(e)}"
                    self.response_received.emit(error_msg)
            print(self.messages)
            response = self.client.chat.completions.create(
                model=self.dmodel,
                messages=self.messages,
                stream=self.stream,
            )
            
            if self.stream:
                full_content = ""
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_content += content
                            self.stream_response_received.emit(content)
                self.response_received.emit(full_content)
            else:
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.response_received.emit(content)

        except Exception as e:
            # 处理异常情况
            error_msg = f"API Error: {str(e)}"
            self.response_received.emit(error_msg)


# qwen3
class ChatThread_Qwen(QThread):
    # 定义两个信号：完整响应和流式响应
    response_received = pyqtSignal(str)       # 非流式或流式结束后发送完整内容
    stream_response_received = pyqtSignal(str) # 流式响应时逐步发送

    def __init__(self, messages, stream=False, base_url=None, api_key=None, model="qwen-plus"):
        super().__init__()
        self.messages = messages
        self.stream = stream
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.api_key = api_key
        self.model = model
        self.enable_search = True
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def run(self):
        try:
            # 创建 OpenAI 客户端并发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                extra_body={
                    "enable_search": self.enable_search
                },
                stream=self.stream
            )

            if self.stream:
                full_content = ""
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_content += content
                            self.stream_response_received.emit(content)
                # 发送完整响应
                self.response_received.emit(full_content)
            else:
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.response_received.emit(content)

        except Exception as e:
            # 发生异常时发送错误信息
            error_msg = f"API Error: {str(e)}"
            self.response_received.emit(error_msg)


#maas
class ChatThread_maas(QThread):
     # 定义两个信号：完整响应和流式响应
    response_received = pyqtSignal(str)       # 非流式或流式结束后发送完整内容
    stream_response_received = pyqtSignal(str) # 流式响应时逐步发送

    def __init__(self, messages, stream=False, base_url= "http://maas-api.cn-huabei-1.xf-yun.com/v1", api_key=None, model="xdeepseekv32"):
        super().__init__()
        self.messages = messages
        self.stream = stream
        self.baseurl = base_url
        self.apikey = api_key
        self.model = model
        self.enable_search = True
        self.client = OpenAI(api_key=self.apikey, base_url=self.baseurl)

    def run(self):
        try:
            # 创建 OpenAI 客户端并发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=self.stream,
                temperature=0.7,
                max_tokens=4096,
                extra_headers={"lora_id": "0"},  # 调用微调大模型时,对应替换为模型服务卡片上的resourceId
                stream_options={"include_usage": True},
                extra_body={"search_disable": False, "show_ref_label": False} 
            )

            if self.stream:
                full_content = ""
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        self.stream_response_received.emit(content)
                        full_content += content
                # 发送完整响应
                self.response_received.emit(full_content)
            else:
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.response_received.emit(content)

        except Exception as e:
            # 发生异常时发送错误信息
            error_msg = f"API Error: {str(e)}"
            self.response_received.emit(error_msg)


#哈基米Gemini
class ChatThread_gemini(QThread):
     # 定义两个信号：完整响应和流式响应
    response_received = pyqtSignal(str)       # 非流式或流式结束后发送完整内容
    stream_response_received = pyqtSignal(str) # 流式响应时逐步发送

    def __init__(self, messages, stream=False, base_url= "https://generativelanguage.googleapis.com/v1beta/openai/", api_key=None, model="gemini-2.0-flash"):
        super().__init__()
        self.messages = messages
        self.stream = stream
        self.baseurl = base_url
        self.apikey = api_key
        self.model = model
        self.enable_search = True
        self.client = OpenAI(api_key=self.apikey, base_url=self.baseurl)

    def run(self):
        try:


            self.MCPclient = get_MCPClient()
            available_tools = self.MCPclient.getAvailable_tools()

            print(f"available_tools : {available_tools}")
            if available_tools:
                # 创建 OpenAI 客户端实例
                print([self.messages[-1]])
                response = self.client.chat.completions.create(
                    model=self.dmodel,
                    messages=[self.messages[-1]],
                    stream=False,
                    tools=available_tools
                )
                # 处理返回的内容
                content = response.choices[0]
                if content.finish_reason == "tool_calls":
                    # 如何是需要使用工具，就解析工具
                    tool_call = content.message.tool_calls[0]
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # 执行工具
                    print(f"\n[Calling tool {tool_name} with args {tool_args}]\n")
                    result = self.MCPclient.getToolCall(tool_name, tool_args)
   
                    print(f"res:{result}")
                    # print(self.messages)
                    # 将模型返回的调用哪个工具数据和工具执行完成后的数据都存入messages中
                    self.messages.append(content.message.model_dump())
                    self.messages.append({
                        "role": "tool",
                        "content": result.content[0].text,
                        "tool_call_id": tool_call.id,
                    })

            # 创建 OpenAI 客户端并发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=self.stream,
                stream_options={"include_usage": True},
                reasoning_effort="low",
            )

            if self.stream:
                full_content = ""
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        self.stream_response_received.emit(content)
                        full_content += content
                # 发送完整响应
                self.response_received.emit(full_content)
            else:
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.response_received.emit(content)

        except Exception as e:
            # 发生异常时发送错误信息
            error_msg = f"API Error: {str(e)}"
            self.response_received.emit(error_msg)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 