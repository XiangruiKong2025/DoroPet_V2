import psutil
import time
import os

class WindowsSystemMonitor:
    """
    获取 Windows 当前 CPU、内存占用。
    也可在 Linux/macOS 上直接使用，无额外修改。
    """

    def __init__(self, interval: float = 1.0):
        """
        :param interval: CPU 利用率采样间隔（秒）。默认 1 秒。
        """
        self.interval = interval

    # ---------- 接口 ----------
    def get_cpu_percent(self) -> float:
        """返回当前整机的 CPU 占用百分比（0~100）"""
        return psutil.cpu_percent(interval=self.interval)

    def get_memory_percent(self) -> float:
        """返回当前整机的内存占用百分比（0~100）"""
        return psutil.virtual_memory().percent

    def get_snapshot(self) -> dict:
        """一次性返回 CPU 和内存占用"""
        return {
            "cpu_percent": self.get_cpu_percent(),
            "memory_percent": self.get_memory_percent()
        }
