from PyQt5.QtCore import *


GeneralOptData_instance = None
def get_GeneralOptData():
    global GeneralOptData_instance
    if GeneralOptData_instance is None:
        GeneralOptData_instance = GeneralOptData()
    return GeneralOptData_instance

class GeneralOptData(QObject):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("cfg/app.cfg", QSettings.IniFormat)
        self.window_Size = "800x600"
        self.alpha = 90
        self.FrontProcess = False
        self.live2dLWa = 1.0
        self.wallpaperType = 0
        self.wallpaperPath_V = ""
        self.wallpaperPath_P = ""
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
        # 模型长宽比
        self.live2dLWa = float(self.settings.value("live2dLWa", 1.0))
        # 人格市场地址
        self.promptmarketurl = self.settings.value("PromptMarketUrl", "https://www.jasongjz.top/")
        #  壁纸类型
        self.wallpaperType = int(self.settings.value("wallpaperType", 0))
        #  壁纸路径
        self.wallpaperPath_V = self.settings.value("wallpaperPath_V", "")
        self.wallpaperPath_P = self.settings.value("wallpaperPath_P", "")

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
        # 模型长宽比
        self.settings.setValue("live2dLWa", self.live2dLWa)
        #  壁纸类型
        self.settings.setValue("wallpaperType", self.wallpaperType)
        #  壁纸路径
        self.settings.setValue("wallpaperPath_V", self.wallpaperPath_V)
        self.settings.setValue("wallpaperPath_P", self.wallpaperPath_P)

        self.settings.endGroup()