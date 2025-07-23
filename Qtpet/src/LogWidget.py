from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from datetime import datetime
import sys
import logging

class StreamRedirector(QObject):
    outputWritten = pyqtSignal(str)

    def write(self, text):
        self.outputWritten.emit(str(text))

    def flush(self):
        pass

class LogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.initUI()
        self.redirect_output()
        

    def initUI(self):
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self.text_edit.document().setMaximumBlockCount(1000)

    def redirect_output(self):
        # 重定向 stdout
        self.stdout_redirector = StreamRedirector()
        self.stdout_redirector.outputWritten.connect(self.handle_stdout)
        sys.stdout = self.stdout_redirector

        # 重定向 stderr
        self.stderr_redirector = StreamRedirector()
        self.stderr_redirector.outputWritten.connect(self.handle_stderr)
        sys.stderr = self.stderr_redirector


    def handle_stdout(self, text:str):
        if text.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_text = f"[{timestamp}]{text}\n"
            self._insert_log(formatted_text)

    def handle_stderr(self, text:str):
        if text.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_text = f"[{timestamp}][ERR] {text}\n"
            self._insert_log(formatted_text)

    def _insert_log(self, text):
         # 防止控件已销毁
        if not hasattr(self, 'text_edit') or self.text_edit is None:
            return
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.insertPlainText(text)
        self.text_edit.ensureCursorVisible()
        


    def closeEvent(self, event):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        super().closeEvent(event)