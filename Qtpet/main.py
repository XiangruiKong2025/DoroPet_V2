from src.DoroPetApp import DesktopPet
from src.MainWindow import myFont
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont(myFont().getFont(), 13)
    app.setFont(font)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())