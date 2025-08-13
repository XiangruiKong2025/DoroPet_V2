from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QOpenGLWidget
from live2d.v3 import init, setLogEnable, LAppModel, LIVE2D_VERSION, glInit, clearBuffer
from live2d.utils.canvas import Canvas
import math


class Live2DCanvas(QOpenGLWidget):
    signal_Live2Dinited = pyqtSignal()
    def __init__(self, bnobackground = True, modelPath = ""):
        super().__init__()
        self.Inited = False
        self.nleftorright = 1
        self.nobackground = bnobackground # 背景透明（普通情况）
        self.click_through = False  # 控制是否允许点击穿透
        self.issnap = 0  # 边缘吸附中（鼠标悬浮时）(1234:左右上下)

        self.sys_state = "" # 系统cpu内存占用文本，由外部直接提供
        self.sys_en = False # 是否显示系统状态

        self.setMinimumSize(120,120)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.myinit()
        
        self.modelpath = r"models/Doro/Doro.model3.json"
        if modelPath.endswith("model3.json"):
            self.modelpath = modelPath



    def myinit(self):
        init()
        setLogEnable(True)
        
        self.model: None | LAppModel = None
        self.canvas: None | Canvas = None

    def LoadnewModelPath(self, sPath = ""):
        if sPath != "":
            self.modelpath = sPath
        
        self.model.StopAllMotions()
        self.model.LoadModelJson(self.modelpath)
        print("live2d加载完成" )

        tmp_timer = QTimer()
        tmp_timer.singleShot(1000, self.signal_Live2Dinited.emit)
        self.Inited = True

    def initializeGL(self):
        glInit()
        
        # 加载模型
        self.model = LAppModel()
        if LIVE2D_VERSION == 3:
            self.LoadnewModelPath()
            self.model.SetAutoBlinkEnable(True) # 自动眨眼
            self.model.SetAutoBreathEnable(True)
        self.canvas = Canvas()
        self.startTimer(int(15))  # 毫秒

    def paintGL(self):
        # 更新模型状态
        self.model.Update()
        # self.on_draw()
        # 这里清除的是窗口的背景
        if self.nobackground:
            if (self.underMouse() and self.issnap==0):
                # 鼠标正在该 QOpenGLWidget 上
                clearBuffer(0.0, 0.0, 0.0, 0.1)
            else:
                # 鼠标不在该 QOpenGLWidget 上
                clearBuffer(0.0, 0.0, 0.0, 0.0)
        else:
            clearBuffer(0.0, 0.0, 0.0, 1)
        # 清除帧缓冲区为透明
        self.canvas.Draw(self.on_draw)
        if self.sys_en:
            self.paintState()

    def on_draw(self):
        # canvas中要清空背景
        clearBuffer() 
        # 绘制模型
        self.model.Draw()
        
    
    def timerEvent(self, a0):
        self.update()


    def SetModelScaleX(self, sx):
        if self.model is None:
            return
        self.nleftorright = sx
        self.model.SetScaleX(sx)

    def resizeGL(self, width: int, height: int):
        
        self.setFixedSize(width, height)
        self.model.Resize(width, height)
        self.canvas.SetSize(width, height)



    def getMotions(self):
        motions = self.model.IsMotionFinished()
        print(motions)

    def MouseTrack(self,x,y):

        pos = self.parentWidget().pos()     # 在屏幕中的位置
        geo = self.frameGeometry()          
        center_x = pos.x() + geo.width() / 2
        center_y = pos.y() + geo.height() / 2

        # print(f"{x - center_x},   {geo.width()},   {(x - center_x)/geo.width()}")

        nParamAngleX = math.degrees(math.atan((x - center_x)/geo.width()))
        nParamAngleY = -math.degrees(math.atan((y - center_y)/geo.height()))

        nParamAngleX = max(-30, min(nParamAngleX, 30))
        nParamAngleY = max(-30, min(nParamAngleY, 30))

        # print(f"{nParamAngleX},{nParamAngleY}")
        nParamAngleX *= self.nleftorright

        self.model.SetParameterValue("ParamAngleX", nParamAngleX)
        self.model.SetParameterValue("ParamAngleY", nParamAngleY)
        
        # self.model.SetParameterValue("ParamEyeBallX", nParamAngleX/30)
        # self.model.SetParameterValue("ParamEyeBallY", nParamAngleY/30)

    def mousePressEvent(self, event):
        if self.click_through:
            event.ignore()  # 忽略事件，让其传递下去
        else:
            super(Live2DCanvas, self).mousePressEvent(event)

    def set_click_through(self, enabled):
        self.click_through = enabled

    def set_Opacity(self, opacity):
        self.canvas.SetOutputOpacity(opacity)
        # cnt = self.model.GetPartCount()
        # for i in range(0, cnt):
        #     self.model.SetPartOpacity(i, opacity)
    
    # def paintState(self):
    #     # ✅ 叠加绘制 CPU 占用文字
    #     fontsize = max(int(self.width()/20), 10)
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.Antialiasing)
    #     painter.setPen(QColor(255, 255, 255))
    #     painter.setFont(QFont("Consolas", fontsize))

    #     painter.drawText(fontsize, fontsize * 2, self.sys_state)
    #     painter.end()

    def paintState(self):
        fontsize = max(int(self.width()/20), 10)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算文字所在矩形的几何信息（这里简单估计，实际可按需要精确计算）
        text = self.sys_state
        fm = QFontMetrics(QFont("Consolas", fontsize))
        text_w = fm.horizontalAdvance(text)
        text_h = fm.height()

        # 背景矩形起点、宽高（留出一点内边距）
        padding = 4
        rect_x = fontsize - padding
        rect_y = fontsize * 2 - text_h + padding
        rect_w = text_w + padding * 2
        rect_h = text_h + padding * 2

        # 半透明背景
        painter.setBrush(QColor(0, 0, 0, 78))   # 黑色，128/255 ≈ 50% 透明度
        painter.setPen(Qt.NoPen)                 # 去掉边框
        painter.drawRect(rect_x, rect_y, rect_w, rect_h)

        # 文字
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Consolas", fontsize))
        painter.drawText(fontsize, fontsize * 2, text)

        painter.end()