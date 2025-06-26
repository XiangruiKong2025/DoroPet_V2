import sys
import json
import os
import configparser
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from .switchbtn import SwitchButton
from .WebViewTool import WebCtrlTool
from .live2dview import Live2DCanvas
from .LLMConfigWindow import LLMConfigWindow

class GeneralOptData(QObject):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("cfg/app.cfg", QSettings.IniFormat)
        self.window_Size = "800x600"
        self.alpha = 90
        self.FrontProcess = False
        self.loadSettings()

    def loadSettings(self):
        self.settings.beginGroup("Appcfg")
        # 窗口尺寸
        self.window_Size = self.settings.value("WindowSize", "800x600")
        # 透明度
        self.alpha = self.settings.value("Alpha", 90)
        # 前台进程
        self.FrontProcess = self.settings.value("FrontProcess", False, type=bool)
        # live2d，默认加载地址
        self.live2dmodeldefpath = self.settings.value("live2dmodeldefpath", "")
        # 人格市场地址
        self.promptmarketurl = self.settings.value("PromptMarketUrl", "https://www.jasongjz.top/")


        self.settings.endGroup()

    def saveSettings(self):
        self.settings.beginGroup("Appcfg")
        # 窗口尺寸
        self.settings.setValue("WindowSize", self.window_Size)
        # 透明度
        self.settings.setValue("Alpha", self.alpha)
        # 开关状态
        self.settings.setValue("FrontProcess", self.FrontProcess)
        # live2d，默认加载地址
        self.settings.setValue("live2dmodeldefpath", self.live2dmodeldefpath)
        # 人格市场地址
        self.settings.setValue("PromptMarketUrl", self.promptmarketurl)
        self.settings.endGroup()

class OptionWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 主窗口布局：水平布局
        main_layout = QHBoxLayout(self)

        # 左侧菜单区域
        menu_widget = QWidget()
        menu_widget.setObjectName("menuwidget")
        menu_layout = QVBoxLayout()
        
        # 创建菜单按钮
        self.buttons = []
        # 创建按钮组
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        menu_items = ['通用', 'LLM模型', '人格','人格市场', 'live2d模型', '关于']
        for text in menu_items:
            btn = QPushButton(text)
            btn.setCheckable(True)  # 启用 checkable 状态
            btn.setObjectName("Menu_button")
            self.buttons.append(btn)
            self.button_group.addButton(btn)
        
        menu_layout.addWidget(self.buttons[0])
        menu_layout.addWidget(self.buttons[1])
        menu_layout.addWidget(self.buttons[2])
        menu_layout.addWidget(self.buttons[3])
        menu_layout.addWidget(self.buttons[4])
        menu_layout.addStretch()
        menu_layout.addWidget(self.buttons[5])
        menu_layout.setContentsMargins(5, 5, 0, 5)
        menu_layout.setSpacing(2)
        menu_widget.setLayout(menu_layout)

        # 右侧堆叠窗口
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("optwidget")

        # 通用配置
        self.GeneratorOptPage = GeneralOptWidget()
        self.stacked_widget.addWidget(self.GeneratorOptPage)

        # 模型配置
        self.ProviderOptPage = LLMConfigWindow()
        self.stacked_widget.addWidget(self.ProviderOptPage)

        # 人格编辑
        self.PromptOptPage = PromptOptionWidget()
        self.stacked_widget.addWidget(self.PromptOptPage)

        # 人格市场
        if self.GeneratorOptPage.cfgdata.promptmarketurl:
            self.webtest = WebCtrlTool(self.GeneratorOptPage.cfgdata.promptmarketurl ,"")
            self.webtest.setAcceptRequest(True)
        else:
            self.webtest = QWidget()
        
        self.stacked_widget.addWidget(self.webtest)

        # live2d配置
        self.Live2DOptPage = Live2DOptWidget()
        self.stacked_widget.addWidget(self.Live2DOptPage)

        # 关于作者
        AuthPage = AboutAuthorWindow()
        self.stacked_widget.addWidget(AuthPage)

        # 连接按钮点击信号到页面切换
        # for i, btn in enumerate(self.buttons):
        #     self.button_group.addButton(btn)
            # btn.clicked.connect(lambda checked, idx=i: self.stacked_widget.setCurrentIndex(idx))

        # 连接 toggled 信号
        self.button_group.buttonToggled.connect(self.on_button_toggled)


        # 设置布局比例（左侧1:右侧3）
        main_layout.addWidget(menu_widget, 1)
        main_layout.addWidget(self.stacked_widget, 8)

        # 初始选中第一个按钮
        self.buttons[0].setChecked(True)

    def getpreset(self):
        return self.PromptOptPage.preset_options
    
    def getProvider(self):
        return self.ProviderOptPage.get_current_service_config()
    
    def on_button_toggled(self, button, checked):
        if checked:
            index = self.buttons.index(button)
            self.stacked_widget.setCurrentIndex(index)


