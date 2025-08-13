from src.DoroPetApp import DesktopPet
from src.MainWindow import myFont
from src.live.Danmu import start_getdanmu
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
import sys

def main():
    app = QApplication(sys.argv)
    font = QFont(myFont().getFont(), 13)
    app.setFont(font)

    print("初始化界面")
    pet = DesktopPet()
    print("初始化完成")

    # 启动线程
    start_getdanmu()

    pet.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

