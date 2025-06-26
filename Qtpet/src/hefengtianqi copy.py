from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage,QWebEngineSettings
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys

class CustomWebPage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)

    def javaScriptConsoleMessage(self, level, msg, line, source_id):
        # 捕获 JS 控制台输出
        print("JS Console: ", msg)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        # 允许初始加载和手动刷新等操作，只拦截用户点击链接
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            print("Blocked link click to:", url.toString())
            return False  # 阻止点击链接跳转
        return True  # 其他类型允许加载

class hefengTool(QWebEngineView):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("网页元素提取示例")
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint| Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(430, 329) # 高度固定329
        self.setStyleSheet(
        """
        QWebEngineView{
            border-radius: 20px;
        }
        """)

        radius = 18
        self.painterPath = QPainterPath()
        self.painterPath.addRoundedRect(QRectF(self.rect()), radius, radius)
        mask = QRegion(self.painterPath.toFillPolygon().toPolygon())
        self.setMask(mask)

        # ForceDarkMode 的内部编号是 32

        self.url = "https://www.qweather.com" 
        self.xpath = "/html/body/div[1]/div[1]/div/div[3]"

        # 设置自定义页面对象以捕获控制台信息
        self.setPage(CustomWebPage(self))

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_element_exists)
        # self.loadStarted.connect(self.on_load_started)
        self.page().loadStarted.connect(self.on_load_started)
        self.load(QUrl(self.url))

    def contextMenuEvent(self, event):
        # 忽略右键菜单事件
        event.ignore()
        # 可选：打印提示信息
        print("Right-click is disabled.")

    def on_load_started(self):
        print("页面开始加载")
        # 启动轮询检测
        self.timer.start(50)  # 每秒检查一次    

    def check_element_exists(self):
        script = f"""
        (function() {{
            let xpath = `{self.xpath}`;
            let result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            if (result.singleNodeValue) {{
                let clone = result.singleNodeValue.cloneNode(true);
                document.body.innerHTML = '';
                document.body.appendChild(clone);
                return document.documentElement.outerHTML;
            }} else {{
                return '<p>未找到匹配的元素</p>';
            }}
        }})();
        """
        self.page().runJavaScript(script, self.handle_check_result)

    def handle_check_result(self, exists):
        if exists and exists != "<p>未找到匹配的元素</p>":
            print("目标元素已加载，开始处理...")
            self.timer.stop()
            # self.loadStarted.disconnect(self.on_load_started)
            self.page().loadStarted.connect(self.on_load_started)
            self.handle_result(exists)


    # def on_load_finished(self):

    #     js_code = f"""
    #     (function() {{
    #         let xpath = `{self.xpath}`;
    #         let result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
    #         if (result.singleNodeValue) {{
    #             let clone = result.singleNodeValue.cloneNode(true);
    #             document.body.innerHTML = '';
    #             document.body.appendChild(clone);
    #             return document.documentElement.outerHTML;
    #         }} else {{
    #             return '<p>未找到匹配的元素</p>';
    #         }}
    #     }})();
    #     """
    #     self.page().runJavaScript(js_code, self.handle_result)

    def handle_result(self, html):
        print("提取到的内容长度：", len(html))
        self.setHtml(html, baseUrl=QUrl(self.url))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = hefengTool()
    window.show()
    sys.exit(app.exec_())