class GeneralOptWidget(QWidget):
    # 自定义信号
    windowSizeChanged = pyqtSignal(QSize)
    alphaChanged = pyqtSignal(float)
    themeChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfgdata = GeneralOptData()
        self.initUI()
       

    def initUI(self):
        layout = QFormLayout(self)

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
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.alpha_slider)
        hbox2.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox2.addWidget(QLabel("开启人格市场后，透明度无法实时更新，重启生效"))
        layout.addRow(QLabel("透明度"), hbox2)

        # 是否有前台窗口
        self.switch = SwitchButton()
        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.switch)
        hbox3.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox3.addWidget(QLabel("切换前台启动/后台启动，重启生效"))
        layout.addRow(QLabel("前台进程"), hbox3)

    
        # 人格市场地址
        self.prompturl = QLineEdit()
        self.prompturl.setMinimumWidth(200)
        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.prompturl)
        hbox4.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox4.addWidget(QLabel("默认：`https://www.jasongjz.top`  内嵌网页工具，方便体验不同人格的对话"))
        layout.addRow(QLabel("人格市场网址"), hbox4)

        # 默认live2d模型
        self.l2dmodeldefpath = QLineEdit()
        self.l2dmodeldefpath.setMinimumWidth(200)
        hbox5 = QHBoxLayout()
        hbox5.addWidget(self.l2dmodeldefpath)
        hbox5.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox5.addWidget(QLabel("默认live2d模型,可用相对路径。例如：models/Doro/Doro.model3.json"))
        layout.addRow(QLabel("默认live2d模型"), hbox5)

        # 信号连接
        self.size_combo.currentIndexChanged.connect(self.handle_size_change)
        self.alpha_slider.valueChanged.connect(self.handle_alpha_change)
        self.switch.statusChanged.connect(self.frontprocesschanged)
        self.prompturl.textChanged.connect(self.prompturlchanged)
        self.l2dmodeldefpath.textChanged.connect(self.l2dmodeldefpathchanged)
        # self.switch.toggled.connect(lambda: print("状态切换到:", self.switch.isChecked()))

        globalinit_timer = QTimer()
        globalinit_timer.singleShot(2000, self.globalinit)
       

    def globalinit(self):
        self.size_combo.setCurrentText(self.cfgdata.window_Size)
        self.alpha_slider.setValue(int(self.cfgdata.alpha))  # 加载参数透明度
        self.switch.setChecked(self.cfgdata.FrontProcess)
        self.prompturl.setText(self.cfgdata.promptmarketurl)
        self.l2dmodeldefpath.setText(self.cfgdata.live2dmodeldefpath)

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

    def prompturlchanged(self):
        self.cfgdata.promptmarketurl = self.prompturl.text()

    def l2dmodeldefpathchanged(self):
        self.cfgdata.live2dmodeldefpath = self.l2dmodeldefpath.text()

    def closeEvent(self, event):
        self.cfgdata.saveSettings()
        super().closeEvent(event)


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

