from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTextBrowser, QScrollArea, QListWidget, QListWidgetItem,
    QVBoxLayout, QPushButton, QTextEdit, QLabel, QMenu, QSizePolicy, QMessageBox,
    QApplication
)
from PyQt5.QtCore import QTimer, Qt, QDateTime, QThread, pyqtSignal

from sys import exit, argv
import sqlite3
from json import dumps, load, dumps as json_dumps
from configparser import ConfigParser

from .loading import LoadingWidget
from .LLMprovider import ChatThread_DefOpenAI
from .option import get_OptionWidget
from .VoskRecognition import VoskRecognitionThread
from .MCPclent import get_MCPClient

# 自定义线程类，用于异步初始化
# class InitThread(QThread):
#     initialized = pyqtSignal(object)  # 初始化完成后发送实例

#     def run(self):
#         vosk_thread = VoskRecognitionThread()
#         self.initialized.emit(vosk_thread)

class ChatMessage(QWidget):
    def __init__(self, content, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setProperty("isUser", self.is_user)  # 用于QSS样式选择
        # self.font_family = myFont().getFont()
        self.init_ui(content)


    def init_ui(self, content):
        # 设置尺寸策略为Preferred以获得更好的布局适应性
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # 主布局：水平布局，用于消息对齐
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 4)  # 添加上下边距
        main_layout.setSpacing(0)

        # 创建气泡容器
        self.bubble = QWidget()
        self.bubble.setObjectName("bubble")  # 用于QSS选择器
        
        # 创建内容显示组件
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)

        self.content_browser.setReadOnly(True)
        self.content_browser.setObjectName("content_label")
        # self.content_browser.anchorClicked.connect(self.handle_anchor_clicked)

        # self.content_label.setFont(QFont(self.font_family, 12))
        # 禁用滚动条，通过动态调整高度实现自适应
        self.content_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 气泡内部布局
        bubble_layout = QHBoxLayout(self.bubble)
        bubble_layout.addWidget(self.content_browser)
        bubble_layout.setContentsMargins(12, 6, 12, 6) 

        # 用户消息右对齐
        if self.is_user:
            main_layout.addStretch()
        
        main_layout.addWidget(self.bubble)
        if not self.is_user:
            main_layout.addStretch()
        self.set_content(content)

    # def handle_anchor_clicked(self, url):
    #         QDesktopServices.openUrl(url)

    def set_content(self, content):
        """设置初始内容"""
        self.full_content = content
        if self.is_user:
            self.content_browser.setPlainText(content)
        else:
            # final_html = render_markdown(content)
            # self.content_label.setHtml(final_html)
            self.content_browser.setMarkdown(content)
        self.adjust_size()

    def append_content(self, content):
        """流式追加内容（用于生成式回复）"""
        self.full_content += content
        # final_html = render_markdown(self.full_content)
        # self.content_label.setHtml(final_html)
        self.content_browser.setMarkdown(self.full_content)
        self.adjust_size()

    def adjust_size(self):
        """动态调整消息气泡尺寸"""
        doc = self.content_browser.document()
        
        # 计算内边距（从布局获取或硬编码）
        padding = 24   # 左右内边距（12*2）
        v_padding = 12 # 垂直内边距（6*2）
        
        # 获取父容器宽度（考虑父级不存在时的默认值）
        parent_width = self.parent().width() if self.parent() else 400

        # 根据消息类型确定最大宽度约束
        if self.is_user:
            max_bubble_width = int(parent_width * 0.7)  # 用户消息最大70%
        else:
            max_bubble_width = int(parent_width * 0.9)  # AI消息最大88%

        # 计算文本可用宽度并设置到文档
        available_text_width = max(max_bubble_width - padding, 1)
        doc.setTextWidth(available_text_width)

        # 计算实际所需宽度
        text_width = doc.idealWidth()
        bubble_width = text_width + padding
        bubble_width = min(bubble_width, max_bubble_width)
        bubble_width = max(bubble_width, 60 if self.is_user else 100)  # 最小宽度限制

        # 设置气泡宽度
        self.bubble.setFixedWidth(int(bubble_width))

        # 计算高度（包含文档边距）
        ideal_height = doc.size().height() + v_padding * 2
        self.setFixedHeight(int(ideal_height))
        self.updateGeometry()

    def resizeEvent(self, event):
        """父窗口尺寸变化时重新调整"""
        super().resizeEvent(event)
        self.adjust_size()

