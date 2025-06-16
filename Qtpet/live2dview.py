import sys

import live2d.v3 as live2d
from PyQt5.QtCore import Qt,pyqtSignal, QTimer
from PyQt5.QtWidgets import QOpenGLWidget


class Live2DCanvas(QOpenGLWidget):
    signal_Live2Dinited = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.Inited = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground | Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAutoFillBackground(False)
        self.setMinimumSize(120,112)
        self.setFixedSize(300,280)
        live2d.init()
        live2d.setLogEnable(True)
        self.model: None | live2d.LAppModel = None
        # self.ModelData : None | live2d.Model = None


    def initializeGL(self):
        live2d.glInit()
        
        # 加载模型
        self.model = live2d.LAppModel()
        if live2d.LIVE2D_VERSION == 3:
            self.model.LoadModelJson(r"Doro_live2d/Doro.model3.json")
            self.model.LoadModelJson("Mao/Mao.model3.json")
            self.model.SetAutoBlinkEnable(True) # 自动眨眼
        print("live2d加载完成")

        tmp_timer = QTimer()
        tmp_timer.singleShot(1000, self.signal_Live2Dinited.emit)
        self.Inited = True

        
        self.startTimer(int(1000 /100))

    def paintGL(self):
        # 更新模型状态
        self.model.Update()
        self.on_draw()
        # self.canvas.Draw(self.on_draw)

    def on_draw(self):
        # 清除帧缓冲区为透明
        live2d.clearBuffer(0.0, 0.0, 0.0, 0.0)
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