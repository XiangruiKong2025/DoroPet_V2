import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import random
from pynput import mouse
from .live2dview import Live2DCanvas
###对话
from .MainWindow import MainAppWindow,myFont
# from .Tools import WeatherDataService, Thread_WeatherData
from .WebViewTool import WebCtrlTool



class MouseListenerThread(QThread):
    mouse_moved = pyqtSignal(int, int)
    
    def run(self):
        def on_move(x, y):
            self.mouse_moved.emit(x, y)

        with mouse.Listener(on_move=on_move) as listener:
            listener.join()


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        # 显示初始化
        self.scale_factor = 1.0
        self.ai_window = MainAppWindow()
        self.globalcfg = self.ai_window.options_widget.GeneratorOptPage.cfgdata
        self.ai_window.options_widget.Live2DOptPage.signal_apply_model.connect(self.change_Model)
        self.initUI()
        self.update_size()

        # chat
        self.ai_window.global_finished_response_received.connect(self.onReceivedLLM)
        self.bottom_chat = False

        # 气泡淡出
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.hide_bubble)

        #天气淡出
        self.hefeng_timer = QTimer()
        # self.hefeng_timer.timeout.connect(self.hide_hefeng)

        # 随机行为
        self.interaction_timer = QTimer()
        self.interaction_timer.timeout.connect(self.random_behavior)
        self.AutoChange = False
        # self.OnclickAutobehavier() # 默认自动事件
        # self.jump_animation() # 立即触发一次跳

        # 循环动作
        self.circleMotion_timer = QTimer()
        self.circleMotiontime = 1200
        self.timeOn = False
        self.motionname = "默认"


        # 启动鼠标监听线程
        self.mouse_thread = MouseListenerThread()
        self.mouse_thread.mouse_moved.connect(self.update_label)
        # self.mouse_thread.start()
        
    def initUI(self):
        # 窗口设置
        self.setWindowTitle("DoroPet")
        self.setWindowIcon(QIcon("./icons/app.ico"))
        if not self.globalcfg.FrontProcess:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # 允许事件穿透
        self.move(800, 600)
        self.setMouseTracking(True)  # 监控所有鼠标移动
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        #思考气泡
        # self.thought_bubble_widget
        self.thought_bubble = QLabel()
        self.thought_bubble.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint| Qt.Tool)
        self.thought_bubble.hide()
        self.thought_bubble.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 220);
                border: 2px solid #8E8E8E;
                padding: 8px;
                color: #333;
                font-weight: bold;
                font-size: 15px;
                height: 30px
            }
        """)

        self.hefengweather = WebCtrlTool("https://map.qweather.com/index.html" ,"", -1,-1)
        # self.hefengweather.setRadius(18)
        self.hefengweather.setAcceptRequest(False)
        # self.hefengweather.setWindowFlags(Qt.WindowStaysOnTopHint| Qt.Tool)
        self.hefengweather.hide()
        self.hefengweather.setWindowTitle("和风天气")


        self.Live2DView = Live2DCanvas(True, self.globalcfg.live2dmodeldefpath)
        # print(f"self.Live2DView init:  {self.Live2DView.width()},{self.Live2DView.height()}")
        self.Live2DView.setFixedSize(450,420)
        
        layout.addWidget(self.Live2DView)
        self.original_size = self.Live2DView.frameSize()
        self.Live2DView.signal_Live2Dinited.connect(self.live2dInited)
        print(self.original_size)
        # 添加伸展项，吸收多余空间
        layout.addStretch(1) 
        
        # 初始化拖动变量
        self.dragging = False
        self.offset = QPoint()

        self.resize(int(self.original_size.width() * self.scale_factor),
                    int(self.original_size.height() * self.scale_factor))
        
        self.sendwidget = QWidget(self)
        layout.addWidget(self.sendwidget)

        sendwidget_HLayout = QHBoxLayout(self.sendwidget)
        sendwidget_HLayout.setContentsMargins(0, 0, 0, 0)
        sendwidget_HLayout.setSpacing(5)
        self.inputLineEdit = QLineEdit(self.sendwidget)
        self.sendBtn = QPushButton("发送")
        self.sendBtn.setFixedHeight(32)
        self.sendBtn.setObjectName("smallsend_button")
        sendwidget_HLayout.addWidget(self.inputLineEdit)
        sendwidget_HLayout.addWidget(self.sendBtn)

        self.inputLineEdit.setPlaceholderText("输入消息...")
        self.inputLineEdit.returnPressed.connect(self.send_message)  # 回车键绑定
        self.sendBtn.clicked.connect(self.send_message)
        self.inputLineEdit.hide()
        self.sendBtn.hide()

        # 右键菜单
        self.menu = QMenu(self)

        zoom_in_action = QAction("放大", self)
        zoom_in_action.triggered.connect(self.zoom_in)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.triggered.connect(self.zoom_out)

        zoom_def_action = QAction("默认", self)
        zoom_def_action.triggered.connect(self.zoom_def)

        show_ai = QAction("主界面", self)
        show_ai.triggered.connect(self.show_deepseek_window)

        self.show_bottom_chat = QAction("快捷聊天", self)
        self.show_bottom_chat.setCheckable(True)
        self.show_bottom_chat.triggered.connect(self.on_show_bottom_chat)


        self.change_Expression = QMenu("表情",self)
        self.action_group_Exp = QActionGroup(self)
        self.action_group_Exp.setExclusive(True)  # 设置为互斥（单选）
        
        # 连接 triggered 信号（所有 action 都连接同一个槽）
        self.action_group_Exp.triggered.connect(self.OnclickchangeExp)

        self.change_Motion = QMenu("动作",self)
        self.action_group_motion = QActionGroup(self)
        self.action_group_motion.setExclusive(True)  # 设置为互斥（单选）

        
        # 连接 triggered 信号（所有 action 都连接同一个槽）
        self.action_group_motion.triggered.connect(self.OnclickchangeMotion)

        self.Mouse_track_action = QAction("鼠标跟随", self)
        self.Mouse_track_action.triggered.connect(self.OnclickMouseTrack)
        self.Mouse_track_action.setCheckable(True)
        self.Mouse_track_action.setChecked(False)

        self.auto_change_gif = QAction("主动闲聊", self)
        self.auto_change_gif.triggered.connect(self.OnclickAutobehavier)
        self.auto_change_gif.setCheckable(True)
        self.auto_change_gif.setChecked(False)
        


        self.Tools_menu = QMenu("小工具",self)

        get_weather_action = QAction("实时天气", self)
        self.Tools_menu.addAction(get_weather_action)  # 添加到菜单或工具栏中
        get_weather_action.triggered.connect(self.get_weather)

        lianliankan_action = QAction("连连看", self)
        self.Tools_menu.addAction(lianliankan_action)  # 添加到菜单或工具栏中
        lianliankan_action.triggered.connect(self.run_external_exe)


        hide_action = QAction("隐藏到托盘", self)
        hide_action.triggered.connect(self.close)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(lambda: sys.exit())

        self.menu.addAction(show_ai)
        self.menu.addAction(self.show_bottom_chat)
        self.menu.addSeparator()

        self.menu.addAction(zoom_in_action)
        self.menu.addAction(zoom_out_action)
        self.menu.addAction(zoom_def_action)
        # self.menu.addAction(change_gif)
        self.menu.addSeparator()
        self.menu.addMenu(self.change_Expression)
        self.menu.addMenu(self.change_Motion)
        self.menu.addAction(self.auto_change_gif)
        self.menu.addAction(self.Mouse_track_action)
        self.menu.addSeparator()
        self.menu.addMenu(self.Tools_menu)
        self.menu.addSeparator()
        self.menu.addAction(hide_action)
        self.menu.addAction(exit_action)

         # 初始化系统托盘图标
        self.init_tray_icon()

    def update_label(self, x, y):
        # print(f"Mouse Position: {x}, {y}")
        if self.Mouse_track_action.isChecked():
            self.Live2DView.MouseTrack(x, y)

    def OnclickMouseTrack(self):
        if self.Mouse_track_action.isChecked():
            self.mouse_thread.start()
        else:
            self.mouse_thread.quit()

    def closeEvent(self, event):
        self.mouse_thread.quit()
        self.mouse_thread.wait()
        event.accept()

    def change_Model(self, sPath):
        self.Live2DView.LoadnewModelPath(sPath)
        self.live2dInited()

    def live2dInited(self):
        self.zoom_def()
        # 自动加载表情
        actiongs = self.action_group_Exp.actions()
        for act in actiongs:
            self.action_group_Exp.removeAction(act)
            self.change_Expression.removeAction(act)
        expressions = self.Live2DView.model.GetExpressionIds()
        for text in expressions:
            print(f"加载表情： {text}")
            action = QAction(text, self)
            action.setCheckable(True)  # 必须设置为可勾选
            action.setChecked(False)
            self.action_group_Exp.addAction(action)
            self.change_Expression.addAction(action)  # 添加到菜单或工具栏中

        actiongs = self.action_group_motion.actions()
        for act in actiongs:
            self.action_group_motion.removeAction(act)
            self.change_Motion.removeAction(act)
        motions = ["默认"]
        for text in motions:
            action = QAction(text, self)
            action.setCheckable(True)  # 必须设置为可勾选
            action.setChecked(False)
            self.action_group_motion.addAction(action)
            self.change_Motion.addAction(action)  # 添加到菜单或工具栏中

        motions = self.Live2DView.model.GetMotionGroups()
        for text in motions:
            print(f"加载动作：{text}")
            action = QAction(text, self)
            action.setCheckable(True)  # 必须设置为可勾选
            action.setChecked(False)
            self.action_group_motion.addAction(action)
            self.change_Motion.addAction(action)  # 添加到菜单或工具栏中

        self.circleMotion_timer.stop()
        self.timeOn = False
        self.motionname = "默认"
        self.Live2DView.model.Update()


    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            # self.changeGIF("./doroimg/dorodagun.gif")
            
    def mouseMoveEvent(self, event: QMouseEvent):
        # print(f"mouseMoveEvent:X:{event.globalPos()}")
        if self.dragging:
            self.move(event.globalPos() - self.offset)
            self.update_thought_bubble_position()
            self.update_hefengweather_position()

            
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            # self.changeGIF(self.curpath)

    def wheelEvent(self, event):
        # return
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()

    def zoom_in(self):
        self.scale_factor *= 1.05
        self.scale_factor = min(self.scale_factor, 3.0)
        self.update_size()

    def zoom_out(self):
        self.scale_factor *= 0.95
        self.scale_factor = max(self.scale_factor, 0.5)
        self.update_size()

    def zoom_def(self):
        print("默认大小")
        self.scale_factor = 1.0
        self.update_size()

    def update_size(self):
        new_width = int(self.original_size.width() * self.scale_factor)
        new_height = int(self.original_size.height() * self.scale_factor)
        # print(new_width, new_height,new_height+self.sendBtn.height()+2)
        self.setFixedSize(new_width, new_height+self.sendBtn.height()+2)
        if self.Live2DView.Inited:
            self.Live2DView.resizeGL(new_width, new_height)
        if not self.thought_bubble.isHidden():
            self.scale_factor
            available_width = self.width() - 20
            self.thought_bubble.setFixedWidth(available_width)
            self.thought_bubble.adjustSize()    
        self.update()    
        # self.label.setFixedSize(new_width, new_height)
        # self.label.update()  # ✅ 强制更新 QLabel  
        
            
    def contextMenuEvent(self, event):
        # 创建右键菜单
        # 在鼠标位置显示菜单
        self.menu.exec_(QCursor.pos())

        
    def OnclickchangeExp(self, action : QAction):
        if(action.text() != ""):
            self.Live2DView.model.SetExpression(action.text())


    def OnclickchangeMotion(self, action : QAction):
        if action.text() != "默认":
            if not self.timeOn:
                self.Live2DView.model.Update()
                self.Live2DView.model.StartMotion(action.text(),0,1)
                self.timeOn = True
                self.motionname = action.text()
                self.circleMotion_timer.singleShot(self.circleMotiontime,self.onfinishmotion)
            return
        else:
            self.circleMotion_timer.stop()
            self.timeOn = False
            self.motionname = "默认"
            self.Live2DView.model.Update()

    def onfinishmotion(self):
        if self.isHidden():
            # 窗口隐藏时自动恢复默认动作
            self.circleMotion_timer.stop()
            self.timeOn = False
            self.motionname = "默认"
        self.Live2DView.model.Update()
        
        if self.timeOn:
            self.Live2DView.model.StartMotion(self.motionname,0,1)
            self.circleMotion_timer.singleShot(self.circleMotiontime,self.onfinishmotion)



    def OnclickAutobehavier(self):
        self.AutoChange = not self.AutoChange
        if self.AutoChange:
            self.auto_change_gif.setChecked(True)
            self.jump_animation()  # 立即触发一次
            # self.random_thought_bubble()
            self.interaction_timer.start(30000)  # 每xx秒触发一次随机行为

            if self.bottom_chat:
                self.on_show_bottom_chat()
                self.show_bottom_chat.setChecked(False)
        else:
            self.auto_change_gif.setChecked(False)
            self.interaction_timer.stop()

    def random_behavior(self):
        behaviors = [
            lambda: self.jump_animation(),
            lambda: self.random_thought_bubble()
        ]
        weights = [1, 9]  # 权重比例
    
        selected_behavior = random.choices(behaviors, weights=weights, k=1)[0]
        selected_behavior()  # 触发行为
       

    def jump_animation(self):
        # 跳跃动画效果
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        start_rect = self.geometry()
        jump_rect = QRect(start_rect.x(), int(start_rect.y()-start_rect.height()/5), 
                         start_rect.width(), start_rect.height())
        self.animation.setKeyValueAt(0.5, jump_rect)
        self.animation.setEndValue(start_rect)
        self.animation.start()    

    def random_thought_bubble(self):
        thinktext_List = [
            "欧润吉！好多好多欧润吉！人也要一起吃！",  # 开心到飞起
            "哼！不理人了！Doro要藏起人所有的袜子！",  # 超生气
            "呜呜...人不要丢下Doro...Doro会乖乖的...",  # 害怕得发抖
            "咕噜咕噜...Doro要吃掉一头牛！还有十个欧润吉！",  # 超级饿
            "Zzz...欧润吉...Zzz...人...",  # 困成一团
            "人什么时候回来呀...Doro要拆家了！...才不是！",  # 无聊到爆炸
            "Doro今天捡了好多瓶子！人会夸Doro能干的！",  # 得意洋洋
            "呜...Doro是不是做错事了...人会不喜欢Doro吗...",  # 难过想哭
            "那个会发光的长方形是什么呀？人为什么一直看它？",  # 好奇宝宝
            "Doro要努力挣钱！给人买最大的欧润吉！",  # 决心满满
            "人...人夸Doro可爱...Doro...Doro才不是最可爱的呢！",  # 害羞脸红
            "Doro是人最棒的家人！Doro会保护人的！",  # 自豪挺胸
            "Doro只是想玩一下...不是故意弄坏的...",  # 委屈巴巴
            "Doro想到一个挣钱的好办法！...是什么来着？",  # 灵光一闪
            "人...人对Doro真好...Doro也要对人好！",  # 感动到哭
            "为什么人要上班呢？上班是什么？能吃吗？",  # 疑惑不解
            "明天一定能捡到更多的瓶子！买更多的欧润吉！",  # 充满希望
            "Doro不要收拾房间！Doro要玩！",  # 厌烦至极
            "嘿嘿嘿...人是Doro的！",  # 傻乐傻乐
            "Doro以后再也不乱翻东西了！...大概吧..."  # 下定决心
        ]
        thinktext = random.choice(thinktext_List)
        self.show_thought_bubble(thinktext)

    def show_thought_bubble(self, text, delay=5000):
        print(text)
        self.thought_bubble.setText(text)
        self.thought_bubble.setWordWrap(True)  # 启用自动换行
        available_width = self.width() - 20
        self.thought_bubble.setFixedWidth(available_width)
        self.thought_bubble.adjustSize()
        
        # self.thought_bubble.move(0, 0)
        self.update_thought_bubble_position()
        # 显示
        if self.isHidden():
            return
        self.thought_bubble.show()
        self.bubble_timer.start(delay)
    
    def hide_bubble(self):
        """隐藏气泡的动画效果"""
        self.bubble_timer.stop()
        if self.thought_bubble:
            self.thought_bubble.hide()

    def update_thought_bubble_position(self):
        if not self or not self.thought_bubble:
            return

        # 获取 DesktopPet 的位置和尺寸
        desktop_pos = self.pos()
        desktop_size = self.size()

        # 获取 thought_bubble 的推荐尺寸
        thought_size = self.thought_bubble.sizeHint()

        # 计算新位置：水平居中，位于 DesktopPet 上方
        x = desktop_pos.x() + (desktop_size.width() - thought_size.width()) // 2
        y = desktop_pos.y() - thought_size.height()

        # 移动并显示 thought_bubble
        self.thought_bubble.move(x, y)
        # self.thought_bubble.show()

    def hide_hefeng(self):
        """隐藏气泡的动画效果"""
        # self.hefeng_timer.stop()
        if self.hefengweather:
            self.hefengweather.hide()

    def update_hefengweather_position(self):
        if not self or not self.hefengweather:
            return

        # 获取 DesktopPet 的位置和尺寸
        desktop_pos = self.pos()
        desktop_size = self.size()

        # 获取 thought_bubble 的推荐尺寸
        # thought_size = self.hefengweather.sizeHint()

        # 计算新位置：水平居中，位于 DesktopPet 右方
        x = desktop_pos.x() + desktop_size.width()
        y = desktop_pos.y() 
        # 移动并显示 thought_bubble
        self.hefengweather.move(x, y)
        # self.thought_bubble.show()

    def show_deepseek_window(self):
        if not self.ai_window:
            return
        self.ai_window.show()

    def on_show_bottom_chat(self): 
        self.bottom_chat = not self.bottom_chat
        if self.bottom_chat:
            self.show_bottom_chat.setChecked(True)
            self.inputLineEdit.show()
            self.sendBtn.show()
            if self.AutoChange:
                self.auto_change_gif.setChecked(False)
                self.interaction_timer.stop()
        else:
            self.inputLineEdit.hide()
            self.show_bottom_chat.setChecked(False)
            self.sendBtn.hide()
        self.update_size()    

    def send_message(self):
        user_input = self.inputLineEdit.text().strip()
        if not user_input:
            return
        if self.AutoChange:
            self.auto_change_gif.setChecked(False)
            self.interaction_timer.stop()
        self.inputLineEdit.clear()
        self.ai_window.send_message(user_input) # 调用聊天窗口的功能，这样记录会留在聊天窗口

    def onReceivedLLM(self,content):
        self.show_thought_bubble(content)

    def get_weather(self):
        if self.hefengweather:
            self.hefengweather.refresh()
            self.hefengweather.show()
            self.update_hefengweather_position()
            # self.hefeng_timer.singleShot(5000,self.hide_hefeng)

    def on_Thread_WeatherData_received(self, weather_data):
        if not weather_data:
            QMessageBox.critical(self, "错误", "无法获取天气信息")
            return

        self.show_thought_bubble(weather_data)
    

    def run_external_exe(self):
        # 替换为你的 .exe 文件路径
        exe_path = r"DoroLianliankan.exe"
        self.process = QProcess(self)        # 启动外部程序
        self.process.start(exe_path)

        if not self.process.waitForStarted():
            print("无法启动程序，请检查路径是否正确。")
        else:
            print("程序已启动。")

    # 托盘
    def init_tray_icon(self):
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icons/app.ico"))  # 替换为你的图标路径

        # 创建右键菜单
        tray_menu = QMenu()

        show_action = QAction("显示窗口", self)
        quit_action = QAction("退出", self)

        # 添加菜单项
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        # 设置菜单
        self.tray_icon.setContextMenu(tray_menu)

        # 连接信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        show_action.triggered.connect(self.show_window)
        quit_action.triggered.connect(lambda: sys.exit())

        # 显示托盘图标
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        # 隐藏窗口而不是关闭
        self.hide()
        event.ignore()  # 阻止窗口真正关闭

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont(myFont().getFont(), 13)
    app.setFont(font)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())