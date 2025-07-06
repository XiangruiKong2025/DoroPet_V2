from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .switchbtn import SwitchButton
from .wallpaperassist import get_WallpaperWindow
from .GeneralOptData import get_GeneralOptData


class WallpaperOptWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.myWin = get_WallpaperWindow()
        self.cfgData = get_GeneralOptData()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 开关按钮
        switch_layout = QHBoxLayout()
        self.switch = SwitchButton()
        
        switch_layout.addStretch()
        switch_layout.addWidget(QLabel("开启壁纸"))
        switch_layout.addWidget(self.switch)
        layout.addLayout(switch_layout)

        # 壁纸类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["视频", "图片"])
        layout.addWidget(QLabel("壁纸类型:"))
        layout.addWidget(self.type_combo)

        # 设置面板堆叠
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # 初始化各类型面板
        self.create_video_page()
        self.create_img_page()

        # 连接信号
        self.type_combo.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        self.switch.statusChanged.connect(self.WalpaperEnable)

        self.Init()

    def Init(self):
        self.myWin = get_WallpaperWindow()
        if self.cfgData.wallpaperType == 1:
            self.type_combo.setCurrentIndex(0)
            self.myWin.startVideo(self.cfgData.wallpaperPath_V)
            
        if self.cfgData.wallpaperType == 2:
            self.type_combo.setCurrentIndex(1)
            self.img_mode_combo.setCurrentIndex(2)
            self.myWin.startImg(self.cfgData.wallpaperPath_P, 2)
            

    def create_video_page(self):
        page = QWidget()
        layout = QHBoxLayout()
        self.video_path = QLineEdit(self.cfgData.wallpaperPath_V)

        self.video_button = QPushButton("选择视频")
        self.video_button.setObjectName("Tool_button")
        self.video_button.clicked.connect(lambda: self.select_file(self.video_path, "选择视频", "*.mp4 *.avi"))
        layout.addWidget(QLabel("视频路径:"))
        layout.addWidget(self.video_path)
        layout.addWidget(self.video_button)
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)


    def create_img_page(self):
        page = QWidget()
        layout = QHBoxLayout()
        self.img_path = QLineEdit(self.cfgData.wallpaperPath_P)
        self.img_button = QPushButton("选择图片")
        self.img_button.setObjectName("Tool_button")
        self.img_button.clicked.connect(lambda: self.select_file(self.img_path, "选择图片", "*.jpg *.png *.jpeg"))
        
        # 新增：显示模式选择
        self.img_mode_combo = QComboBox()
        self.img_mode_combo.addItems(["拉伸", "适应", "填充"])
        self.img_mode_combo.currentIndexChanged.connect(self.on_img_mode_change)

        layout.addWidget(QLabel("图片路径:"))
        layout.addWidget(self.img_path)
        layout.addWidget(self.img_button)
        layout.addWidget(QLabel("显示模式:"))
        layout.addWidget(self.img_mode_combo)

        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def select_file(self, line_edit, caption, filter):
        path, _ = QFileDialog.getOpenFileName(self, caption, "", filter)
        if path:
            line_edit.setText(path)

    def on_img_mode_change(self, index):
        path = self.img_path.text()
        if not path:
            return
        
        
        if self.switch.checked():
            mode = self.img_mode_combo.currentIndex()
            self.myWin = get_WallpaperWindow()
            self.myWin.startImg(path, mode)
            self.myWin.showFullScreen()

    def WalpaperEnable(self):
        if self.switch.checked():
            current_index = self.type_combo.currentIndex()
            if current_index == 0:
                path = self.video_path.text()
                if not path:
                    QMessageBox.warning(self, "错误", "请先选择视频文件路径")
                    return
                self.myWin = get_WallpaperWindow()
                self.myWin.startVideo(path)
                self.myWin.showFullScreen()

                if not self.myWin.height() == QDesktopWidget().screenGeometry().height():
                    self.myWin.startVideo(path)

                    
            elif current_index == 1:
                path = self.img_path.text()
                if not path:
                    QMessageBox.warning(self, "错误", "请先选择图片文件路径")
                    return
                mode = self.img_mode_combo.currentIndex()
                self.myWin = get_WallpaperWindow()
                self.myWin.startImg(path, mode)
                self.myWin.showFullScreen()
        else:
            if self.myWin:
                self.myWin.deleteAll()
                self.myWin.close()
                self.myWin = None
