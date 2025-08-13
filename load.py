from sys import argv, exit
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QMovie, QFont, QFontDatabase
from PyQt5.QtCore import Qt, AlignHCenter

# loading_animation.py

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

class LoadingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QLabel(self)
        self.movie = QMovie("data/img/load.gif")  # 替换为你自己的 GIF 文件
        self.label.setMovie(self.movie)
        layout.addWidget(self.label)

        self.label2 = QLabel("Loading...")
        self.label2.setEnabled(False)
        self.label2.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self.label2)
        self.setLayout(layout)


        self.movie.start()

    def closeEvent(self, event):
        self.movie.stop()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(argv)
    font = QFont(myFont().getFont(), 20)
    app.setFont(font)
    window = LoadingWindow()
    window.setFixedSize(360, 382)
    window.show()
    exit(app.exec_())