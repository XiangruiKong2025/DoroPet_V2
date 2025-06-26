import sys
import json
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# 接口类型模板
SERVICE_TEMPLATES = {
    "deepseek": {
        "baseurl": "https://api.deepseek.com",
        "apikey": "",
        "model": "deepseek-chat"
    },
    "openai": {
        "baseurl": "https://api.openai.com",
        "apikey": "",
        "model": "gpt-3.5-turbo"
    },
    "qwen":{
         "baseurl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "apikey": "",
        "model": "qwen-plus"
    },
    "maas":{
         "baseurl": "https://maas-api.cn-huabei-1.xf-yun.com/v1",
        "apikey": "",
        "model": "xop3qwen235b"
    },
    "gemini":{
        "baseurl": "https://generativelanguage.googleapis.com/v1beta/openai",
        "apikey": "",
        "model": "gemini-2.0-flash"
    }

}

class LLMConfigWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM 接口配置")
        self.resize(600, 400)

        # 初始化配置数据
        self.config_path = "cfg/LLMconfig.json"
        self.config = self.load_config()
        self.current_service = self.config.get("app", {}).get("default", "")

        self.param_widgets = {}  # 当前服务的参数控件
        self.service_combo = QComboBox()
        self.params_container = QWidget()
        self.params_layout = QVBoxLayout()

        self.init_ui()
        self.update_service_combo()
        self.restore_current_service()
        self.update_service_list()

    def load_config(self):
        os.makedirs("cfg", exist_ok=True)
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"app": {"default": ""}, "services": []}


    def save_config(self):
        # 清理所有参数值的前后空格
        for service in self.config.get("services", []):
            if "params" in service and isinstance(service["params"], dict):
                for key, value in service["params"].items():
                    if isinstance(value, str):
                        service["params"][key] = value.strip()

        # 写入文件（保持 UTF-8 编码，确保中文正常显示）
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

        self.show_notification("配置已保存成功。")

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 模型选择
        model_layout = QHBoxLayout()
        self.service_combo.currentTextChanged.connect(self.change_current_service)
        model_layout.addWidget(QLabel("当前服务:"))
        model_layout.addWidget(self.service_combo)

        model_layout.addStretch(1)

        add_btn = QPushButton("添加")
        add_btn.setObjectName("Tool_button")
        add_btn.clicked.connect(self.add_service)
        model_layout.addWidget(add_btn)

        del_btn = QPushButton("删除")
        del_btn.setObjectName("Tool_button")
        del_btn.clicked.connect(self.delete_service)
        model_layout.addWidget(del_btn)

        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.setObjectName("Tool_button")
        save_btn.clicked.connect(self.save_service)
        model_layout.addWidget(save_btn)

        main_layout.addLayout(model_layout)

        # 参数区域
        # self.params_container.setLayout(self.params_layout)
        # scroll_area = QScrollArea()
        # scroll_area.setWidgetResizable(True)
        # scroll_area.setWidget(self.params_container)
        # main_layout.addWidget(scroll_area)

        # 模型列表
        self.service_list = QListWidget()
        self.service_list.setObjectName("service_list")
        # self.service_list.setFlow(QListView.LeftToRight)  # 自动换行排列
        # self.service_list.setWrapping(True)
        self.service_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.service_list.setResizeMode(QListWidget.Adjust)
        self.service_list.setSpacing(10)

        main_layout.addWidget(self.service_list)



        self.setLayout(main_layout)

    def update_service_combo(self):
        self.service_combo.clear()
        for svc in self.config.get("services", []):
            self.service_combo.addItem(svc["name"])

    def restore_current_service(self):
        if self.current_service:
            index = self.service_combo.findText(self.current_service)
            if index >= 0:
                self.service_combo.setCurrentIndex(index)
                # self.load_service_params(self.current_service)
                self.update_service_list()

    def update_service_list(self):
        self.service_list.clear()
        for svc in self.config.get("services", []):
            item = QListWidgetItem(self.service_list)
            container = self.create_service_container(svc)
            item.setSizeHint(container.sizeHint())
            self.service_list.setItemWidget(item, container)

    def create_service_container(self, svc):
        container = QFrame()
        container.setObjectName("service_container")
        if(self.current_service == svc['name']):
            container.setObjectName("service_container_cur")
        
        layout = QVBoxLayout(container)

        name_label = QLabel(f"<b>服务名称：</b> {svc['name']}")
        layout.addWidget(name_label)

        provider_label = QLabel(f"<b>服务提供商：</b> {svc['provider']}")
        layout.addWidget(provider_label)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        self.param_widgets[svc['name']] = {}
        for key, value in svc["params"].items():
            line_edit = QLineEdit(value)
            if key == "apikey":
                line_edit.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)

            line_edit.textEdited.connect(lambda: self.serviceParamsChanged(svc['name']))
            keylabel = QLabel(key)
            keylabel.setMinimumWidth(100)
            self.param_widgets[svc['name']][key] = line_edit
            form_layout.addRow(keylabel, line_edit)
        layout.addLayout(form_layout)

        return container

    def serviceParamsChanged(self, name):
        for svc in self.config.get("services", []):
            if svc["name"] == name:
                for key, widget in self.param_widgets[svc["name"]].items():
                    svc["params"][key] = widget.text().strip()
                break


    def change_current_service(self, new_service=None):
        # 保存当前服务的参数
        current_service = self.current_service
        if current_service:
            for svc in self.config.get("services", []):
                if svc["name"] == current_service and self.param_widgets.get(svc["name"]):
                    for key, widget in self.param_widgets[svc["name"]].items():
                        svc["params"][key] = widget.text().strip()
                    break

        # 更新默认服务
        if new_service:
            self.config["app"]["default"] = new_service
            self.current_service = new_service
            # self.load_service_params(new_service)
            self.update_service_list()

    def save_service(self, new_service=None):
        # 保存当前服务的参数
        # current_service = self.current_service
        # if current_service:
        for svc in self.config.get("services", []):
            # if svc["name"] == current_service:
            for key, widget in self.param_widgets[svc["name"]].items():
                svc["params"][key] = widget.text().strip()
            break

        # 更新默认服务
        if new_service:
            self.config["app"]["default"] = new_service
            self.current_service = new_service
            # self.load_service_params(new_service)
            self.update_service_list()

        self.save_config()

    def add_service(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("添加服务")
        layout = QVBoxLayout()

        name_label = QLabel("服务名称:")
        name_input = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(name_input)

        type_label = QLabel("接口类型:")
        type_combo = QComboBox()
        type_combo.addItems(SERVICE_TEMPLATES.keys())
        layout.addWidget(type_label)
        layout.addWidget(type_combo)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        ok_btn.clicked.connect(lambda: self.handle_add_service(dialog, name_input.text(), type_combo.currentText()))
        cancel_btn.clicked.connect(dialog.reject)

        dialog.setLayout(layout)
        dialog.exec_()

    def handle_add_service(self, dialog, name, service_type):
        if not name or any(svc["name"] == name for svc in self.config.get("services", [])):
            QMessageBox.warning(self, "错误", "服务名称不能为空或已存在。")
            return

        if service_type not in SERVICE_TEMPLATES:
            QMessageBox.warning(self, "错误", "无效的接口类型。")
            return

        new_service = {
            "name": name,
            "provider": service_type,
            "params": SERVICE_TEMPLATES[service_type].copy()
        }

        self.config["services"].append(new_service)
        self.config["app"]["default"] = name
        # self.save_config()
        self.update_service_combo()
        self.service_combo.setCurrentText(name)
        dialog.accept()

    def delete_service(self):
        current_name = self.service_combo.currentText()
        if not current_name:
            return

        reply = QMessageBox.question(self, "确认删除", f"确定要删除服务 {current_name} 吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config["services"] = [svc for svc in self.config.get("services", []) if svc["name"] != current_name]
            if self.config["app"]["default"] == current_name:
                if self.config["services"]:
                    self.config["app"]["default"] = self.config["services"][0]["name"]
                else:
                    self.config["app"]["default"] = ""
            # self.save_config()
            self.update_service_combo()
            if self.config["services"]:
                self.service_combo.setCurrentIndex(0)
            else:
                self.current_service = ""
                # self.load_service_params("")
                self.update_service_list()

    def show_notification(self, message):
        QMessageBox.information(self, "LLM 配置", message, QMessageBox.Ok)

    def get_current_service_config(self):
        current_name = self.service_combo.currentText()
        for svc in self.config.get("services", []):
            if svc["name"] == current_name:
                return svc.copy()
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LLMConfigWindow()
    window.show()

    aa = window.get_current_service_config()
    sys.exit(app.exec_())