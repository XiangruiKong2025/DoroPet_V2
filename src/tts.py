# tts_player.py
from io import BytesIO
from threading import Lock, Thread
from requests import get
from wave import open as wave_open
import simpleaudio as sa

class TTSPlayer:
    _lock = Lock()
    _current_play = None          # 正在播放的句柄

    @staticmethod
    def play(text: str,
             base_url: str = "http://127.0.0.1:5000/tts",
             cha_name: str = "可莉",
             timeout: int = 20) -> None:
        if not text.strip():
            print("[TTSPlayer] 空文本，忽略")
            return

        def _download_and_play():
            try:
                resp = get(
                    f"{base_url}?text={text}&cha_name={cha_name}",
                    timeout=timeout
                )
                resp.raise_for_status()
            except Exception as e:
                print(f"[TTSPlayer] 请求失败: {e}")
                return

            audio_bytes = resp.content
            try:
                wav = wave_open(BytesIO(audio_bytes))
                wave_obj = sa.WaveObject(
                    wav.readframes(wav.getnframes()),
                    wav.getnchannels(),
                    wav.getsampwidth(),
                    wav.getframerate()
                )
            except Exception as e:
                print(f"[TTSPlayer] 解码失败: {e}")
                return

            # 线程安全：先停掉旧的，再播新的
            with TTSPlayer._lock:
                if TTSPlayer._current_play is not None:
                    TTSPlayer._current_play.stop()  # 立即打断
                TTSPlayer._current_play = wave_obj.play()

        Thread(target=_download_and_play, daemon=True).start()