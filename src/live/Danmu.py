from requests import post
from time import sleep
from threading import Thread
from collections import deque
from PyQt5.QtCore import QThread
from src.socketthread import send_to_port, TcpListenThread
from src.GeneralOptData import get_GeneralOptData

class Danmu:
    def __init__(self):
        # 弹幕url
        self.url = 'https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory'
        # 请求头
        self.headers = {
            'Host': 'api.live.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
        }

        self.cfg = get_GeneralOptData()


        self.ID = "5499538"

        if self.cfg.Live_RoomID:
            self.ID = self.cfg.Live_RoomID

        # 定义POST传递的参数
        self.data = {
            'roomid': self.ID,
            'csrf_token': '',
            'csrf': '',
            'visit_id': '',
        }
        
        # 使用双端队列存储最近的弹幕记录，限制大小为100
        self.processed_danmu = deque(maxlen=100)
        self.isfirst = True

    def get_danmu(self):
        # 获取直播间弹幕
        html = post(url=self.url, headers=self.headers, data=self.data).json()
        # 解析弹幕列表
        if 'data' in html and 'room' in html['data']:
            for content in html['data']['room']:
                # 获取昵称
                nickname = content['nickname']
                # 获取发言
                text = content['text']
                # 获取发言时间
                timeline = content['timeline']
                # 构造弹幕的唯一标识
                danmu_id = f"{nickname}-{text}-{timeline}"
                # 如果这条弹幕没有被处理过
                if danmu_id not in self.processed_danmu:
                    # 记录这条弹幕
                    self.processed_danmu.append(danmu_id)
                    
                    prefix = str(self.cfg.Live_Danmu_Filter)
                    if self.cfg.Live_Danmu_Filter and str(text).startswith(prefix):
                        text = text[len(prefix):]   # 去掉前缀后的正文

                        # 打印弹幕
                        msg = timeline + ' ' + nickname + ': ' + text
                        print(msg)
                        if self.cfg.TCP_listenport > 0 and not self.isfirst:
                            send_to_port(msg, remote_port=self.cfg.TCP_listenport)
        else:
            print("No data or room information found in the response.")

        self.isfirst = False

def danmu_thread():
    bDanmu = Danmu()
    while True:
        try:
            bDanmu.get_danmu()
        except Exception as e:
            print(f"Error occurred while fetching danmu: {e}")
        sleep(5)  # 每5秒获取一次弹幕

# thread: None | threading.Thread = None
# def start_getdanmu():
#     # 创建线程
#     thread = threading.Thread(target=danmu_thread)
#     # 启动线程
#     thread.start()
#     print("Danmu fetching thread has started.")

class DanmuThread(QThread):
    def run(self):
        bDanmu = Danmu()
        while not self.isInterruptionRequested():
            try:
                bDanmu.get_danmu()
            except Exception as e:
                print(f"Error occurred while fetching danmu: {e}")
            self.msleep(5000)

_thread: QThread | None = None

def start_getdanmu():
    global _thread
    if _thread and _thread.isRunning():
        print("Danmu thread already running.")
        return
    _thread = DanmuThread()
    _thread.finished.connect(_thread.deleteLater)
    _thread.start()
    print("Danmu fetching thread has started.")

def stop_danmu():
    global _thread
    if not _thread or not _thread.isRunning():
        print("No running thread to stop.")
        return
    _thread.requestInterruption()
    _thread.quit()
    _thread.wait()
    _thread = None
    print("Danmu fetching thread has stopped.")