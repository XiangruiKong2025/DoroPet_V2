"""
DoroPet - 桌面宠物应用

这是一个基于PyQt5的桌面宠物应用程序，主要功能包括：
- 显示Live2D模型作为桌面宠物
- 支持鼠标交互、表情切换和动作播放
- 提供气泡对话、天气查询等附加功能
- 可配置的自动行为和闲逛模式
"""

from sys import argv, exit
from random import choices, choice, uniform
from math import pi, cos, sin
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QAction, QActionGroup,
    QMenu, QSystemTrayIcon, QMessageBox, QApplication, QLabel
)
from PyQt5.QtGui import QIcon, QFont, QCursor, QMouseEvent, QEnterEvent
from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPoint, QRect, QPropertyAnimation, QEasingCurve, QProcess, QEvent
)
from pynput.mouse import Listener
from send2trash import send2trash
import time

# ======================
# 模块导入与依赖声明
# ======================

### 对话与界面组件
from .MainWindow import MainAppWindow, myFont
from .WebViewTool import WebCtrlTool
from .wallpaperassist import get_WallpaperWindow
from .createOrange import createOrange
from .live2dview import Live2DCanvas
from .socketthread import send_to_port, TcpListenThread
from .tts import TTSPlayer
from .SysMonitor import WindowsSystemMonitor
# ======================
# 辅助类定义
# ======================

class MouseListenerThread(QThread):
    """鼠标移动监听线程，用于实现鼠标跟随功能"""
    mouse_moved = pyqtSignal(int, int)
    
    def run(self):
        """启动鼠标监听器"""
        def on_move(x, y):
            self.mouse_moved.emit(x, y)
        
        with Listener(on_move=on_move) as listener:
            listener.join()


class SystemMonitorThread(QThread):
    """鼠标移动监听线程，用于实现鼠标跟随功能"""
    sys_state_changed = pyqtSignal(str)
    def __init__(self):
        """初始化桌面宠物窗口"""
        super().__init__()
        self.monitor = WindowsSystemMonitor()

    def run(self):
        """启动鼠标监听器"""
        while 1:
            snap = self.monitor.get_snapshot()
            # print(f"CPU: {snap['cpu_percent']:5.1f}% | Memory: {snap['memory_percent']:5.1f}%")
            self.sys_state_changed.emit(f"CPU: {snap['cpu_percent']:5.1f}%  MEM: {snap['memory_percent']:5.1f}%")
            time.sleep(1)

# ======================
# 主应用程序类
# ======================

