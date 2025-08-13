from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMenu, QMessageBox, QApplication, QStackedWidget
)
from PyQt5.QtGui import QIcon, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QSize, QPoint
import sys

from .option import get_OptionWidget
from .chatwidget import ChatWidget, ChatMessage

class myFont():
    def __init__(self):
        super().__init__()
        self.font_id = QFontDatabase.addApplicationFont("./cfg/zxf.ttf")
        if self.font_id == -1:
            print("Failed to load font.")
        else:
            families = QFontDatabase.applicationFontFamilies(self.font_id)
            if families:
                self.font_family = families[0]

    def getFont(self):
        return self.font_family

# async def main():
#     await MCPClient.connect_to_server("MCP/bilibili-mcp-main/bilibili_mcp.py")


class StyleLoader:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._cache = {}
        return cls._instance
    
    def load_theme(self, theme_name):
        if theme_name not in self._cache:
            try:
                with open(f"themes/{theme_name}.qss", "r",  encoding='utf-8') as f:
                    self._cache[theme_name] = f.read()
            except FileNotFoundError:
                return ""
        return self._cache[theme_name]


def get_windows_theme():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return 'light' if value == 1 else 'dark'
    except Exception:
        return 'unknown'

class MainAppWindow(QMainWindow):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool)
        self.initUI()
        
        self.current_ai_message = None
        self.loading_widget = None
        self.preset = 0
        self.style_loader = StyleLoader()
        # 获取系统颜色方案

        self.current_theme = "light"

        self.current_theme = get_windows_theme()
        self.apply_theme()
        # self.loadcfg()
        self.preset_options = self.options_widget.getpreset()
        # self.update_system_message("Doro")
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # self.on_alpha_changed(0.9)

        # 修改窗口大小
        self.margin = 5  # 边缘检测区域宽度
        self.dragging = False
        self.resize_dir = None
        self.drag_start_pos = None
        self.window_start_size = None
        self.drag_position= None

        

    def apply_theme(self):
        qss = self.style_loader.load_theme(self.current_theme)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)  # 确保qss字符串无语法错误
            self.update()  # 触发重绘

        
    def update_children_theme(self, widget):
        for child in widget.children():
            if isinstance(child, QWidget):
                if hasattr(child, "update_theme"):
                    child.update_theme(self.current_theme)
                self.update_children_theme(child)
                
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.theme_button.setIcon(QIcon("data/icons/light.ico") if self.current_theme == "light" else QIcon("data/icons/dark.ico"))
        self.preset_button.setIcon(QIcon("data/icons/personl.ico")if self.current_theme == "light" else QIcon("data/icons/persond.ico"))
        self.size_button.setIcon(QIcon("data/icons/sizel.ico")if self.current_theme == "light" else QIcon("data/icons/sized.ico"))
        self.exit_button.setIcon(QIcon("data/icons/exitl.ico")if self.current_theme == "light" else QIcon("data/icons/exitd.ico"))
        # self.general_button.setIcon(QIcon("./icons/settingl.ico")if self.current_theme == "light" else QIcon("./icons/settingd.ico"))
        if self.stack_widget.currentIndex() == 0:
            self.general_button.setIcon(QIcon("data/icons/settingl.ico")if self.current_theme == "light" else QIcon("data/icons/settingd.ico"))
        else:
            self.general_button.setIcon(QIcon("data/icons/returnl.ico")if self.current_theme == "light" else QIcon("data/icons/returnd.ico"))
        self.apply_theme()
        
    def maxwindow(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        return
    
    def hide(self):
        self.options_widget.GeneratorOptPage.cfgdata.saveSettings()
        self.close()

    def initUI(self):
        self.setWindowTitle("聊天")
        self.setWindowIcon(QIcon("data/icons/app.ico"))
        
        # self.setGeometry(100, 100, 1000, 800)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        main_widget = QWidget() # 聊天页面
        self.setCentralWidget(main_widget)
        
        # 主页面
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setObjectName("toolbar")
        layout.addWidget(toolbar)

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 0, 6, 0)
        
        # 这里改成人格名字
        self.title_label = QLabel("DoroPet")
        self.title_label.setObjectName("title_label")
        toolbar_layout.addWidget(self.title_label)
        toolbar_layout.addStretch()
        

        iconsize = 24
        # 通用设置
        self.general_button = QPushButton() # 通用设置
        self.general_button.setIcon(QIcon("data/icons/settingl.ico"))
        self.general_button.setIconSize(QSize(iconsize, iconsize))
        self.general_button.setObjectName("Tool_button")
        self.general_button.clicked.connect(self.set_Promptwidget)
        toolbar_layout.addWidget(self.general_button)

        self.preset_button = QPushButton() # 人格设置
        self.preset_button.setIcon(QIcon("data/icons/personl.ico"))
        self.preset_button.setIconSize(QSize(iconsize, iconsize))
        self.preset_button.setObjectName("Tool_button")
        self.preset_button.clicked.connect(self.set_personality)
        toolbar_layout.addWidget(self.preset_button)

        self.theme_button = QPushButton()   # 切换浅色深色主题
        self.theme_button.setIcon(QIcon("data/icons/light.ico"))
        self.theme_button.setIconSize(QSize(iconsize, iconsize))
        self.theme_button.setObjectName("Tool_button")
        self.theme_button.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_button)

        self.size_button = QPushButton()   # 窗口化最大化
        self.size_button.setIcon(QIcon("data/icons/sizel.ico"))
        self.size_button.setIconSize(QSize(iconsize, iconsize))
        self.size_button.setObjectName("Tool_button")
        self.size_button.clicked.connect(self.maxwindow)
        toolbar_layout.addWidget(self.size_button)


        self.exit_button = QPushButton() # 退出
        self.exit_button.setIcon(QIcon("data/icons/exitl.ico"))
        self.exit_button.setObjectName("Tool_button")
        self.exit_button.setIconSize(QSize(iconsize, iconsize))
        self.exit_button.clicked.connect(self.hide)
        toolbar_layout.addWidget(self.exit_button)


        # 创建堆叠窗口控件
        self.stack_widget = QStackedWidget()
        self.stack_widget.setObjectName("stackwidget")
        layout.addWidget(self.stack_widget)
        
        self.options_widget = get_OptionWidget() # 设置
        self.options_widget.GeneratorOptPage.windowSizeChanged.connect(self.on_size_changed)

        self.chat_widget = ChatWidget()


        self.stack_widget.addWidget(self.chat_widget)
        self.stack_widget.addWidget(self.options_widget)
        self.stack_widget.setCurrentIndex(0)

        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        for i in range(self.chat_widget.chat_container.layout().count()):
            if self.layout().itemAt(i):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, ChatMessage):
                    widget.adjust_size()

    # 槽函数 响应尺寸变化
    def on_size_changed(self, size):
        if self.isMaximized():
            return
        self.setFixedSize(size)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 记录鼠标按下时的全局坐标
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            if self.isMaximized():
                self.showNormal()  # 取消最大化以便拖动
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            # 计算新的窗口位置并移动
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = None  # 重置拖动位置
            event.accept()

    # def read_ini(self, file_path):
    #     config = configparser.RawConfigParser()
    #     read_files = config.read(file_path)

    #     if not read_files:
    #         self.show_error(f"配置文件不存在: {file_path}")
    #         return {}

    #     return {
    #         section: dict(config.items(section))
    #         for section in config.sections()
    #     }

    def show_error(self, message):
        """使用 PyQt 的 QMessageBox 显示错误信息"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def set_personality(self):
        # 创建人格菜单
        personality_menu = QMenu("选择人格", self)
        personality_menu.setObjectName("personality_menu")
        personality_menu.setAttribute(Qt.WA_TranslucentBackground)
        # 添加预设项
        for name in self.preset_options:
            action = personality_menu.addAction(name)
            action.triggered.connect(lambda checked, n=name: 
                self.update_system_message(n))
        
        # 获取触发菜单的控件位置
        btn = self.sender()  # 假设通过按钮触发
        pos = btn.mapToGlobal(QPoint(0, btn.height()))
        
        # 显示菜单（模态）
        personality_menu.exec_(pos)

    def set_Promptwidget(self):
        if self.stack_widget.currentIndex() == 0:
            self.general_button.setIcon(QIcon("data/icons/returnl.ico")if self.current_theme == "light" else QIcon("data/icons/returnd.ico"))
            self.stack_widget.setCurrentIndex(1)
        else:
            self.general_button.setIcon(QIcon("data/icons/settingl.ico")if self.current_theme == "light" else QIcon("data/icons/settingd.ico"))
            self.stack_widget.setCurrentIndex(0)
            

    def update_system_message(self, selected):
    # 这里使用 selected 和 preset_options 设置人格预设
        # self.chat_widget.set_system_message(self.preset_options[selected])
        # self.chat_widget.reset_messages()
        self.chat_widget.create_new_session_(selected)
        # self.title_label.setText(selected)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont(myFont().getFont(), 13)
    app.setFont(font)
    window = MainAppWindow()
    window.show()
    sys.exit(app.exec_())