class ChatWidget(QWidget):
    global_finished_response_received = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.messages = []
        self.curname = ""
        self.system_message = ""
        self.current_session_id = None
        self.initUI()
        self.setAcceptDrops(True)
        # self.initVosk()
        get_OptionWidget().GeneratorOptPage.VoskSettingpage.voskEnChanged.connect(self.initVosk)
        get_MCPClient()   #初始化

    def reset_messages(self):
        """重置对话历史"""
        self.messages = [{"role": "system", "content": self.system_message}]
        # 清空聊天界面
        for i in reversed(range(self.chat_layout.count())): 
            self.chat_layout.itemAt(i).widget().setParent(None)

    def set_system_message(self, system_message):
        self.system_message = system_message

    def initUI(self):
        # 主窗口布局：水平布局
        # 主窗口布局改为水平分割
        main_layout = QHBoxLayout(self)
        # 左侧会话列表
        self.session_list = QListWidget()
        self.session_list.setFixedWidth(200)
        self.session_list.itemClicked.connect(self.load_session)
        self.session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self.show_context_menu)
    
        # 添加"新建对话"按钮
        new_conv_btn = QPushButton("➕ 新建对话")
        new_conv_btn.clicked.connect(self.create_new_session)
    
        session_layout = QVBoxLayout()
        session_layout.addWidget(new_conv_btn)
        session_layout.addWidget(self.session_list)

        # chatlayout = QVBoxLayout(self)
        chat_container = QWidget()
        chatlayout = QVBoxLayout(chat_container)
         # 聊天区域
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setObjectName("chat_scroll")
        
        self.chat_container = QWidget()
        self.chat_container.setObjectName("chat_scroll")

        
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(40, 20, 20, 20)
        self.chat_layout.setSpacing(0)
        
        self.chat_scroll.setWidget(self.chat_container)
        chatlayout.addWidget(self.chat_scroll, 1)

        # 输入区域
        input_widget = QWidget(self)
        # input_widget.setStyleSheet("background-color: #FFFFFF; border-top: 1px solid #E5E5E5;")
        input_widget.setFixedHeight(210)
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入消息...")
        self.input_box.setObjectName("inputbox")
        self.input_box.setAcceptRichText(False)
        self.input_box.setFixedHeight(210)
        # self.input_box.setFont(QFont(myFont().getFont(), 12))

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.voskbtn = QPushButton()
        self.voskbtn.setFixedSize(32, 32)
        self.voskbtn.setObjectName("vosk_button")
        self.voskbtn.setCheckable(True)
        button_layout.addWidget(self.voskbtn)
        self.voskbtn.clicked.connect(self.toggle_recording)
        self.voskbtn.hide()

        self.partial_label = QLabel("")
        button_layout.addWidget(self.partial_label)
        # button_layout.addStretch()
        
        self.send_button = QPushButton("发送")
        self.send_button.setFixedSize(80, 32)
        self.send_button.setObjectName("SendBtn")

        self.send_button.clicked.connect(self.on_clicked_send_message)
        
        button_layout.addWidget(self.send_button)
        input_layout.addWidget(self.input_box)
        input_layout.addLayout(button_layout)
        chatlayout.addWidget(input_widget)

        # self.chat_scroll.verticalScrollBar().setObjectName("verticalScrollBar")

        # 组合整体布局
        main_layout.addLayout(session_layout)
        main_layout.addWidget(chat_container, 1)
        self.setLayout(main_layout)
        
        # 初始化数据库连接
        self.init_db()
        self.load_sessions_from_db()

    def initVosk(self, voskEn):
        if voskEn:
            # 初始化语音识别线程
            voskpath = get_OptionWidget().GeneratorOptPage.cfgdata.voskpath
            if voskpath:
                self.recognition_thread = VoskRecognitionThread(voskpath)
                
                self.voskbtn.show()
                # 连接信号与槽
                self.recognition_thread.partial_result.connect(self.update_partial)
                self.recognition_thread.final_result.connect(self.update_final)
                self.recognition_thread.error_init.connect(self.vosk_error_init)

                self.is_recording = False

                self.recognition_thread.initmodel()
        else:
            self.voskbtn.hide()


    def vosk_error_init(self, error):
        self.voskbtn.setEnabled(False)
        self.partial_label.setText(f"{error}")
        self.is_recording = False

    def toggle_recording(self):
        """切换录音状态"""
        if not self.is_recording:
            # 开始录音
            self.recognition_thread.start()
            self.voskbtn.setChecked(True)
            self.is_recording = True
            # self.result_text.clear()
            self.partial_label.setText("我在听...")
        else:
            # 停止录音
            self.recognition_thread.stop()
            self.voskbtn.setChecked(False)
            self.is_recording = False
            self.partial_label.clear()

    def update_partial(self, text):
        """更新实时识别结果"""
        # self.input_box.setText(text)
        partial = text.strip()
        if not partial:
            return
        self.partial_label.setText(partial)

    def update_final(self, text):
        """更新完整识别结果"""
        user_input = self.input_box.toPlainText().strip()
        self.input_box.setText(f"{user_input}{text}")
        self.partial_label.clear()

    def on_clicked_send_message(self):
        user_input = self.input_box.toPlainText().strip()
        if not user_input:
            return
        self.input_box.clear()
        self.send_message(user_input)

    def keyPressEvent(self, event):
        # 检查是否按下了 Ctrl + Enter
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            if event.modifiers() == Qt.ControlModifier:
                print("你按下了 Ctrl + Enter")
                self.on_clicked_send_message()
                return  # 阻止其他处理

        # 其他按键可以继续处理
        super().keyPressEvent(event)

    def send_message(self, content):
        # 添加用户消息
        user_message = ChatMessage(content, is_user=True, parent=self.chat_container)
        self.chat_layout.addWidget(user_message)
        self.messages.append({"role": "user", "content": content})

        # 添加加载状态
        self.loading_widget = LoadingWidget()
        self.chat_layout.addWidget(self.loading_widget, 0, Qt.AlignLeft)
        self.scroll_to_bottom()


        # 创建AI消息占位符
        self.current_ai_message = ChatMessage("", is_user=False,parent=self.chat_container)
        self.chat_layout.addWidget(self.current_ai_message)

        # 启动线程
        provider = get_OptionWidget().getProvider()
        if provider.get("baseurl") == '':
            self.update_chat_display_stream(f"模型：{provider.get('provider')}，baseurl未配置")
            return
        if provider.get("apikey") == '':
            self.update_chat_display_stream(f"模型：{provider.get('provider')}，apikey未配置")
            return
        if provider.get("model") == '':
            self.update_chat_display_stream(f"模型：{provider.get('provider')}，model未配置")
            return


        params = provider.get("params")
        self.chat_thread = QThread()
        
        # if(provider.get("provider") == "maas"):
        #     self.chat_thread = ChatThread_maas(self.messages, 
        #                                     stream= True, 
        #                                     base_url= params.get("baseurl"),
        #                                     api_key= params.get("apikey"), 
        #                                     model= params.get("model")) 
        # if(provider.get("provider") == "qwen"):
        #     self.chat_thread = ChatThread_Qwen(self.messages, 
        #                                     stream= True, 
        #                                     base_url= params.get("baseurl"),
        #                                     api_key= params.get("apikey"), 
        #                                     model= params.get("model")) 
        # if(provider.get("provider") == "deepseek" or provider.get("provider") == "openai"):
        #     self.chat_thread = ChatThread_DefOpenAI(self.messages, 
        #                                     stream= True, 
        #                                     base_url= params.get("baseurl"),
        #                                     api_key= params.get("apikey"), 
        #                                     model= params.get("model"))     
        # if(provider.get("provider") == "gemini"):
        #     self.chat_thread = ChatThread_gemini(self.messages, 
        #                                     stream= True, 
        #                                     base_url= params.get("baseurl"),
        #                                     api_key= params.get("apikey"), 
        #                                     model= params.get("model"))  
            

        self.chat_thread = ChatThread_DefOpenAI(self.messages, 
                                        stream= True, 
                                        base_url= params.get("baseurl"),
                                        api_key= params.get("apikey"), 
                                        model= params.get("model"))     
        
        self.chat_thread.stream_response_received.connect(self.update_chat_display_stream)
        self.chat_thread.finished.connect(self.on_chat_thread_finished)
        self.chat_thread.start()

    # 流式输出
    def update_chat_display_stream(self, content):
        if self.loading_widget:
            self.chat_layout.removeWidget(self.loading_widget)
            self.loading_widget.deleteLater()
            self.loading_widget = None
        
        if self.current_ai_message:
            self.current_ai_message.append_content(content)
            self.scroll_to_bottom()
            # print(content)

    # 返回结果
    def on_chat_thread_finished(self):
        if self.loading_widget:
            self.chat_layout.removeWidget(self.loading_widget)
            self.loading_widget.deleteLater()
            self.loading_widget = None
        
        ai_content = self.current_ai_message.full_content
        self.messages.append({"role": "assistant", "content": ai_content})
        self.global_finished_response_received.emit(ai_content)
        self.save_session_to_db()
        print(f"api调用结束：{ai_content}")

    def scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def init_db(self):
        self.conn = sqlite3.connect("data/chat_sessions.db")
        cursor = self.conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS sessions (
                        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        system_name TEXT,
                        system_prompt TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
                        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        role TEXT,
                        content TEXT,
                        FOREIGN KEY(session_id) REFERENCES sessions(session_id))""")
        self.conn.commit()


    def save_session_to_db(self):
        cursor = self.conn.cursor()
        if self.current_session_id is None:
            # 新建会话
            timestamp = QDateTime.currentDateTime().toString(Qt.ISODate)
            cursor.execute("INSERT INTO sessions (timestamp, system_prompt, system_name) VALUES (?, ?, ?)",
                        (timestamp, self.system_message,self.curname))
            session_id = cursor.lastrowid
            self.current_session_id = session_id
            item = QListWidgetItem(f"{self.curname}-{timestamp}")
            item.setData(Qt.UserRole, session_id)
            self.session_list.insertItem(0, item)
            self.session_list.setCurrentItem(item)
        else:
            # 更新已有会话
            timestamp = QDateTime.currentDateTime().toString(Qt.ISODate)
            cursor.execute("UPDATE sessions SET system_prompt=?, timestamp=? WHERE session_id=?",
                        (self.system_message, timestamp, self.current_session_id))
            # 删除旧消息
            cursor.execute("DELETE FROM messages WHERE session_id=?", (self.current_session_id,))

        # 插入当前对话消息
        for msg in self.messages:
            if msg["role"] != "system" and msg["role"] != "tool" and msg["content"] != '':
                cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                            (self.current_session_id, msg["role"], msg["content"]))
        self.conn.commit()


    def load_sessions_from_db(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT session_id, timestamp, system_prompt, system_name FROM sessions ORDER BY timestamp DESC")
        
        for row in cursor.fetchall():
            session_id, timestamp, system_prompt, self.curname = row
            item = QListWidgetItem(f"{self.curname}-{timestamp}")
            item.setData(Qt.UserRole, session_id)  # 存储 session_id 用于后续查询
            self.session_list.addItem(item)
        if self.session_list.count() < 1:
            self.create_new_session_("Doro")

    def create_new_session(self):
        self.create_new_session_("Doro")


    def create_new_session_(self, strname="Doro"):
        print(f"创建新对话{strname}")
        self.curname = strname
        
        preset_options = get_OptionWidget().getpreset()
        self.set_system_message(preset_options[strname])

        self.reset_messages()  # 先设ystem_message,再调用

        cursor = self.conn.cursor()
        timestamp = QDateTime.currentDateTime().toString(Qt.ISODate)
        cursor.execute("INSERT INTO sessions (timestamp, system_prompt, system_name) VALUES (?, ?, ?)",
                    (timestamp, self.system_message, self.curname))
        self.conn.commit()
        session_id = cursor.lastrowid

        item = QListWidgetItem(f"{strname}-{timestamp}")
        item.setData(Qt.UserRole, session_id)
        self.session_list.insertItem(0, item)
        self.session_list.setCurrentItem(item)

        self.current_session_id = session_id  # 设置当前会话ID



    def load_session(self, item):
        session_id = item.data(Qt.UserRole)
        cursor = self.conn.cursor()

        cursor.execute("SELECT system_prompt FROM sessions WHERE session_id=?", (session_id,))
        result = cursor.fetchone()
        if result is None:
            # 会话不存在，可能是未保存或已删除
            QMessageBox.warning(self, "错误", "会话不存在或已被删除。")
            return

        system_prompt = result[0]
        self.set_system_message(system_prompt)

        cursor.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY message_id", (session_id,))
        self.reset_messages()
        for role, content in cursor.fetchall():
            if(role == "tool"):
                continue
            msg = ChatMessage(content, is_user=(role == "user"), parent=self.chat_container)
            self.chat_layout.addWidget(msg)
            self.messages.append({"role": role, "content": content})
        self.scroll_to_bottom()
        self.current_session_id = session_id  # 设置当前会话ID


    def show_context_menu(self, pos):
        menu = QMenu()
        delete_action = menu.addAction("🗑 删除会话")
        action = menu.exec_(self.session_list.mapToGlobal(pos))

        if action == delete_action:
            current_item = self.session_list.currentItem()
            if current_item:
                session_id = current_item.data(Qt.UserRole)
                cursor = self.conn.cursor()

                try:
                    # 先删除 messages 表中对应的消息记录
                    cursor.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
                    # 再删除 sessions 表中的会话记录
                    cursor.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
                    self.conn.commit()

                    # 从会话列表中移除该项
                    self.session_list.takeItem(self.session_list.row(current_item))
                    self.current_session_id = None
                    if self.session_list.count() < 1:
                        self.create_new_session_()

                except sqlite3.Error as e:
                    QMessageBox.critical(self, "数据库错误", f"删除会话时发生错误：{str(e)}")

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


    def dragEnterEvent(self, event):
        # 当拖动进入窗口时触发
        if event.mimeData().hasUrls():
            event.acceptProposedAction()  # 接受拖放
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        # 支持的文本/配置文件后缀
        TEXT_EXTENSIONS = {'.txt', '.log'}
        CONFIG_EXTENSIONS = {'.json', '.ini', '.cfg'}

        results = []
        for url in urls:
            file_path = url.toLocalFile()
            if not file_path:
                continue

            # 获取文件后缀名
            ext = file_path[file_path.rfind('.'):].lower()

            if ext in TEXT_EXTENSIONS:
                content = self.read_text_file(file_path)
                results.append(f"📄 {file_path}\n{content}")
            elif ext in CONFIG_EXTENSIONS:
                content = self.read_config_file(file_path, ext)
                results.append(f"⚙️ {file_path}\n{content}")
            else:
                results.append(f"📎 文件（不读取内容）：{file_path}")

        self.input_box.setText("\n\n".join(results))

    def read_text_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return content if content else "(文件为空)"
        except Exception as e:
            return f"❌ 读取失败: {str(e)}"

    def read_config_file(self, file_path, ext):
        try:
            if ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = load(f)
                return dumps(data, indent=2, ensure_ascii=False)

            elif ext == '.ini' or ext == '.cfg':
                config = ConfigParser()
                config.read(file_path, encoding='utf-8')
                lines = []
                for section in config.sections():
                    lines.append(f"[{section}]")
                    for key, value in config[section].items():
                        lines.append(f"  {key} = {value}")
                return "\n".join(lines) if lines else "(无配置项)"

            # elif ext in {'.yaml', '.yml'}:
            #     # 注意：需要安装 PyYAML: pip install pyyaml
            #     import yaml
            #     with open(file_path, 'r', encoding='utf-8') as f:
            #         data = yaml.safe_load(f)
            #     return yaml.dump(data, default_flow_style=False, allow_unicode=True, indent=2)

        except Exception as e:
            return f"❌ 解析失败: {str(e)}"

        return "❌ 不支持的配置格式"

if __name__ == '__main__':
    app = QApplication(argv)
    window = ChatWidget()
    window.show()
    exit(app.exec_())

