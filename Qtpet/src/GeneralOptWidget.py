from .GeneralOptData import get_GeneralOptData
from .VoskRecognition import VoskSettingWindow
from .switchbtn import SwitchButton

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class GeneralOptWidget(QWidget):
    # 自定义信号
    windowSizeChanged = pyqtSignal(QSize)
    alphaChanged = pyqtSignal(float)
    themeChanged = pyqtSignal(str)
    live2dLWaChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfgdata = get_GeneralOptData()
        self.initUI()
       

    def initUI(self):

         # 主布局
        main_layout = QVBoxLayout(self)

        # 创建一个用于承载 QFormLayout 的容器
        self.form_container = QWidget(self)
        self.form_container.setObjectName("GeneralOptWidgetListWisget")
        layout = QFormLayout(self.form_container)
        

        # 将 form_container 放入 QScrollArea
        scroll_area = QScrollArea(self)
        # scroll_area.setAttribute(Qt.WA_TranslucentBackground)
        scroll_area.setAutoFillBackground(False)
        scroll_area.viewport().setAutoFillBackground(False)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.form_container)

        # 将 scroll_area 加入主布局
        main_layout.addWidget(scroll_area)


        # layout = QFormLayout(self)

        # 窗口尺寸选择
        self.size_combo = QComboBox()
        self.size_combo.setMinimumWidth(200)
        self.populate_sizes()
        hbox = QHBoxLayout()
        hbox.addWidget(self.size_combo)
        hbox.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox.addWidget(QLabel("切换窗口尺寸，实时生效"))
        
        layout.addRow(QLabel("窗口尺寸"), hbox)

        # 透明度控制
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setMinimumWidth(200)
        self.alpha_slider.setRange(15, 100)
        
        # 是否有前台窗口
        self.switch = SwitchButton()
        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.switch)
        hbox3.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox3.addWidget(QLabel("切换前台启动/后台启动，重启生效"))
        layout.addRow(QLabel("前台进程"), hbox3)

        self.switchTTS = SwitchButton()
        hbox12 = QHBoxLayout()
        hbox12.addWidget(self.switchTTS)
        hbox12.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox12.addWidget(QLabel("是否开启TTS"))
        layout.addRow(QLabel("开启TTS"), hbox12)

    
        # 添加一条水平分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)  # 水平线
        line.setFrameShadow(QFrame.Sunken)  # 阴影效果
        line.setFixedHeight(50)
        layout.addRow(line)

        # 人格市场地址
        self.prompturl = QLineEdit()
        self.prompturl.setMinimumWidth(200)
        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.prompturl)
        hbox4.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox4.addWidget(QLabel("内嵌网页工具，方便体验不同人格的对话"))
        layout.addRow(QLabel("人格市场网址"), hbox4)

        # 人格市场地址
        self.emojiurl = QLineEdit()
        self.emojiurl.setMinimumWidth(200)
        hbox8 = QHBoxLayout()
        hbox8.addWidget(self.emojiurl)
        hbox8.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox8.addWidget(QLabel("内嵌网页工具，表情包站"))
        layout.addRow(QLabel("表情包网址"), hbox8)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)  # 水平线
        line2.setFrameShadow(QFrame.Sunken)  # 阴影效果
        line2.setFixedHeight(50)
        layout.addRow(line2)

        # 默认live2d模型
        self.l2dmodeldefpath = QLineEdit()
        self.l2dmodeldefpath.setMinimumWidth(200)
        hbox5 = QHBoxLayout()
        hbox5.addWidget(self.l2dmodeldefpath)
        hbox5.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox5.addWidget(QLabel("默认live2d模型,可用相对路径"))
        layout.addRow(QLabel("默认live2d模型"), hbox5)


        self.live2dLWa_slider = QSlider(Qt.Horizontal)
        self.live2dLWa_slider.setMinimumWidth(200)
        self.live2dLWa_slider.setRange(20, 500)
        hbox6 = QHBoxLayout()
        hbox6.addWidget(self.live2dLWa_slider)
        hbox6.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox6.addWidget(QLabel("桌宠窗口的长宽比例，调节到合适的比例即可"))
        layout.addRow(QLabel("小窗比例"), hbox6)

        self.live2dalpha_slider = QSlider(Qt.Horizontal)
        self.live2dalpha_slider.setMinimumWidth(200)
        self.live2dalpha_slider.setRange(20, 100)
        hbox9 = QHBoxLayout()
        hbox9.addWidget(self.live2dalpha_slider)
        hbox9.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox9.addWidget(QLabel("桌宠窗口的透明度"))
        layout.addRow(QLabel("透明度"), hbox9)

        # 随机行为的间隔
        self.autoThinkTimeedit = QLineEdit("10")
        validator = QIntValidator(5, 999, self.autoThinkTimeedit)
        self.autoThinkTimeedit.setValidator(validator)
        self.autoThinkTimeedit.setMinimumWidth(200)
        hbox7 = QHBoxLayout()
        hbox7.addWidget(self.autoThinkTimeedit)
        hbox7.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox7.addWidget(QLabel("随机行为的间隔(s)，取值区间[5, 120]"))
        layout.addRow(QLabel("随机行为的间隔"), hbox7)

        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)  # 水平线
        line3.setFrameShadow(QFrame.Sunken)  # 阴影效果
        line3.setFixedHeight(50)
        layout.addRow(line3)


        # Vosk 
        self.VoskSettingpage = VoskSettingWindow()
        layout.addRow(self.VoskSettingpage)


        # 随机行为的间隔
        self.TCP_sendport_edit = QLineEdit("")
        validator = QIntValidator(100, 99999, self.TCP_sendport_edit)
        self.TCP_sendport_edit.setValidator(validator)
        self.TCP_sendport_edit.setMinimumWidth(200)

        self.TCP_litsenport_edit = QLineEdit("")
        validator = QIntValidator(100, 99999, self.TCP_litsenport_edit)
        self.TCP_litsenport_edit.setValidator(validator)
        self.TCP_litsenport_edit.setMinimumWidth(200)

        hbox10 = QHBoxLayout()
        hbox10.addWidget(self.TCP_sendport_edit)
        hbox10.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox10.addWidget(self.TCP_litsenport_edit)
        hbox10.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox10.addWidget(QLabel("  "))
        layout.addRow(QLabel("TCP设置"), hbox10)

        self.Live_RoomID_edit = QLineEdit("")
        self.Live_RoomID_edit.setMinimumWidth(200)

        self.Live_Danmu_Filter_edit = QLineEdit("")
        self.Live_Danmu_Filter_edit.setMinimumWidth(200)

        hbox11 = QHBoxLayout()
        hbox11.addWidget(QLabel("直播间ID"))
        hbox11.addWidget(self.Live_RoomID_edit)
        hbox11.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox11.addWidget(QLabel("弹幕唤醒前缀"))
        hbox11.addWidget(self.Live_Danmu_Filter_edit)
        hbox11.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox11.addWidget(QLabel("  "))
        layout.addRow(QLabel("直播设置"), hbox11)

        # 添加一个伸展空间项以防止压缩
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 信号连接
        self.size_combo.currentIndexChanged.connect(self.handle_size_change)
        self.live2dalpha_slider.valueChanged.connect(self.handle_alpha_change)
        self.switch.statusChanged.connect(self.frontprocesschanged)
        self.prompturl.textChanged.connect(self.prompturlchanged)
        self.emojiurl.textChanged.connect(self.emojiurlchanged)
        self.l2dmodeldefpath.textChanged.connect(self.l2dmodeldefpathchanged)
        self.live2dLWa_slider.valueChanged.connect(self.handle_live2dLWa_change)
        # self.switch.toggled.connect(lambda: print("状态切换到:", self.switch.isChecked()))
        self.autoThinkTimeedit.textEdited.connect(self.handle_autoThinkTimeedit_change)

        self.TCP_sendport_edit.textEdited.connect(self.handle_sendport_edit_change)
        self.TCP_litsenport_edit.textEdited.connect(self.handle_litsenport_edit_change)
        self.switchTTS.statusChanged.connect(self.switchTTSchanged)

        self.Live_RoomID_edit.textEdited.connect(self.Live_RoomID_edit_change)
        self.Live_Danmu_Filter_edit.textEdited.connect(self.Live_Danmu_Filter_edit_change)

        globalinit_timer = QTimer()
        globalinit_timer.singleShot(2000, self.globalinit)
       

    def globalinit(self):
        self.size_combo.setCurrentText(self.cfgdata.window_Size)
        self.live2dalpha_slider.setValue(int(self.cfgdata.alpha))  # 加载参数透明度
        self.switch.setChecked(self.cfgdata.FrontProcess)
        self.switchTTS.setChecked(self.cfgdata.TTSEn)
        self.prompturl.setText(self.cfgdata.promptmarketurl)
        self.emojiurl.setText(self.cfgdata.Emojiweburl)
        self.l2dmodeldefpath.setText(self.cfgdata.live2dmodeldefpath)
        self.live2dLWa_slider.setValue(int(self.cfgdata.live2dLWa*100))
        self.autoThinkTimeedit.setText(f"{self.cfgdata.autoThinkTime}")
        self.TCP_sendport_edit.setText(f"{self.cfgdata.TCP_sendport}")
        self.TCP_litsenport_edit.setText(f"{self.cfgdata.TCP_listenport}")
        self.Live_Danmu_Filter_edit.setText(self.cfgdata.Live_Danmu_Filter)
        self.Live_RoomID_edit.setText(self.cfgdata.Live_RoomID)

    def populate_sizes(self):
        screen = QApplication.primaryScreen()
        screen_size = screen.availableSize()

        default_sizes = [
            (int(screen_size.width() * 0.4), int(screen_size.height() * 0.4)),
            (screen_size.width() // 2, screen_size.height() // 2),
            (int(screen_size.width() * 0.6), int(screen_size.height() * 0.6)),
            (int(screen_size.width() * 0.75), int(screen_size.height() * 0.75)),
            (int(screen_size.width() * 0.85), int(screen_size.height() * 0.85)),
            (screen_size.width(), screen_size.height()),
            (800, 600),
            (1024, 768),
        ]

        # 按面积大小排序（从大到小）
        default_sizes.sort(key=lambda x: x[0] * x[1], reverse=True)

        for width, height in default_sizes:
            size = QSize(width, height)
            self.size_combo.addItem(f"{width}x{height}", size)


    def handle_size_change(self, index):
        size = self.size_combo.itemData(index)
        if isinstance(size, QSize):
            self.cfgdata.window_Size = f"{size.width()}x{size.height()}"
            self.windowSizeChanged.emit(size)
            # self.saveSettings()

    def handle_alpha_change(self, value):
        alpha = value / 100.0
        self.cfgdata.alpha = value
        self.alphaChanged.emit(alpha)
        # self.saveSettings()

    def frontprocesschanged(self):
        self.cfgdata.FrontProcess = self.switch.checked()

    def switchTTSchanged(self):
        self.cfgdata.TTSEn = self.switchTTS.checked()

    def prompturlchanged(self):
        self.cfgdata.promptmarketurl = self.prompturl.text()

    def emojiurlchanged(self):
        self.cfgdata.Emojiweburl = self.emojiurl.text()

    def l2dmodeldefpathchanged(self):
        self.cfgdata.live2dmodeldefpath = self.l2dmodeldefpath.text()

    def handle_live2dLWa_change(self, value):
        value = value / 100.0
        self.cfgdata.live2dLWa = value
        self.live2dLWaChanged.emit()

    def closeEvent(self, event):
        self.cfgdata.saveSettings()
        super().closeEvent(event)

    def handle_autoThinkTimeedit_change(self, text):
        if text:
            val = int(text)
            if val > 120 or val < 5:
                return
            self.cfgdata.autoThinkTime = val

    def handle_sendport_edit_change(self, text):
        if text:
            val = int(text)
            self.cfgdata.TCP_sendport = val

    def handle_litsenport_edit_change(self, text):
        if text:
            val = int(text)
            self.cfgdata.TCP_listenport = val

    def Live_RoomID_edit_change(self, text):
        if text:
            self.cfgdata.Live_RoomID = text
        
    def Live_Danmu_Filter_edit_change(self, text):
        if text:
            self.cfgdata.Live_Danmu_Filter = text

    # 接口方法

    def get_window_size(self):
        index = self.size_combo.currentIndex()
        if index >= 0:
            return self.size_combo.itemData(index)
        return QSize(800, 600)

    def set_window_size(self, size):
        if isinstance(size, QSize):
            index = self.size_combo.findData(size)
            if index >= 0:
                self.size_combo.setCurrentIndex(index)

    def get_alpha(self):
        return self.alpha_slider.value() / 100.0

    def set_alpha(self, alpha):
        value = int(alpha * 100)
        if value < 15:
            value = 15
        elif value > 100:
            value = 100
        self.alpha_slider.setValue(value)

    def get_switch_state(self):
        return self.switch.isChecked()

    def set_switch_state(self, state):
        self.switch.setChecked(state)