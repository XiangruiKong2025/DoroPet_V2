#weather_wallpaper.py
 
import sys
# from src.DoroPetApp import DesktopPet
# from src.MainWindow import myFont
 
import win32.win32gui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from .GeneralOptData import get_GeneralOptData

import time
import pythoncom  # 必须导入以初始化 COM 环境
class foreground_fullscreenThread(QThread):
    foreground_fullscreen_changed = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        self.previous_state = None  # 记录上一次检测的状态
        self.running = True  # 控制线程运行的标志

    
    def run(self):
        pythoncom.CoInitialize()  # ✅ 初始化 COM 库（必须！）
        while self.running:  # 持续监控的循环
            try:
                current_state = is_any_window_fullscreen()  # 获取当前状态
                
                # 仅当状态变化时才发送信号
                if current_state != self.previous_state:
                    self.foreground_fullscreen_changed.emit(current_state)
                    self.previous_state = current_state  # 更新记录的状态
                    # print(f"状态变化: {current_state}")
                
                time.sleep(0.2)  # 降低CPU占用（单位：秒，按需调整）
            
            except Exception as e:
                # print(f"线程错误: {str(e)}")
                pythoncom.CoInitialize()  # ✅ 初始化 COM 库（必须！）
                # self.stop()
                self.start()
            finally:
                pythoncom.CoUninitialize()  # ✅ 清理 COM 资源
    
    def stop(self):  # 安全停止线程的方法
        self.running = False
        self.wait()  # 等待线程结束


def getWindowHandle():
    hwnd = win32.win32gui.FindWindow("Progman", "Program Manager")
    win32.win32gui.SendMessageTimeout(hwnd, 0x052C, 0, None, 0, 0x03E8)
    hwnd_WorkW = None
    while 1:
        hwnd_WorkW = win32.win32gui.FindWindowEx(None, hwnd_WorkW, "WorkerW", None)
        # print('hwmd_workw: ', hwnd_WorkW)
        if not hwnd_WorkW:
            continue
        hView = win32.win32gui.FindWindowEx(hwnd_WorkW, None, "SHELLDLL_DefView", None)
        # print('hwmd_hView: ', hView)
        if not hView:
            continue
        h = win32.win32gui.FindWindowEx(None, hwnd_WorkW, "WorkerW", None)
        # print('h_1: ',h)
        while h:
            win32.win32gui.SendMessage(h, 0x0010, 0, 0)  # WM_CLOSE
            h = win32.win32gui.FindWindowEx(None, hwnd_WorkW, "WorkerW", None)
            # print(h)
        break
    return hwnd


import win32gui
import win32con
from ctypes import windll


def is_window_fullscreen(hwnd):
    # 排除系统桌面窗口（如壁纸）
    class_name = win32gui.GetClassName(hwnd)
    if class_name in ["Progman", "WorkerW","Windows.UI.Core.CoreWindow"]:
        return False

    try:
        # 获取窗口矩形 (left, top, right, bottom)
        win_rect = win32gui.GetWindowRect(hwnd)
        win_width = win_rect[2] - win_rect[0]
        win_height = win_rect[3] - win_rect[1]

        # 获取真实屏幕分辨率（考虑 DPI 缩放）
        user32 = windll.user32
        gdi32 = windll.gdi32
        hdc = user32.GetDC(None)
        screen_width = gdi32.GetDeviceCaps(hdc, win32con.DESKTOPHORZRES)
        screen_height = gdi32.GetDeviceCaps(hdc, win32con.DESKTOPVERTRES)
        user32.ReleaseDC(None, hdc)

        TOLERANCE = 30

        # 获取窗口样式
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

        # 判断是否“真全屏”：窗口尺寸几乎等于屏幕大小，且贴边
        is_true_fullscreen = (
            abs(win_width - screen_width) <= TOLERANCE and
            abs(win_height - screen_height) <= TOLERANCE and
            win_rect[0] <= TOLERANCE and
            win_rect[1] <= TOLERANCE
        )

        # 判断是否“伪全屏”：窗口贴边 + 横向铺满 + 高度占大部分，且没有标题栏/边框
        is_pseudo_fullscreen = (
            win_rect[0] <= TOLERANCE and
            win_rect[1] <= TOLERANCE and
            abs(win_width - screen_width) <= TOLERANCE and
            win_height >= screen_height * 0.95 and
            not (style & win32con.WS_CAPTION)  # 无标题栏（常见于游戏/播放器）
        )

        return is_true_fullscreen or is_pseudo_fullscreen

    except Exception as e:
        print(f"Error checking window: {e}")
        return False


