import live2d.v3 as live2d
from PyQt5.QtCore import Qt,pyqtSignal, QTimer
from PyQt5.QtWidgets import QOpenGLWidget
import math
# import faulthandler
# faulthandler.enable()

class Live2DCanvas(QOpenGLWidget):
    signal_Live2Dinited = pyqtSignal()
    def __init__(self, bnobackground = True, modelPath = ""):
        super().__init__()
        self.Inited = False
        self.nobackground = bnobackground
        self.setMinimumSize(120,112)
        
        self.myinit()
        
        self.modelpath = r"models/Doro/Doro.model3.json"
        if modelPath.endswith("model3.json"):
            self.modelpath = modelPath

        

    def myinit(self):
        live2d.init()
        live2d.setLogEnable(True)
        self.model: None | live2d.LAppModel = None

    def LoadnewModelPath(self, sPath = ""):
        if sPath != "":
            self.modelpath = sPath
        
        self.model.StopAllMotions()
        self.model.LoadModelJson(self.modelpath)
        print("live2d加载完成")

        tmp_timer = QTimer()
        tmp_timer.singleShot(1000, self.signal_Live2Dinited.emit)
        self.Inited = True

    def initializeGL(self):
        live2d.glInit()
        
        # 加载模型
        self.model = live2d.LAppModel()
        if live2d.LIVE2D_VERSION == 3:
            self.LoadnewModelPath()
            # self.model.LoadModelJson(r"Doro/Doro.model3.json")
            self.model.SetAutoBlinkEnable(True) # 自动眨眼
            self.model.SetAutoBreathEnable(True)

        # print("live2d加载完成")

        # tmp_timer = QTimer()
        # tmp_timer.singleShot(1000, self.signal_Live2Dinited.emit)
        # self.Inited = True

        
        self.startTimer(int(15))

    def paintGL(self):
        # 更新模型状态
        self.model.Update()
        self.on_draw()
        # self.canvas.Draw(self.on_draw)

    def on_draw(self):
        # 清除帧缓冲区为透明
        if self.nobackground:
            live2d.clearBuffer(0.0, 0.0, 0.0, 0.0)
        else:
            live2d.clearBuffer(0.0, 0.0, 0.0, 1)
        # 绘制模型
        self.model.Draw()
    
    def timerEvent(self, a0):
        self.update()


    def resizeGL(self, width: int, height: int):
        self.model.Resize(width, height)
        self.setFixedSize(width, height)
        # print(f"resizeGL:{width},{height}")


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
        self.model.SetParameterValue("ParamAngleX", nParamAngleX)
        self.model.SetParameterValue("ParamAngleY", nParamAngleY)
        
        # self.model.SetParameterValue("ParamEyeBallX", nParamAngleX/30)
        # self.model.SetParameterValue("ParamEyeBallY", nParamAngleY/30)



    # def mouseMoveEvent(self, event: QMouseEvent):
    #     print(f"mouseMoveEvent: {event.globalPos()}")
    #     super().mouseMoveEvent(event)  # 可选：根据需要调用父类处理

# class mainwidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setMinimumSize(800,600)
#         self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
#         self.setAutoFillBackground(False)
        
#         vlayout = QVBoxLayout(self)
#         hlayout = QHBoxLayout()
#         self.Live2D = Live2DCanvas()
#         vlayout.addWidget(self.Live2D)
#         vlayout.addLayout(hlayout)
#         testbtn = QPushButton("test")
#         hlayout.addWidget(testbtn)

#         testbtn.clicked.connect(self.ontest)

#     def ontest(self):
#         # self.Live2D.model.SetRandomExpression()
#         # self.Live2D.model.SetRandomExpression()
#         self.Live2D.model.StartMotion("Idle",0,1)
#         # self.Live2D.model.StartRandomMotion()
        


# if __name__ == '__main__':
#     from PyQt5.QtWidgets import QApplication
#     live2d.init()
#     app = QApplication(sys.argv)
#     win = mainwidget()
#     win.show()
#     app.exec()
#     live2d.dispose()