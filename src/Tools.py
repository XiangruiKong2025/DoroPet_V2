from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from requests import get, exceptions

class Thread_WeatherData(QThread):
    response_received = pyqtSignal(str)
    def __init__(self, api_key=""):
        super().__init__()
        self.apikey = api_key
        self.IP = "127.0.0.1"
        self.weather_service = WeatherDataService(self.apikey)

    def run(self):
        try:
            self.IP = self.weather_service.get_public_ip()
            if self.IP != "127.0.0.1":
                print(self.IP)
                Addr = self.weather_service.get_location_from_ip(self.IP)
                if Addr.get("city"):
                    self.city = Addr.get("city")
                elif Addr.get("pro"):
                    self.city = Addr.get("pro")

                if self.city == "":
                    self.city = "上海"
                weather_data = self.weather_service.get_weather(self.city)
                self.response_received.emit(weather_data)

        except Exception as e:
            # 处理异常情况
            error_msg = f"Error: {str(e)}"
            self.response_received.emit(error_msg)


class WeatherDataService:
    def __init__(self, api_key):
        self.api_key = api_key

    
    def get_public_ip(self):
        try:
            response = requests.get("https://ifconfig.me/ip")     
            return response.text.strip()
        except Exception as e:
            print(f"获取公网 IP 失败: {e}")
            return None
        
    def get_location_from_ip(self, ip_address):
        if not ip_address:
            return None
        surl = f"https://qifu-api.baidubce.com/ip/geo/v1/district?ip={ip_address}"
        if len(ip_address) > 15:
            surl = f"https://qifu-api.baidubce.com/ip/geo/v1/ipv6/district?ip={ip_address}"
            
        try:
            # url = f"http://whois.pconline.com.cn/ipJson.jsp?ip={ip_address}&json=true"
            response = requests.get(surl, timeout=5)
            data = response.json()
            # print(data)
            if data.get("ip") == ip_address:
                posdata = data.get("data", {})
                print(posdata.get("city"))
                return {
                    "city": posdata.get("city"),
                    "region": posdata.get("district"),
                    "pro": posdata.get("prov")
                }
            else:
                print("IP 地理信息查询失败:", data.get("message"))
                return None
        except Exception as e:
            print(f"查询地理位置失败: {e}")
            return None

    def get_weather(self, city):
        if not self.api_key:
            raise ValueError("API 密钥未设置")

        base_url = "https://api.seniverse.com/v3/weather/now.json"   
        params = {
            "location": city,
            "key": self.api_key,
            "language": "zh-Hans",
            "unit": "c"
        }
        # print(params)
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            weather_data = response.json()

            result = weather_data.get("results", [{}])[0]
            location = result.get("location", {})
            now = result.get("now", {})

            city = location.get("name", "未知")
            weather_text = now.get("text", "未知")
            temperature = now.get("temperature", "未知")
            humidity = now.get("humidity", "未知")
            wind_direction = now.get("wind_direction", "未知")
            wind_speed = now.get("wind_speed", "未知")

            return (
                f"知心天气\n城市：{city}\n"
                f"天气：{weather_text}\n"
                f"温度：{temperature}°C\n"
                f"湿度：{humidity}%\n"
                f"风向：{wind_direction}\n"
                f"风速：{wind_speed} km/h"
            )

        except requests.exceptions.RequestException as e:
            print(f"请求天气数据失败: {e}")
            return None

    # def get_public_ip(self):
    #     try:
    #         response = httpx.get("https://ifconfig.me/ip",  timeout=10.0)
    #         response.raise_for_status()  # 显式检查 HTTP 错误
    #         return response.text.strip()
    #     except httpx.RequestError as e:
    #         print(f"获取公网 IP 失败: {e}")
    #         return None

    # def get_location_from_ip(self, ip_address):
    #     if not ip_address:
    #         return None
    #     try:
    #         url = f"http://whois.pconline.com.cn/ipJson.jsp?ip={ip_address}&json=true"
    #         response = httpx.get(url, timeout=5.0)

    #         # 尝试手动解码
    #         try:
    #             text = response.content.decode('utf-8')
    #         except UnicodeDecodeError:
    #             try:
    #                 text = response.content.decode('gbk')
    #             except UnicodeDecodeError:
    #                 text = response.content.decode('gb2312')

    #         data = json.loads(text)

    #         if data.get("ip") == ip_address:
    #             return {
    #                 "city": data.get("city"),
    #                 "region": data.get("region"),
    #                 "pro": data.get("pro")
    #             }
    #         else:
    #             print("IP 地理信息查询失败:", data.get("message"))
    #             return None
    #     except httpx.RequestError as e:
    #         print(f"查询地理位置失败: {e}")
    #         return None
    #     except json.JSONDecodeError as e:
    #         print(f"JSON 解析失败: {e}")
    #         print("原始响应内容:", repr(response.content))
    #         return None
    

    # def get_weather(self, city):
    #     if not self.api_key:
    #         raise ValueError("API 密钥未设置")

    #     base_url = "https://api.seniverse.com/v3/weather/now.json" 
    #     params = {
    #         "location": city,
    #         "key": self.api_key,
    #         "language": "zh-Hans",
    #         "unit": "c"
    #     }

    #     try:
    #         response = httpx.get(base_url, params=params, timeout=10.0)
    #         response.raise_for_status()
    #         return response.json()
    #     except httpx.RequestError as e:
    #         print(f"请求天气数据失败: {e}")
    #         return None
    
    

# class WeatherApp(QWidget):
#     def __init__(self):
#         super().__init__()

#         self.api_key = "SnBaWNZaFTyNDVlj4"  # 替换为你的 API 密钥
#         self.weather_service = WeatherDataService(self.api_key)

#         self.IP = self.weather_service.get_public_ip()
#         if self.IP:
#             Addr = self.weather_service.get_location_from_ip(self.IP)
#             if Addr:
#                 self.city = Addr.get("city")
#             else:
#                 self.city = "北京"
#         else:
#             self.city = "北京"

#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle('天气预报')
#         layout = QVBoxLayout()

#         self.btn = QPushButton('查询天气', self)
#         self.label_ip = QLabel('IP信息：未知', self)
#         self.label_weather = QLabel('天气信息：未知', self)

#         layout.addWidget(self.btn)
#         layout.addWidget(self.label_ip)
#         layout.addWidget(self.label_weather)

#         self.setLayout(layout)
#         self.btn.clicked.connect(self.handle_get_weather)

#         if self.IP:
#             self.label_ip.setText(f'当前IP地址：{self.IP}')
#         else:
#             self.label_ip.setText('无法获取IP地址')

#     def handle_get_weather(self):
#         weather_data = self.weather_service.get_weather(self.city)
#         if not weather_data:
#             QMessageBox.critical(self, "错误", "无法获取天气信息")
#             return

#         try:
#             result = weather_data.get("results", [{}])[0]
#             location = result.get("location", {})
#             now = result.get("now", {})

#             city = location.get("name", "未知")
#             weather_text = now.get("text", "未知")
#             temperature = now.get("temperature", "未知")
#             humidity = now.get("humidity", "未知")
#             wind_direction = now.get("wind_direction", "未知")
#             wind_speed = now.get("wind_speed", "未知")

#             self.label_weather.setText(
#                 f"城市：{city}\n"
#                 f"天气：{weather_text}\n"
#                 f"温度：{temperature}°C\n"
#                 f"湿度：{humidity}%\n"
#                 f"风向：{wind_direction}\n"
#                 f"风速：{wind_speed} km/h"
#             )
#         except Exception as e:
#             QMessageBox.critical(self, "解析错误", f"解析天气数据失败：{e}")