def is_any_window_fullscreen():
    full_screen_found = [False]  # 使用列表来在回调中修改值

    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):  # 只处理可见窗口
            if is_window_fullscreen(hwnd):
                full_screen_found[0] = True
                return False  # 停止枚举
        return True

    win32gui.EnumWindows(enum_callback, None)

    return full_screen_found[0]


################################################################################################################################################################################################### 
def is_windows_24H2():
    """检测是否为 Windows 24H2（Build >= 26000）"""
    ver = sys.getwindowsversion()
    return ver.build >= 26000

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

class WallpaperWindow(QMainWindow):
    def __init__(self, parent=None):
        super(WallpaperWindow, self).__init__(parent)
        self.cfgData = get_GeneralOptData()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.gif_label = QLabel(self)
        self.gif_label.hide()
         # 创建视频显示部件
        self.video_widget = QVideoWidget(self)
        self.video_widget.hide()
        # 创建媒体播放器
        self.media_player = QMediaPlayer(self)

        getWindowHandle()
        win_hwnd = int(self.winId())
        h = win32.win32gui.FindWindow(("Progman"), ("Program Manager"))
        win32.win32gui.SetParent(win_hwnd, h)
        self.showFullScreen()
        self.imgh = 0
        self.mode = 0
        self.allowmouse = True
        self.is_foreground_fullscreen = False
        self.ffthread =  foreground_fullscreenThread()
        self.ffthread.foreground_fullscreen_changed.connect(self.updateFf)
        self.ffthread.start()

    
    def updateFf(self, isFf):
        # 焦点窗口全屏
        print(f"桌面是否被遮盖{isFf}")
        if isFf: 
            if self.cfgData.wallpaperType == 1:
                 if hasattr(self, 'media_player') and self.media_player is not None:
                    try:
                        self.media_player.mediaStatusChanged.disconnect(self.handle_media_status)
                    except TypeError:
                        # 如果从未连接过，忽略异常
                        pass
                    self.media_player.pause()
            if self.cfgData.wallpaperType == 2:
                self.allowmouse = False
        else:
            if self.cfgData.wallpaperType == 1:
                # self.startVideo(self.cfgData.wallpaperPath_V)
                 if hasattr(self, 'media_player') and self.media_player is not None:
                    try:
                        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
                    except TypeError:
                        # 如果从未连接过，忽略异常
                        pass
                    self.media_player.play()
            if self.cfgData.wallpaperType == 2:
                self.allowmouse = True



    def startVideo(self, path):
        if self.cfgData.wallpaperType == 2:
            self.gif_label.close()
        # 1. 如果已有播放器存在，先清理
        if hasattr(self, 'media_player') and self.media_player is not None:
            try:
                self.media_player.mediaStatusChanged.disconnect(self.handle_media_status)
            except TypeError:
                # 如果从未连接过，忽略异常
                pass
            self.media_player.stop()
        import os
        if not os.path.exists(path):
            return

        self.cfgData.wallpaperType =1

        screen = QDesktopWidget().screenGeometry()
        desktop_size = screen.size()
        self.resize(desktop_size)
        
        # 2. 创建新的视频部件和播放器
        self.video_widget = QVideoWidget(self)
        self.media_player = QMediaPlayer(self)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.media_player.setVideoOutput(self.video_widget)

        self.setCentralWidget(self.video_widget)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        # self.media_player.stateChanged.connect(self.handle_state_changed)
        self.media_player.error.connect(self.handle_media_error)

        self.cfgData.wallpaperPath_V = path
        self.media_player.play()
        self.move(0, 0)

    def handle_media_error(error, error_no):
        print(f"发生错误: {error} - {error_no}")
        
        if error_no == QMediaPlayer.FormatError:
            print("不支持的视频格式，请安装合适的解码器")
        elif error_no == QMediaPlayer.ResourceError:
            print("资源加载失败，请检查文件是否存在或路径是否正确")
        elif error_no == QMediaPlayer.NetworkError:
            print("网络错误，请检查网络连接")
        elif error_no == QMediaPlayer.AccessDeniedError:
            print("没有权限访问该资源")
        elif error_no == QMediaPlayer.ServiceMissingError:
            print("缺少必要的多媒体服务，请安装相关组件")
        else:
            print("未知错误")
        # self.deleteAll()

    def handle_media_status(self, status):

        if status == QMediaPlayer.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()

    def startImg(self, path, mode):
        self.mode = mode
        if self.cfgData.wallpaperType == 1:
            if hasattr(self, 'media_player') and self.media_player is not None:
                try:
                    self.media_player.mediaStatusChanged.disconnect(self.handle_media_status)
                except TypeError:
                    # 如果从未连接过，忽略异常
                    pass
                self.media_player.stop()
        import os
        if not os.path.exists(path):
            return

        self.cfgData.wallpaperType = 2
        self.gif_label.close()
        self.gif_label = QLabel(self)
        self.setCentralWidget(self.gif_label)
        screen = QDesktopWidget().screenGeometry()
        desktop_size = screen.size()
        self.gif_label.setGeometry(0,0,int(desktop_size.width()),int(desktop_size.height()))
        # 加载并缩放图片
        pixmap = QPixmap(path)
        self.cfgData.wallpaperPath_P = path
        self.move(0, 0)

        RatioMode = Qt.IgnoreAspectRatio
        if mode == 1:
            RatioMode = Qt.KeepAspectRatio
        if mode == 2:
            RatioMode = Qt.KeepAspectRatioByExpanding

        scaled_pixmap = pixmap.scaled(desktop_size, RatioMode, Qt.SmoothTransformation)

        self.imgh = scaled_pixmap.height()
        self.gif_label.setPixmap(scaled_pixmap)
        self.gif_label.setScaledContents(True)  # 自动缩放内容（可选）
        

    def updateMouse(self,x,y):

        if not self.mode == 2:
            return
        screen = QDesktopWidget().screenGeometry()
        desktop_size = screen.size()
 
        if self.imgh > desktop_size.height() and self.cfgData.wallpaperType == 2 and self.allowmouse:
            rate = y/desktop_size.height()
            rate = max(rate,0)
            rate = min(rate,1)

            yy =(self.imgh - desktop_size.height())*rate

            self.move(0, int(-yy))
        
    def deleteAll(self):
        self.cfgData.wallpaperType = 0
        self.gif_label.close()
        self.gif_label = QLabel(self)

        if hasattr(self, 'media_player') and self.media_player is not None:
            try:
                self.media_player.mediaStatusChanged.disconnect(self.handle_media_status)
            except TypeError:
                # 如果从未连接过，忽略异常
                pass
            self.media_player.stop()


WallpaperWindow_instance = None

def get_WallpaperWindow():
    global WallpaperWindow_instance
    if WallpaperWindow_instance is None:
        WallpaperWindow_instance = WallpaperWindow()
    return WallpaperWindow_instance
       
 
# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     myWin = WallpaperWindow()

#     myWin.startImg ('f:/stable diffusion/stable-diffusion-webui/outputs/txt2img-images/2025-07-01/00037-1188630020.png', 2)

#     sys.exit(app.exec_())
 
 
 