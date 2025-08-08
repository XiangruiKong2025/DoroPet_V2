import sys
import pyaudio
import json
from vosk import Model, KaldiRecognizer
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import *
from .GeneralOptData import get_GeneralOptData
from .switchbtn import SwitchButton

class VoskRecognitionThread(QThread):
    """处理语音识别的线程类"""
    partial_result = pyqtSignal(str)  # 实时识别结果信号
    final_result = pyqtSignal(str)    # 完整识别结果信号
    error_init = pyqtSignal(str)
    def __init__(self, model_path="vosk/vosk-model-cn-0.222"):
        super().__init__()
        self.modelpath = model_path
        

    def initmodel(self):
        try:
            self.model = Model(self.modelpath)  # 加载模型
            self.recognizer = KaldiRecognizer(self.model, 16000)  # 创建识别器
        except Exception as e:
            self.error_init.emit(f"加载错误: {e}")
            return
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.frames_per_buffer = 8000
        self.is_recording = False  # 录音状态标志
        self.audio = None
        self.stream = None


    def run(self):
        """线程执行方法"""
        try:
            # 初始化音频流
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.frames_per_buffer
            )
            self.is_recording = True
            
            print("开始录音...")
            while self.is_recording:
                data = self.stream.read(4000, exception_on_overflow=False)
                if self.is_recording:  # 双重检查
                    if self.recognizer.AcceptWaveform(data):
                        # 完整句子识别结果
                        result = json.loads(self.recognizer.Result())['text']
                        self.final_result.emit(result)
                    else:
                        # 实时识别结果
                        partial = json.loads(self.recognizer.PartialResult())['partial']
                        self.partial_result.emit(partial)
                        
        except Exception as e:
            print(f"录音错误: {e}")
        finally:
            self.cleanup()

    def stop(self):
        """停止录音"""
        self.is_recording = False
        self.wait()  # 等待线程结束

    def cleanup(self):
        """清理资源"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()
        except Exception as e:
            print(f"清理资源错误: {e}")


import sys
import os
import zipfile
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


# 下载和解压线程类
class DownloadExtractThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, url, zip_path, extract_path):
        super().__init__()
        self.url = url
        self.zip_path = zip_path
        self.extract_path = extract_path

    def run(self):
        self.status.emit("开始下载文件...")

        # 下载文件
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(self.zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
                            self.status.emit(f"下载中: {percent}%")

            self.status.emit("下载完成，开始解压...")
            self.progress.emit(0)

            # 解压文件
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_files = zip_ref.namelist()
                total_files = len(zip_files)
                for i, file in enumerate(zip_files):
                    zip_ref.extract(file, self.extract_path)
                    percent = int(((i + 1) / total_files) * 100)
                    self.progress.emit(percent)
                    self.status.emit(f"解压中: {percent}% - {file}")

            self.status.emit("解压完成！")
            os.remove(self.zip_path)
            self.finished_signal.emit()

        except Exception as e:
            self.status.emit(f"出错: {str(e)}")
            QMessageBox.critical(None, "错误", str(e))

        finally:
            self.quit()

class VoskSettingWindow(QWidget):
    # MODEL_MAP: 从 https://alphacephei.com/vosk/models  提取的语言列表及对应的 small/big 模型名
    MODEL_MAP = {
        "Chinese": {
            "small": "vosk-model-small-cn-0.22",
            "big": "vosk-model-cn-0.22"
        },
        "English (US)": {
            "small": "vosk-model-small-en-us-0.15",
            "big": "vosk-model-en-us-0.22"
        },
        "Indian English": {
            "small": "vosk-model-small-en-in-0.4",
            "big": "vosk-model-en-in-0.5"
        },
        "Russian": {
            "small": "vosk-model-small-ru-0.22",
            "big": "vosk-model-ru-0.42"
        },
        "French": {
            "small": "vosk-model-small-fr-0.22",
            "big": "vosk-model-fr-0.22"
        },
        "Spanish": {
            "small": "vosk-model-small-es-0.42",
            "big": "vosk-model-es-0.42"
        },
        "Portuguese (Brazil)": {
            "small": "vosk-model-small-pt-0.3",
            "big": "vosk-model-pt-fb-v0.1.1-20220516_2113"
        },
        "German": {
            "small": "vosk-model-small-de-0.15",
            "big": "vosk-model-de-0.21"
        },
        "Italian": {
            "small": "vosk-model-small-it-0.22",
            "big": "vosk-model-it-0.22"
        },
        "Dutch": {
            "small": "vosk-model-small-nl-0.22",
            "big": "vosk-model-nl-spraakherkenning-0.6"
        },
        "Japanese": {
            "small": "vosk-model-small-ja-0.22",
            "big": "vosk-model-ja-0.22"
        },
        "Korean": {
            "small": "vosk-model-small-ko-0.22",
            "big": None  # 没有官方 big 模型
        },
        "Hindi": {
            "small": "vosk-model-small-hi-0.22",
            "big": "vosk-model-hi-0.22"
        },
        "Vietnamese": {
            "small": "vosk-model-small-vn-0.4",
            "big": "vosk-model-vn-0.4"
        },
        "Catalan": {
            "small": "vosk-model-small-ca-0.4",
            "big": None
        },
        "Arabic": {
            "small": "vosk-model-ar-mgb2-0.4",
            "big": "vosk-model-ar-0.22-linto-1.1.0"
        },
        "Arabic Tunisian": {
            "small": "vosk-model-small-ar-tn-0.1-linto",
            "big": "vosk-model-ar-tn-0.1-linto"
        },
        "Farsi": {
            "small": "vosk-model-small-fa-0.42",
            "big": "vosk-model-fa-0.42"
        },
        "Filipino": {
            "small": None,
            "big": "vosk-model-tl-ph-generic-0.6"
        },
        "Ukrainian": {
            "small": "vosk-model-small-uk-v3-small",
            "big": "vosk-model-uk-v3"
        },
        "Kazakh": {
            "small": "vosk-model-small-kz-0.15",
            "big": "vosk-model-kz-0.15"
        },
        "Swedish": {
            "small": "vosk-model-small-sv-rhasspy-0.15",
            "big": None
        },
        "Esperanto": {
            "small": "vosk-model-small-eo-0.42",
            "big": None
        },
        "Czech": {
            "small": "vosk-model-small-cs-0.4-rhasspy",
            "big": None
        },
        "Polish": {
            "small": "vosk-model-small-pl-0.22",
            "big": None
        },
        "Uzbek": {
            "small": "vosk-model-small-uz-0.22",
            "big": None
        },
        "Breton": {
            "small": None,
            "big": "vosk-model-br-0.8"
        },
        "Gujarati": {
            "small": "vosk-model-small-gu-0.42",
            "big": "vosk-model-gu-0.42"
        },
        "Tajik": {
            "small": "vosk-model-small-tg-0.22",
            "big": "vosk-model-tg-0.22"
        },
        "Telugu": {
            "small": "vosk-model-small-te-0.42",
            "big": None
        }
    }

    voskEnChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vosk 模型下载器")
        # self.resize(500, 300)
        self.cfgdata = get_GeneralOptData()
        layout = QFormLayout()


        self.voskEnbtn = SwitchButton()
        self.voskEnbtn.setChecked(self.cfgdata.voskEn)
        hbox = QHBoxLayout()
        hbox.addWidget(self.voskEnbtn)
        hbox.addStretch()  # 添加水平弹簧，右侧填充空白
        hbox.addWidget(QLabel("如果使用了完整的模型，需要加载一段时间，请耐心等待"))
        layout.addRow(QLabel("语音输入"),hbox)

        hbox3 = QHBoxLayout()
        hbox3.addStretch() 
        self.curModel = QLabel(self.cfgdata.voskpath)
        hbox3.addWidget(self.curModel)
        layout.addRow(QLabel("当前使用模型"), hbox3)

        # 语言选择
        hbox2 = QHBoxLayout()
        self.lang_label = QLabel("请选择语言", self)
        self.lang_combo = QComboBox(self)
        for lang in self.MODEL_MAP:
            self.lang_combo.addItem(lang)
        hbox2.addWidget(self.lang_combo)

        # 模型类型选择
        self.model_type_combo = QComboBox(self)
        self.model_type_combo.addItems(["轻量模型，加载更快，但是效果一般", "完整模型，加载较慢，效果更好"])
        hbox2.addWidget(self.model_type_combo)

        layout.addRow(self.lang_label, hbox2)

        # 状态栏
        self.status_label = QLabel("就绪", self)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.check_button = QPushButton("使用本地模型", self)
        self.download_button = QPushButton("开始下载", self)
        btn_layout.addWidget(self.check_button)
        btn_layout.addWidget(self.download_button)
        layout.addRow( QLabel(""), btn_layout)

        self.setLayout(layout)

        # 初始化路径
        self.vosk_dir = "./vosk"

        # 绑定事件
        self.check_button.clicked.connect(self.check_local_model)
        self.download_button.clicked.connect(self.start_download_extract)
        self.voskEnbtn.statusChanged.connect(self.voskEnbtnchanged)
        # 自动检查一次
        self.check_local_model()

    def voskEnbtnchanged(self):
        self.cfgdata.voskEn = self.voskEnbtn.checked()
        self.voskEnChanged.emit(self.cfgdata.voskEn)

    def check_local_model(self):
        """检查当前选择的模型是否已存在"""
        lang = self.lang_combo.currentText()
        model_type = "small" if self.model_type_combo.currentIndex() == 0 else "big"
        model_name = self.MODEL_MAP[lang].get(model_type)

        if not model_name:
            self.status_label.setText("❌ 当前语言不支持所选模型类型")
            self.download_button.setEnabled(False)
            return

        model_path = os.path.join(self.vosk_dir, model_name)
        model_path = model_path.replace("\\", "/")
        if os.path.exists(model_path) and os.listdir(model_path):
            self.status_label.setText(f"✅ 已找到本地模型: {model_name}")
            self.download_button.setEnabled(False)
            self.cfgdata.voskpath = model_path
            self.curModel.setText(self.cfgdata.voskpath)
        else:
            self.status_label.setText("❌ 未检测到本地模型，可以开始下载")
            self.download_button.setEnabled(True)

    def start_download_extract(self):
        """开始下载并解压模型"""
        lang = self.lang_combo.currentText()
        model_type = "small" if self.model_type_combo.currentIndex() == 0 else "big"
        model_name = self.MODEL_MAP[lang].get(model_type)

        if not model_name:
            QMessageBox.critical(self, "错误", "当前语言不支持所选模型类型！")
            return

        url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
        zip_path = os.path.join(self.vosk_dir, f"{model_name}.zip")
        extract_path = self.vosk_dir

        self.thread = DownloadExtractThread(url, zip_path, extract_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(self.status_label.setText)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.start()

        self.download_button.setEnabled(False)

    def on_finished(self):
        """下载完成后的处理"""
        lang = self.lang_combo.currentText()
        model_type = "small" if self.model_type_combo.currentIndex() == 0 else "big"
        model_name = self.MODEL_MAP[lang].get(model_type)
        QMessageBox.information(
            self, "完成", f"{model_name} 已成功下载并解压到 {self.vosk_dir}！"
        )
        self.check_local_model()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VoskSettingWindow()
    window.show()
    sys.exit(app.exec_())