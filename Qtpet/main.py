from src.DoroPetApp import DesktopPet
from src.MainWindow import myFont
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
# import subprocess
# import asyncio

# def start_loading_animation():
#     # 启动加载动画程序
#     loading_exe_path = "data/DoroLoad.exe" 
#     return subprocess.Popen([loading_exe_path])

def main():
    app = QApplication(sys.argv)
    font = QFont(myFont().getFont(), 13)
    app.setFont(font)

    # 启动加载动画
    # loading_process = start_loading_animation()

    print("初始化界面")
    pet = DesktopPet()
    print("初始化完成")


    # 关闭加载动画程序（包含子进程）
    # os.system(f'taskkill /f /pid {loading_process.pid} /t')

    pet.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    