# LLM
class LLMWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.current_model = ""

        self.load_config()
        self.init_ui()
        self.restore_current_model()

    def load_config(self):
        os.makedirs("cfg", exist_ok=True)
        self.config.read("cfg/LLMconfig.ini")


    def init_ui(self):
        main_layout = QVBoxLayout()

        # 模型选择
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.update_model_combo()
        self.model_combo.currentTextChanged.connect(self.update_default_model)
        model_layout.addWidget(QLabel("默认模型:"))
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("Tool_button")
        save_btn.clicked.connect(self.save_all)
        btn_layout.addWidget(save_btn)
        model_layout.addLayout(btn_layout)

        main_layout.addLayout(model_layout)
        # 参数区域
        self.params_scroll_area = QScrollArea()
        self.params_scroll_area.setWidgetResizable(True)
        self.params_container = QWidget()
        self.params_container.setObjectName("chat_scroll")
        self.params_layout = QVBoxLayout()
        self.params_container.setLayout(self.params_layout)
        self.params_scroll_area.setWidget(self.params_container)
        main_layout.addWidget(self.params_scroll_area)

        self.setLayout(main_layout)

    def update_model_combo(self):
        self.model_combo.clear()
        models = [s for s in self.config.sections() if s != "app"]
        self.model_combo.addItems(models)

    def restore_current_model(self):
        if "app" in self.config and "llm" in self.config["app"]:
            current = self.config["app"]["llm"]
            index = self.model_combo.findText(current)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
        self.load_all_params()    

    def load_all_params(self):
        # 清空现有参数组
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.param_widgets = {}

        for model in self.config.sections():
            if model == "app":
                continue

            group_box = QGroupBox(model)
            form_layout = QFormLayout()
            self.param_widgets[model] = {}

            for key in self.config[model]:
                value = self.config[model][key]
                line_edit = QLineEdit(value)
                self.param_widgets[model][key] = line_edit
                form_layout.addRow(QLabel(key), line_edit)

            group_box.setLayout(form_layout)
            self.params_layout.addWidget(group_box)

        self.params_layout.update()
        self.params_container.update()
        self.update()

    def update_default_model(self, new_model):
        self.config["app"] = {"llm": new_model}

    def save_all(self):
        for model, params in self.param_widgets.items():
            if model not in self.config:
                self.config[model] = {}
            for key, line_edit in params.items():
                self.config[model][key] = line_edit.text()

        self.save_to_file()    

    def save_to_file(self):
        self.config["app"] = {"llm": self.model_combo.currentText()}
        with open("cfg/LLMconfig.ini", "w") as f:
            self.config.write(f)
        self.show_notification("所有模型配置已保存成功。")    

    def show_notification(self, message):
        QMessageBox.information(self,"LLM Option", message,QMessageBox.NoButton)


    def getcurLLM(self):
        model = self.model_combo.currentText()
        if model not in self.param_widgets:
            return {'provider': model}

        params = {'provider': model}
        for key, widget in self.param_widgets[model].items():
            if isinstance(widget, QLineEdit):
                params[key] = widget.text()

        return params