class DesktopPet(QWidget):
    """
    桌面宠物主窗口类
    
    主要功能：
    - 显示Live2D模型作为桌面宠物
    - 处理用户交互（鼠标、键盘、右键菜单）
    - 管理自动行为和动画
    - 提供附加功能（天气、快捷聊天等）
    """
    
    def __init__(self):
        """初始化桌面宠物窗口"""
        super().__init__()
        
        # =====================
        # 状态与配置初始化
        # =====================
        
        # 显示相关状态
        self.Lock = False   # 窗口锁定状态
        self.scale_factor = 1.0  # 缩放比例
        self.original_size = None  # 原始尺寸
        
        # 主应用程序窗口
        self.ai_window = MainAppWindow()
        self.globalcfg = self.ai_window.options_widget.GeneratorOptPage.cfgdata
        
        # Live2D模型状态
        self.IsWalking = False     # 是否在闲逛
        self.Live2DView = None     # Live2D视图组件
        self.motionname = "默认"    # 当前动作名称
        self.expname = "默认"       # 当前表情名称
        self.timeOn = False         # 动作是否在循环中
        self.circleMotiontime = 20  # 动作循环是否完成的查询间隔时间(毫秒)
        
        # 气泡与聊天状态
        self.thought_bubble = None  # 思考气泡
        self.hefengweather = None   # 天气窗口
        self.bottom_chat = False    # 是否显示底部聊天
        
        # 自动行为状态
        self.AutoChange = False     # 是否启用自动行为
        
        # =====================
        # 初始化与设置
        # =====================
        
        # 初始化UI
        self.initUI()
        self.update_size()
        
        # 设置拖放支持
        self.setAcceptDrops(True)
        
        # =====================
        # 信号连接
        # =====================
        
        # Live2D模型配置更新
        self.ai_window.options_widget.Live2DOptPage.signal_apply_model.connect(self.change_Model)
        self.ai_window.options_widget.GeneratorOptPage.alphaChanged.connect(self.on_alpha_changed)
        
        # 聊天功能连接
        self.ai_window.chat_widget.global_finished_response_received.connect(self.onReceivedLLM)
        
        # =====================
        # 定时器初始化
        # =====================
        
        # 气泡淡出定时器
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.hide_bubble)
        
        # 随机行为定时器
        self.interaction_timer = QTimer()
        self.interaction_timer.timeout.connect(self.random_behavior)
        
        # 循环动作定时器
        self.circleMotion_timer = QTimer()
        
        # 闲逛移动定时器
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.start_new_movement)
        
        # =====================
        # 线程与动画初始化
        # =====================
        
         # 启动后台线程
        if self.globalcfg.TCP_listenport > 0:
            self.tcpthread = TcpListenThread(port=self.globalcfg.TCP_listenport)
            self.tcpthread.text_received.connect(self.on_TCPreceived_text)
            self.tcpthread.start()

        # 鼠标监听线程
        self.mouse_thread = MouseListenerThread()
        self.mouse_thread.mouse_moved.connect(self.update_label)
        self.mouse_thread.start()

        # SystemMonitorThread
        self.monitor_thread = SystemMonitorThread()
        self.monitor_thread.sys_state_changed.connect(self.update_sysstate)
        self.monitor_thread.start()
        
        # 移动动画
        self.move_animation = QPropertyAnimation(self, b"pos")
        self.move_animation.setDuration(900)  # 移动持续900毫秒
        self.move_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.move_animation.stateChanged.connect(self.on_animation_state_changed)
    
    # =====================
    # UI设置相关方法
    # =====================
    
    def initUI(self):
        """初始化用户界面"""
        # 窗口基本设置
        self.setWindowTitle("DoroPet")
        self.setWindowIcon(QIcon("data/icons/app.ico"))
        if not self.globalcfg.FrontProcess:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # 事件穿透
        self.move(800, 600)
        self.setMouseTracking(True)  # 监控所有鼠标移动
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 初始化思考气泡
        self.thought_bubble = QLabel()
        self.thought_bubble.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.thought_bubble.hide()
        self.thought_bubble.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 220);
                border: 2px solid #8E8E8E;
                padding: 8px;
                color: #333;
                height: 30px
            }
        """)
        
        # 初始化天气组件
        self.hefengweather = WebCtrlTool("https://map.qweather.com/index.html", "", -1, -1)
        self.hefengweather.setAcceptRequest(False)
        self.hefengweather.hide()
        self.hefengweather.setWindowTitle("和风天气")
        
        # 初始化Live2D视图
        self.Live2DView = Live2DCanvas(True, self.globalcfg.live2dmodeldefpath)
        screen = QApplication.primaryScreen()
        defwidth = int(screen.availableSize().width() / 10)
        self.Live2DView.setFixedSize(defwidth, int(self.globalcfg.live2dLWa * defwidth))
        self.ai_window.options_widget.GeneratorOptPage.live2dLWaChanged.connect(self.update_size)
        self.Live2DView.signal_Live2Dinited.connect(self.live2dInited)
        layout.addWidget(self.Live2DView)
        self.original_size = self.Live2DView.frameSize()
        
        # 添加伸展项，吸收多余空间
        layout.addStretch(1) 
        
        # 初始化拖动变量
        self.dragging = False
        self.offset = QPoint()
        
        # 调整窗口尺寸
        self.resize(int(self.original_size.width() * self.scale_factor),
                    int(self.original_size.height() * self.scale_factor))
        
        # 初始化底部聊天组件
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
        self.inputLineEdit.returnPressed.connect(self.send_message)
        self.sendBtn.clicked.connect(self.send_message)
        self.inputLineEdit.hide()
        self.sendBtn.hide()
        
        # 初始化右键菜单
        self.init_context_menu()
        
        # 初始化系统托盘图标
        self.init_tray_icon()
    
    def init_context_menu(self):
        """初始化右键菜单"""
        self.menu = QMenu(self)
        
        # 基本操作菜单项
        show_ai = QAction("主界面", self)
        show_ai.triggered.connect(self.show_deepseek_window)
        
        self.show_bottom_chat = QAction("快捷聊天", self)
        self.show_bottom_chat.setCheckable(True)
        self.show_bottom_chat.triggered.connect(self.on_show_bottom_chat)
        
        self.lock_action = QAction("锁定窗口", self)
        self.lock_action.triggered.connect(self.lock_window)
        self.lock_action.setCheckable(True)
        self.lock_action.setChecked(False)
        
        # 缩放菜单
        self.memu_zoom = QMenu("缩放", self)
        zoom_in_action = QAction("放大", self)
        self.memu_zoom.addAction(zoom_in_action)
        zoom_in_action.triggered.connect(self.zoom_in)
        
        zoom_out_action = QAction("缩小", self)
        self.memu_zoom.addAction(zoom_out_action)
        zoom_out_action.triggered.connect(self.zoom_out)
        
        zoom_def_action = QAction("默认", self)
        self.memu_zoom.addAction(zoom_def_action)
        zoom_def_action.triggered.connect(self.zoom_def)
        
        # 表情菜单
        self.change_Expression = QMenu("表情", self)
        self.action_group_Exp = QActionGroup(self)
        self.action_group_Exp.setExclusive(True)
        self.action_group_Exp.triggered.connect(self.OnclickchangeExp)
        
        # 动作菜单
        self.change_Motion = QMenu("动作", self)
        self.action_group_motion = QActionGroup(self)
        self.action_group_motion.setExclusive(True)
        self.action_group_motion.triggered.connect(self.OnclickchangeMotion)
        
        # 自动行为菜单项
        self.auto_talk = QAction("主动闲聊", self)
        self.auto_talk.triggered.connect(self.OnclickAutobehavier)
        self.auto_talk.setCheckable(True)
        self.auto_talk.setChecked(False)
        
        self.auto_walk = QAction("溜达", self)
        self.auto_walk.triggered.connect(self.OnclickAutowalk)
        self.auto_walk.setCheckable(True)
        self.auto_walk.setChecked(False)
        
        self.Mouse_track_action = QAction("鼠标跟随", self)
        self.Mouse_track_action.setCheckable(True)
        self.Mouse_track_action.setChecked(False)
        
        # 工具菜单
        self.Tools_menu = QMenu("小工具", self)
        get_weather_action = QAction("实时天气", self)
        self.Tools_menu.addAction(get_weather_action)
        get_weather_action.triggered.connect(self.get_weather)
        
        lianliankan_action = QAction("连连看", self)
        self.Tools_menu.addAction(lianliankan_action)
        lianliankan_action.triggered.connect(self.run_external_exe)
        
        creOrg_action = QAction("来个欧润吉", self)
        self.Tools_menu.addAction(creOrg_action)
        creOrg_action.triggered.connect(createOrange)

        sysState_action = QAction("显示/隐藏:CPU/内存占用", self)
        self.Tools_menu.addAction(sysState_action)
        sysState_action.triggered.connect(self.changesysState_action)
        
        # 系统操作菜单项
        hide_action = QAction("隐藏到托盘", self)
        hide_action.triggered.connect(self.hide)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.ExitApp)
        
        # 将所有菜单项添加到主菜单
        self.menu.addAction(show_ai)
        self.menu.addAction(self.show_bottom_chat)
        self.menu.addAction(self.lock_action)
        self.menu.addSeparator()
        self.menu.addMenu(self.memu_zoom)
        self.menu.addSeparator()
        self.menu.addMenu(self.change_Expression)
        self.menu.addMenu(self.change_Motion)
        self.menu.addAction(self.auto_talk)
        self.menu.addAction(self.auto_walk)
        self.menu.addAction(self.Mouse_track_action)
        self.menu.addSeparator()
        self.menu.addMenu(self.Tools_menu)
        self.menu.addSeparator()
        self.menu.addAction(hide_action)
        self.menu.addAction(exit_action)
    
    # =====================
    # 事件处理方法
    # =====================
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        self.mouse_thread.quit()
        self.mouse_thread.wait()
        self.monitor_thread.quit()
        self.monitor_thread.wait()
        event.accept()
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件处理"""
        if self.Lock:
            return
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.Live2DView.model.Rotate(0)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件处理"""
        if self.Lock:
            return
        if self.dragging:
            self.move(event.globalPos() - self.offset)
            self.update_thought_bubble_position()
            self.update_hefengweather_position()
    
    def enterEvent(self, event: QEnterEvent):
        """鼠标进入窗口事件处理"""
        if self.Lock:
            return
        if self.Live2DView.issnap > 0 and not self.dragging:
            self.Live2DView.model.Update()
            self.Live2DView.model.SetExpression("问号")
            if self.Live2DView.issnap == 1:
                self.Live2DView.model.SetOffset(0.2, 0)
            if self.Live2DView.issnap == 2:
                self.Live2DView.model.SetOffset(-0.2, 0)
            if self.Live2DView.issnap == 3:
                self.Live2DView.model.SetOffset(0, -0.2)
            if self.Live2DView.issnap == 4:
                self.Live2DView.model.SetOffset(0, 0.2)
        super().enterEvent(event)
    
    def leaveEvent(self, event: QEvent):
        """鼠标离开窗口事件处理"""
        if self.Lock:
            return
        if self.Live2DView.issnap and not self.dragging:
            self.Live2DView.model.Update()
            self.Live2DView.model.ResetExpression()
        self.Live2DView.model.SetOffset(0, 0)
        super().leaveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件处理"""
        if self.Lock:
            return
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.Snap()
    
    def wheelEvent(self, event):
        """鼠标滚轮事件处理"""
        if self.Lock:
            return
        if self.Live2DView.issnap > 0:
            return
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()
    
    def contextMenuEvent(self, event):
        """右键菜单事件处理"""
        self.menu.exec_(QCursor.pos())
    
    def dragEnterEvent(self, event):
        """拖放进入事件处理"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """文件拖放事件处理"""
        # 获取拖入的文件路径
        file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
        texttitle = "确认放入回收站"
        textinfo = f"确定要将 {len(file_paths)} 个文件移至回收站吗？\n{chr(10).join(file_paths[:5])}"
        completeinfo = "个文件移至回收站。"
        
        if self.Live2DView.modelpath.find(r"Doro.model3.json"):
            texttitle = "吃掉欧润吉"
            textinfo = f"哇！人，这 {len(file_paths)} 个欧润吉是给我吃的吗？\n{chr(10).join(file_paths[:5])}"
            completeinfo = "个欧润吉吃掉啦。"
        
        # 确认操作
        reply = QMessageBox.question(self, texttitle, textinfo, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success_count = 0
            for file_path in file_paths:
                try:
                    fixed_path = file_path.replace('/', '\\')  # 转换为反斜杠
                    send2trash(fixed_path)
                    success_count += 1
                except Exception as e:
                    print(f"无法删除 {file_path}: {e}")
            QMessageBox.information(self, "完成", f"成功将 {success_count} {completeinfo}")
            print("文件已移至回收站")
        else:
            print("取消文件删除操作")
    
    # =====================
    # Live2D模型相关方法
    # =====================
    
    def change_Model(self, sPath):
        """更换Live2D模型"""
        self.Live2DView.LoadnewModelPath(sPath)
        self.live2dInited()
    
    def live2dInited(self):
        """Live2D模型初始化完成后的处理"""
        self.zoom_def()
        
        # 自动加载表情
        actiongs = self.action_group_Exp.actions()
        for act in actiongs:
            self.action_group_Exp.removeAction(act)
            self.change_Expression.removeAction(act)
        
        expressions = ["默认"]
        for text in expressions:
            action = QAction(text, self)
            action.setCheckable(True)
            action.setChecked(False)
            self.action_group_Exp.addAction(action)
            self.change_Expression.addAction(action)
        
        expressions = self.Live2DView.model.GetExpressionIds()
        for text in expressions:
            action = QAction(text, self)
            action.setCheckable(True)
            action.setChecked(False)
            self.action_group_Exp.addAction(action)
            self.change_Expression.addAction(action)
        
        # 自动加载动作
        actiongs = self.action_group_motion.actions()
        for act in actiongs:
            self.action_group_motion.removeAction(act)
            self.change_Motion.removeAction(act)
        
        motions = ["默认"]
        for text in motions:
            action = QAction(text, self)
            action.setCheckable(True)
            action.setChecked(False)
            self.action_group_motion.addAction(action)
            self.change_Motion.addAction(action)
        
        motions = self.Live2DView.model.GetMotionGroups()
        for text in motions:
            action = QAction(text, self)
            action.setCheckable(True)
            action.setChecked(False)
            self.action_group_motion.addAction(action)
            self.change_Motion.addAction(action)
        
        # 重置动作状态
        self.circleMotion_timer.stop()
        self.timeOn = False
        self.motionname = "默认"
        self.Live2DView.model.Update()

    # 修改模型透明度
    def on_alpha_changed(self, alpha):
        print(f"透明度{alpha}")
        self.Live2DView.set_Opacity(alpha)
    
    # =====================
    # 缩放与尺寸管理
    # =====================
    
    def update_size(self):
        """更新窗口尺寸"""
        new_width = int(self.original_size.width() * self.scale_factor)
        new_height = int(self.original_size.height() * self.scale_factor)
        new_height = int(new_width * self.globalcfg.live2dLWa)
        self.resize(new_width, new_height + self.sendBtn.height() + 2)
        
        if self.Live2DView.Inited:
            self.Live2DView.resizeGL(new_width, new_height)
        
        if not self.thought_bubble.isHidden():
            available_width = self.width() - 20
            self.thought_bubble.setFixedWidth(available_width)
            self.thought_bubble.adjustSize()
        
        self.update()
    
    def zoom_in(self):
        """放大窗口"""
        self.scale_factor *= 1.05
        self.scale_factor = min(self.scale_factor, 100.0)
        self.update_size()
    
    def zoom_out(self):
        """缩小窗口"""
        self.scale_factor *= 0.95
        self.scale_factor = max(self.scale_factor, 0.2)
        self.update_size()
    
    def zoom_def(self):
        """恢复默认大小"""
        print("恢复默认大小")
        self.scale_factor = 1.0
        self.update_size()
    
    # =====================
    # 边缘吸附功能
    # =====================
    
    def Snap(self):
        """窗口边缘吸附功能"""
        if not self.Live2DView.modelpath.find(r"Doro.model3.json"):
            return
        if self.IsWalking:
            return  # 开启闲逛不允许边缘吸附
        
        self.snap_distance = 20    # 吸附距离
        self.update_size()  # 不加这行，多屏幕吸附可能出问题
        
        window_rect = self.frameGeometry()
        window_center = window_rect.center()
        
        # 确定窗口所在的屏幕
        screen = QApplication.screenAt(window_center)
        if not screen:
            # 找到与窗口中心最近的屏幕
            screens = QApplication.screens()
            min_distance = float('inf')
            closest_screen = None
            for s in screens:
                screen_center = s.geometry().center()
                dx = screen_center.x() - window_center.x()
                dy = screen_center.y() - window_center.y()
                distance = dx * dx + dy * dy  # 平方距离
                if distance < min_distance:
                    min_distance = distance
                    closest_screen = s
            screen = closest_screen if closest_screen else QApplication.primaryScreen()
        if not screen:
            return
        
        available = screen.geometry()
        new_x = window_rect.left()
        new_y = window_rect.top()
        nsnaptype = 0
        
        # Y轴判断
        top_dist = abs(window_rect.top() - available.top())
        bottom_dist = abs(window_rect.bottom() - available.bottom())
        if top_dist <= self.snap_distance or bottom_dist <= self.snap_distance or window_rect.top() < available.top() or window_rect.bottom() > available.bottom():
            if top_dist < bottom_dist:
                new_y = available.top() - int(window_rect.height() * 0.6)
                self.Live2DView.model.Rotate(180)
                nsnaptype = 3
            else:
                new_y = available.bottom() - int(window_rect.height() * 0.3)
                self.Live2DView.model.Rotate(0)
                nsnaptype = 4
        
        # X轴判断
        left_dist = abs(window_rect.left() - available.left())
        right_dist = abs(window_rect.right() - available.right())
        if left_dist <= self.snap_distance or right_dist <= self.snap_distance or window_rect.left() < available.left() or window_rect.right() > available.right():
            if left_dist < right_dist:
                new_x = available.left() - int(window_rect.width() * 0.6)
                self.Live2DView.model.Rotate(-90)
                nsnaptype = 1
            else:
                new_x = available.right() - int(window_rect.width() * 0.4)
                self.Live2DView.model.Rotate(90)
                nsnaptype = 2
        
        # 如果位置变化，执行吸附
        if new_x != window_rect.left() or new_y != window_rect.top():
            self.move(new_x, new_y)
            self.Live2DView.issnap = nsnaptype
            # 动作停止
            self.circleMotion_timer.stop()
            self.timeOn = False
            self.motionname = "默认"
            self.Live2DView.model.Update()
            # 快捷聊天功能隐藏
            self.inputLineEdit.hide()
            self.show_bottom_chat.setChecked(False)
            self.sendBtn.hide()
            self.bottom_chat = False
            self.update_size()
        else:
            if self.Live2DView.issnap > 0:
                self.Live2DView.issnap = 0
                self.Live2DView.model.ResetExpression()
                self.Live2DView.model.Update()
    
    # =====================
    # 表情与动作控制
    # =====================
    
    def OnclickchangeExp(self, action: QAction):
        """切换表情"""
        if action.text() != "":
            self.Live2DView.model.SetExpression(action.text())
    
    def OnclickchangeMotion(self, action: QAction):
        """切换动作"""
        print(f"切换动作{action.text()}")
        if self.IsWalking:
            return
        if action.text() != "默认":
            if self.timeOn:
                self.motionname = action.text()
                return
            self.Live2DView.model.Update()
            self.Live2DView.model.StartMotion(action.text(), 0, 1, onFinishMotionHandler=self.onfinishmotionhd)
            self.timeOn = True
            self.motionname = action.text()
        else: 
            self.circleMotion_timer.stop()
            self.timeOn = False
            self.motionname = "默认"
            self.Live2DView.model.Update()
        
    
    def onfinishmotionhd(self):
        if not self.timeOn:
            return
        # print(f"动作结束{ self.Live2DView.model.IsMotionFinished()}")
        self.circleMotion_timer.timeout.connect( self.onfinishmotion2)
        self.circleMotion_timer.start(self.circleMotiontime)

    def onfinishmotion2(self):
        # print(f"动作结束{ self.Live2DView.model.IsMotionFinished()}")
        if self.Live2DView.model.IsMotionFinished():
            self.Live2DView.model.Update()
            self.Live2DView.model.StartMotion(self.motionname, 0, 1, onFinishMotionHandler=self.onfinishmotionhd)
            self.circleMotion_timer.stop()

    def onfinishmotion(self):
        """动作完成后的处理"""
        if self.isHidden():
            # 窗口隐藏时自动恢复默认动作
            self.circleMotion_timer.stop()
            self.timeOn = False
            self.motionname = "默认"
        self.Live2DView.model.Update()
        if self.timeOn:
            self.Live2DView.model.StartMotion(self.motionname, 0, 1)
            self.circleMotion_timer.singleShot(self.circleMotiontime, self.onfinishmotion)
    
    # =====================
    # 自动行为与动画
    # =====================
    
    def OnclickAutobehavier(self):
        """切换自动行为状态"""
        if not self.Live2DView.modelpath.find(r"Doro.model3.json"):
            self.AutoChange = False
            self.auto_talk.setChecked(False)
            return
        self.AutoChange = not self.AutoChange
        if self.AutoChange:
            self.auto_talk.setChecked(True)
            self.jump_animation()  # 立即触发一次
            autotime = self.globalcfg.autoThinkTime
            if autotime > 120 or autotime < 5:
                autotime = 10
            self.interaction_timer.start(int(autotime * 1000))  # 每xx秒触发一次随机行为
            if self.bottom_chat:
                self.on_show_bottom_chat()
                self.show_bottom_chat.setChecked(False)
        else:
            self.auto_talk.setChecked(False)
            self.interaction_timer.stop()
    
    def random_behavior(self):
        """随机行为选择器"""
        behaviors = [
            lambda: self.jump_animation(),
            lambda: self.random_thought_bubble()
        ]
        weights = [1, 9]  # 权重比例
        selected_behavior = choices(behaviors, weights=weights, k=1)[0]
        selected_behavior()  # 触发行为
    
    def jump_animation(self):
        """跳跃动画效果"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        start_rect = self.geometry()
        jump_rect = QRect(start_rect.x(), int(start_rect.y() - start_rect.height() / 5),
                         start_rect.width(), start_rect.height())
        self.animation.setKeyValueAt(0.5, jump_rect)
        self.animation.setEndValue(start_rect)
        self.animation.start()
    
    def random_thought_bubble(self):
        """随机显示思考气泡"""
        thinktext_List = self.globalcfg.thinktext
        thinktext = choice(thinktext_List)
        if thinktext.get("text"):
            self.show_thought_bubble(thinktext.get("text"))
        if thinktext.get("exp"):
            self.Live2DView.model.SetExpression(thinktext.get("exp"))
    
    # =====================
    # 气泡与聊天功能
    # =====================
    
    def show_thought_bubble(self, text, delay=5000):
        """显示思考气泡"""
        font = QFont(myFont().getFont(), int(13*self.scale_factor))
        self.thought_bubble.setFont(font)
        self.thought_bubble.setText(text)
        self.thought_bubble.setWordWrap(True)  # 启用自动换行
        available_width = self.width() - 20
        self.thought_bubble.setFixedWidth(available_width)
        self.thought_bubble.adjustSize()
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
        """更新气泡位置"""
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
    
    def onReceivedLLM(self, content):
        """接收LLM响应的处理"""
        self.show_thought_bubble(content, 8000)
        if self.globalcfg.TTSEn:
            TTSPlayer.play(content)
        # if self.globalcfg.TCP_sendport > 0:
        #     send_to_port(content, remote_port=self.globalcfg.TCP_sendport)
    
    def on_show_bottom_chat(self):
        """切换底部聊天窗口显示"""
        if self.Live2DView.issnap > 0:
            return
        self.bottom_chat = not self.bottom_chat
        if self.bottom_chat:
            self.show_bottom_chat.setChecked(True)
            self.inputLineEdit.show()
            self.sendBtn.show()
            if self.AutoChange:
                self.auto_talk.setChecked(False)
                self.interaction_timer.stop()
        else:
            self.inputLineEdit.hide()
            self.show_bottom_chat.setChecked(False)
            self.sendBtn.hide()
        self.update_size()
    
    def send_message(self):
        """发送消息"""
        user_input = self.inputLineEdit.text().strip()
        if not user_input:
            return
        if self.AutoChange:
            self.auto_talk.setChecked(False)
            self.interaction_timer.stop()
        self.inputLineEdit.clear()
        self.ai_window.chat_widget.send_message(user_input)  # 调用聊天窗口的功能


    def on_TCPreceived_text(self, user_input):
        if not user_input:
            return
        
        # if self.globalcfg.Live_Danmu_Filter and not str(user_input).startswith(self.globalcfg.Live_Danmu_Filter):
        #     return
        if self.AutoChange:
            self.auto_talk.setChecked(False)
            self.interaction_timer.stop()
        self.inputLineEdit.clear()
        self.ai_window.chat_widget.send_message(user_input)  # 调用聊天窗口的功能
        # send_to_port(text, remote_port=12345, local_port=12344)
    
    # =====================
    # 天气功能
    # =====================
    
    def get_weather(self):
        """获取并显示天气信息"""
        if self.hefengweather:
            self.hefengweather.refresh()
            self.hefengweather.show()
            self.update_hefengweather_position()
    
    def update_hefengweather_position(self):
        """更新天气窗口位置"""
        if not self or not self.hefengweather:
            return
        # 获取 DesktopPet 的位置和尺寸
        desktop_pos = self.pos()
        desktop_size = self.size()
        # 计算新位置：水平居中，位于 DesktopPet 右方
        x = desktop_pos.x() + desktop_size.width()
        y = desktop_pos.y()
        # 移动并显示 thought_bubble
        self.hefengweather.move(x, y)
    
    # =====================
    # 闲逛功能
    # =====================
    
    def OnclickAutowalk(self):
        """切换闲逛模式"""
        if self.auto_walk.isChecked():
            self.move_timer.start(7000)  # 7秒
            # 立即开始第一次移动
            self.start_new_movement()
            self.IsWalking = True
        else:
            self.move_timer.stop()
            self.IsWalking = False
    
    def get_current_screen_geometry(self):
        """获取当前窗口所在屏幕的几何区域"""
        current_pos = self.pos()
        screens = QApplication.screens()
        # 找到包含当前窗口中心点的屏幕
        center_point = self.rect().center()
        window_center = self.mapToGlobal(center_point)
        for screen in screens:
            if screen.geometry().contains(window_center):
                return screen.geometry(), screen
        # 如果没找到（理论上不会发生），返回主屏幕
        primary_screen = QApplication.primaryScreen()
        return primary_screen.geometry(), primary_screen
    
    def get_safe_boundaries(self):
        """获取当前屏幕的安全边界（考虑窗口尺寸）"""
        screen_geo, _ = self.get_current_screen_geometry()
        # 安全边界：确保窗口完全在当前屏幕区域内
        safe_x_min = screen_geo.x()
        safe_x_max = screen_geo.x() + screen_geo.width() - self.width()
        safe_y_min = screen_geo.y()
        safe_y_max = screen_geo.y() + screen_geo.height() - self.height()
        return safe_x_min, safe_x_max, safe_y_min, safe_y_max
    
    def is_point_on_screen(self, x, y):
        """检查点是否在任意一个屏幕上"""
        screens = QApplication.screens()
        point = QPoint(x, y)
        for screen in screens:
            screen_geo = screen.geometry()
            if screen_geo.contains(point):
                return True
        return False
    
    def get_random_target_position(self):
        """生成距离当前位置不超过100像素的随机目标位置（多屏幕支持）"""
        current_x = self.x()
        current_y = self.y()
        # 获取安全边界
        safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_boundaries()
        # 限制移动范围：距离当前位置不超过100像素
        max_distance = 500
        min_distance = 300
        max_attempts = 100  # 防止无限循环
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            # 生成随机角度（0-360度）
            angle = uniform(0, 2 * pi)
            # 生成随机距离（像素）
            distance = uniform(min_distance, max_distance)
            # 计算偏移量
            dx = int(distance * cos(angle))
            dy = int(distance * sin(angle))
            # 计算目标位置
            target_x = current_x + dx
            target_y = current_y + dy
            # 检查是否在安全区域内
            if (safe_x_min <= target_x <= safe_x_max and
                safe_y_min <= target_y <= safe_y_max):
                # 进一步检查目标位置是否在某个屏幕上（防止跨屏幕间隙）
                if self.is_point_on_screen(target_x, target_y):
                    return QPoint(target_x, target_y)
        # 如果多次尝试失败，返回一个安全的默认位置
        fallback_x = max(safe_x_min, min(safe_x_max, current_x))
        fallback_y = max(safe_y_min, min(safe_y_max, current_y))
        return QPoint(fallback_x, fallback_y)
    
    def start_new_movement(self):
        """开始一次新的移动过程"""
        # 如果动画正在运行，先停止
        if self.move_animation.state() == QPropertyAnimation.Running:
            self.move_animation.stop()
        self.Live2DView.issnap = 0  # 取消边缘吸附状态
        self.Live2DView.model.Rotate(0)
        
        # 如果模型有动作，也需要停止
        if self.Live2DView.modelpath.find(r"Doro.model3.json"):
            self.Live2DView.model.StopAllMotions()
            self.circleMotion_timer.stop()
            self.timeOn = False
            self.Live2DView.model.Update()
            self.Live2DView.model.StartMotion("跑", 0, 1)  # 播放奔跑动画
        
        # 生成随机目标位置（距离当前位置不超过100像素）
        target_pos = self.get_random_target_position()
        # 计算移动方向
        dx = target_pos.x() - self.x()
        leftorright = -1 if dx > 0 else 1 if dx < 0 else 1
        self.Live2DView.SetModelScaleX(leftorright)
        # 设置动画参数
        self.move_animation.setStartValue(self.pos())
        self.move_animation.setEndValue(target_pos)
        self.move_animation.start()
    
    def on_animation_state_changed(self, new_state, old_state):
        """动画状态变化时的处理"""
        if new_state == QPropertyAnimation.Running:
            self.IsWalking = True
        elif new_state == QPropertyAnimation.Stopped and old_state == QPropertyAnimation.Running:
            print(f"闲逛模式: 到达位置 {self.pos()}")
    
    # =====================
    # 窗口管理与系统托盘
    # =====================
    
    def lock_window(self):
        """锁定窗口（禁止交互）"""
        self.Lock = self.lock_action.isChecked()
        self.update_mouse_passthrough()
    
    def unlock_window(self):
        """解锁窗口"""
        self.Lock = False
        self.lock_action.setChecked(False)
        self.update_mouse_passthrough()
    
    def update_mouse_passthrough(self):
        """更新鼠标穿透设置"""
        print("Lock 状态:", self.Lock)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, self.Lock)
        flags = Qt.Window
        if not self.globalcfg.FrontProcess:
            flags |= (Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        else:
            flags |= (Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        if self.Lock:
            flags |= Qt.WindowTransparentForInput
        
        # 强制刷新 native 窗口句柄
        self.hide()
        self.setWindowFlags(flags)
        self.show()
        self.raise_()
        self.activateWindow()
    
    def show_deepseek_window(self):
        """显示主应用程序窗口"""
        if not self.ai_window:
            return
        self.ai_window.show()
        self.ai_window.raise_()
    
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("data/icons/app.ico"))
        # 创建右键菜单
        tray_menu = QMenu()
        show_action = QAction("显示窗口", self)
        unlock_action = QAction("取消锁定", self)
        quit_action = QAction("退出", self)
        # 添加菜单项
        tray_menu.addAction(show_action)
        tray_menu.addAction(unlock_action)
        tray_menu.addAction(quit_action)
        # 设置菜单
        self.tray_icon.setContextMenu(tray_menu)
        # 连接信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        show_action.triggered.connect(self.show_window)
        quit_action.triggered.connect(self.ExitApp)
        unlock_action.triggered.connect(self.unlock_window)
        # 显示托盘图标
        self.tray_icon.show()
    
    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件处理"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """显示窗口"""
        self.showNormal()
        self.raise_()
        self.activateWindow()
    
    # =====================
    # 外部程序与退出
    # =====================
    
    def run_external_exe(self):
        """运行外部程序（连连看）"""
        # 替换为你的 .exe 文件路径
        exe_path = r"DoroLianliankan.exe"
        self.process = QProcess(self)
        self.process.start(exe_path)
        if not self.process.waitForStarted():
            print("无法启动连连看程序，请检查路径是否正确。")
        else:
            print("程序已启动。")
    
    def update_label(self, x, y):
        """鼠标移动事件处理"""
        if self.globalcfg.wallpaperType == 2:
            get_WallpaperWindow().updateMouse(x, y)
        if self.Mouse_track_action.isChecked() and not self.Live2DView.issnap > 0:
            self.Live2DView.MouseTrack(x, y)
    
    def update_sysstate(self, text):
        """系统状态事件处理"""
        if text: 
            self.Live2DView.sys_state = text

    def changesysState_action(self):
        self.Live2DView.sys_en = not self.Live2DView.sys_en

    def ExitApp(self):
        """退出应用程序"""
        self.mouse_thread.exit()
        self.monitor_thread.exit()
        print("程序退出")
        QApplication.instance().quit()


# ======================
# 主程序入口
# ======================

# if __name__ == '__main__':
#     """程序启动入口点"""
#     app = QApplication(sys.argv)
#     font = QFont(myFont().getFont(), 13)
#     app.setFont(font)
#     pet = DesktopPet()
#     pet.show()
#     sys.exit(app.exec_())