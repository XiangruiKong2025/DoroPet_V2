from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QLabel


class TcpListenThread(QThread):
    """后台线程：阻塞监听端口，收到数据后 emit 文本。"""
    text_received = pyqtSignal(str)          # 给主线程的信号

    def __init__(self, host='127.0.0.1', port=12345):
        super().__init__()
        self.addr = (host, port)
        self.running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(self.addr)
        sock.listen(5)
        sock.settimeout(1)          # 让线程能定期自检 running 标志
        while self.running:
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            conn.settimeout(None)
            while self.running:
                data = conn.recv(1024)
                if not data:        # 对端关闭
                    break
                text = data.decode('utf-8', errors='ignore')
                self.text_received.emit(text)
            conn.close()
        sock.close()

    def stop(self):
        self.running = False
        self.wait()

import socket

def send_to_port(data: str,
                   remote_host='127.0.0.1',
                   remote_port=12345,
                   local_port=None,
                   encoding='utf-8'):
    """
    从指定本地端口发送 TCP 数据。
    local_port=None 时由系统随机分配。
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if local_port is not None:                   # ★ 指定本地端口
            sock.bind(('', local_port))
        sock.connect((remote_host, remote_port))
        sock.sendall(data.encode(encoding))
        return True
    except Exception as e:
        print('发送失败:', e)
        return False
    finally:
        sock.close()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("端口监听示例")
        self.resize(400, 300)

        self.label = QLabel("监听 127.0.0.1:12345")
        self.edit = QTextEdit(readOnly=True)

        lay = QVBoxLayout(self)
        lay.addWidget(self.label)
        lay.addWidget(self.edit)

        # 启动后台线程
        self.thread = TcpListenThread()
        self.thread.text_received.connect(self.append_text)
        self.thread.start()

    def append_text(self, txt):
        self.edit.append(txt.rstrip())

    def closeEvent(self, evt):
        self.thread.stop()
        evt.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())