# 人格
class PromptOptionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset_options = {}
        self.original_name = None
        self.presets_file = "./cfg/presets.json"
        self.init_ui()
        self.load_presets()
        self.update_list()
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        # 左侧容器
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self.on_item_selected)

        # 按钮
        self.add_btn = QPushButton("添加")
        self.delete_btn = QPushButton("删除")
        save_btn = QPushButton("保存")
        self.add_btn.setObjectName("Tool_button")
        self.delete_btn.setObjectName("Tool_button")
        save_btn.setObjectName("Tool_button")

        # 连接信号
        self.add_btn.clicked.connect(self.add_preset)
        self.delete_btn.clicked.connect(self.delete_preset)
        save_btn.clicked.connect(self.save_current)

        # 布局
        left_layout.addWidget(self.list_widget)

        leftbtn_layout = QHBoxLayout()
        leftbtn_layout.addWidget(self.add_btn)
        leftbtn_layout.addWidget(self.delete_btn)
        leftbtn_layout.addWidget(save_btn)
        left_layout.addLayout(leftbtn_layout)
        # left_layout.addStretch()  # 弹簧，使按钮固定在底部

        layout.addWidget(left_container, 1)

        # 右侧编辑区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 名称编辑框
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入人设名称")
        right_layout.addWidget(self.name_edit)

        # 详情编辑框
        self.detail_edit = QTextEdit()
        self.detail_edit.setObjectName("inputbox")
        self.detail_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.detail_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.detail_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.detail_edit.setAcceptRichText(False)
        right_layout.addWidget(self.detail_edit)

        layout.addWidget(right_widget, 2)
        self.setLayout(layout)

    def load_presets(self):
        """从文件加载预设数据"""
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    self.preset_options = json.load(f)
            else:
                self.preset_options = {}
        except (json.JSONDecodeError, FileNotFoundError):
            self.preset_options = {}

    def save_presets(self):
        """将当前数据保存到文件"""
        with open(self.presets_file, 'w', encoding='utf-8') as f:
            json.dump(self.preset_options, f, ensure_ascii=False, indent=4)

    def update_list(self):
        """更新左侧列表内容"""
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for name in self.preset_options:
            self.list_widget.addItem(name)
        self.list_widget.blockSignals(False)

    def on_item_selected(self, current, previous):
        """处理列表项切换事件"""
        # if previous is not None:
        #     self.save_current()
        if current:
            self.original_name = current.text()
            self.name_edit.setText(current.text())
            self.detail_edit.setText(self.preset_options.get(self.original_name, ""))
        else:
            self.original_name = None
            self.name_edit.clear()
            self.detail_edit.clear()

    def save_current(self):
        """保存当前编辑的人设数据"""
        name = self.name_edit.text().strip()
        detail = self.detail_edit.toPlainText()
        if not name:
            return

        # 处理名称变更
        if self.original_name and self.original_name in self.preset_options:
            if self.original_name != name:
                del self.preset_options[self.original_name]

        # 更新数据
        self.preset_options[name] = detail
        self.original_name = name

        # 更新界面
        self.update_list()
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == name:
                self.list_widget.setCurrentRow(i)
                break
        # 保存到文件
        self.save_presets()

    def add_preset(self):
        """添加一个新的预设角色"""
        base_name = "人设名称"
        count = 0
        name = base_name
        while name in self.preset_options:
            count += 1
            name = f"{base_name}_{count}"

        # 添加新条目
        self.preset_options[name] = ""
        self.save_presets()
        self.update_list()

        # 选中并聚焦新条目
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == name:
                self.list_widget.setCurrentRow(i)
                self.name_edit.setText(name)
                self.detail_edit.clear()
                self.original_name = name
                break
           

    def delete_preset(self):
        """删除当前选中的预设角色"""
        current_item = self.list_widget.currentItem()
        if not current_item:
            return

        name = current_item.text()
        if name == "Doro":
            QMessageBox.information(self,"提示", "/(ㄒoㄒ)/~~不许你删掉Doro啊,混蛋！",QMessageBox.NoButton)
            return
        if name in self.preset_options:
            del self.preset_options[name]
            self.save_presets()
            self.update_list()

            # 清空右侧编辑区
            self.name_edit.clear()
            self.detail_edit.clear()
            self.original_name = None



