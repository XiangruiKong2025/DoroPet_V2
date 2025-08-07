from PyQt5.QtCore import *
import os
import json

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
        self.TTSEn = False
        self.live2dLWa = 1.0
        self.wallpaperType = 0
        self.wallpaperPath_V = ""
        self.wallpaperPath_P = ""
        self.autoThinkTime = 10  # 
        self.voskEn = False
        self.voskpath = ""

        self.TCP_sendport=""
        self.TCP_listenport=""

        self.Live_RoomID = ""
        self.Live_Danmu_Filter = ""

        self.loadSettings()
        self.thinktext = []
        self.loadthinktext()

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
        self.promptmarketurl = self.settings.value("PromptMarketUrl", "")
        # 表情包地址
        self.Emojiweburl = self.settings.value("Emojiweburl", "")
        #  壁纸类型
        self.wallpaperType = int(self.settings.value("wallpaperType", 0))
        #  壁纸路径
        self.wallpaperPath_V = self.settings.value("wallpaperPath_V", "")
        self.wallpaperPath_P = self.settings.value("wallpaperPath_P", "")
        # 随机行为的间隔
        self.autoThinkTime = int(self.settings.value("autoThinkTime", 10))
        # 语音识别
        self.voskEn =  self.settings.value("voskEn", False, type=bool)
        self.voskpath = self.settings.value("voskpath", "")

        #TTS
        self.TTSEn =  self.settings.value("TTSEn", False, type=bool)

        # tcp
        self.TCP_listenport = int(self.settings.value("TCP_listenport", 0))
        self.TCP_sendport = int(self.settings.value("TCP_sendport", 0))

        # 直播设定  房间号，  
        self.Live_RoomID = self.settings.value("Live_RoomID", "")
        self.Live_Danmu_Filter = self.settings.value("Live_Danmu_Filter", "")

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
        # 表情包地址
        self.settings.setValue("Emojiweburl", self.Emojiweburl)
        # 模型长宽比
        self.settings.setValue("live2dLWa", self.live2dLWa)
        #  壁纸类型
        self.settings.setValue("wallpaperType", self.wallpaperType)
        #  壁纸路径
        self.settings.setValue("wallpaperPath_V", self.wallpaperPath_V)
        self.settings.setValue("wallpaperPath_P", self.wallpaperPath_P)
        # 随机行为的间隔
        self.settings.setValue("autoThinkTime", self.autoThinkTime)
        # 语音识别
        self.settings.setValue("voskEn", self.voskEn)
        self.settings.setValue("voskpath", self.voskpath)

        # TTS
        self.settings.setValue("TTSEn", self.TTSEn)

        self.settings.setValue("TCP_sendport", self.TCP_sendport)
        self.settings.setValue("TCP_listenport", self.TCP_listenport)
        
        self.settings.setValue("Live_RoomID", self.Live_RoomID)
        self.settings.setValue("Live_Danmu_Filter", self.Live_Danmu_Filter)

        self.settings.endGroup()

    def loadthinktext(self):
        file_path = os.path.join(os.getcwd(), 'cfg/thinktext.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            self.thinktext = json.load(f)