class Live2DOptWidget(QWidget):
    signal_apply_model = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        # self.canvas.LoadnewModelPath(r"./bai/白-免费版.model3.json")

    def init_ui(self):
        # 创建左侧的 Live2DCanvas
        self.canvas = Live2DCanvas(False, "")
        self.canvas.signal_Live2Dinited.connect(self.init_exp)
        
        # 文件选择区域组件
        self.file_label = QLabel("模型路径:")
        self.file_path_edit = QLineEdit()
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.setObjectName("Tool_button")

        # 动作表情调试区域组件
        self.action_label = QLabel("动作:")
        self.action_combo = QComboBox()
        self.play_btn = QPushButton("播放")
        self.play_btn.setObjectName("Tool_button")

        self.exp_label = QLabel("表情:")
        self.exp_combo = QComboBox()
        self.play_btn2 = QPushButton("播放")
        self.play_btn2.setObjectName("Tool_button")
        # 应用按钮
        self.restart_btn = QPushButton("重置")
        self.apply_btn = QPushButton("应用")
        self.restart_btn.setObjectName("Tool_button")
        self.apply_btn.setObjectName("Tool_button")

        self.setup_layout()
        self.setup_connections()

    def setup_layout(self):
        # 文件选择行
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_btn)

        # 动作调试行
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.action_label)
        action_layout.addWidget(self.action_combo)
        action_layout.addWidget(self.play_btn)

        # 表情调试行
        exp_layout = QHBoxLayout()
        exp_layout.addWidget(self.exp_label)
        exp_layout.addWidget(self.exp_combo)
        exp_layout.addWidget(self.play_btn2)

        # 控制
        Ctrl_layout = QHBoxLayout()
        Ctrl_layout.addWidget(self.restart_btn)
        Ctrl_layout.addWidget(self.apply_btn)

        # 右侧面板布局
        right_layout = QVBoxLayout()
        right_layout.addLayout(file_layout)
        right_layout.addLayout(action_layout)
        right_layout.addLayout(exp_layout)
        right_layout.addLayout(Ctrl_layout)
        right_layout.addStretch(1)  # 保持控件紧凑

        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.canvas, stretch=3)  # 左侧占3份
        main_layout.addLayout(right_layout, stretch=2)  # 右侧占1份
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

    def setup_connections(self):
        """连接信号与槽"""
        self.browse_btn.clicked.connect(self.select_model_file)
        self.play_btn2.clicked.connect(self.apply_expression)
        self.play_btn.clicked.connect(self.play_action)
        self.apply_btn.clicked.connect(self.apply_model)
        self.restart_btn.clicked.connect(self.restart_model)

    def select_model_file(self):
        """文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", "", "Model Files (*.model3.json)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            if not self.canvas.Inited:
                self.canvas.myinit()
            # 加载模型
            self.canvas.LoadnewModelPath(file_path)

            
            # self.init_exp()

    def apply_expression(self):
        """应用动作/表情"""
        expression = self.exp_combo.currentText()
        if expression:
            self.canvas.model.SetExpression(expression)

    def play_action(self):
        """播放选中动作"""
        action = self.action_combo.currentText()
        if action:
            print(f"Playing action: {action}")
            # 这里添加播放动作的逻辑
            self.canvas.model.Update()
            self.canvas.model.StartMotion(action,0,1)

    def init_exp(self):
        self.exp_combo.clear()
        expressions = self.canvas.model.GetExpressionIds()
        for text in expressions:
            print(f"加载表情： {text}")
            self.exp_combo.addItem(text)
        self.action_combo.clear()
        motions = self.canvas.model.GetMotionGroups()
        for text in motions:
            print(f"加载动作：{text}")
            self.action_combo.addItem(text)

    def apply_model(self):
        path = self.canvas.modelpath
        self.signal_apply_model.emit(path)
        return
    
    def restart_model(self):
        self.canvas.LoadnewModelPath()
        self.init_exp()


class AboutAuthorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("关于作者")
        self.resize(400, 300)
        self.initUI()
    
    def initUI(self):
        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 介绍文本
        info_text = """<h2>作者信息</h2>
        <p>水脚脚</p>
        <p>WaterFeet</p>
        <p></p>
        <p>联系方式：<a href="417771692@qq.com">417771692@qq.com</a></p>"""
        
        label = QLabel(info_text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setOpenExternalLinks(False)  # 禁止自动打开外部链接
        
        # GitHub按钮
        github_btn = QPushButton()
        github_btn.setFixedSize(100,100)
        github_btn.setObjectName("githubbtn")
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://github.com/waterfeet")
        ))
        
        # 将元素添加到布局
        layout.addWidget(label, alignment=Qt.AlignCenter)
        layout.addWidget(github_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    #window = OptionWidget()
    window = GeneralOptWidget()
    window.show()
    sys.exit(app.exec_())

