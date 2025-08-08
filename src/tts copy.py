# tts_player.py
import io
import threading
import requests
import wave
import simpleaudio as sa

class TTSPlayer:
    @staticmethod
    def play(text: str,
             base_url: str = "http://127.0.0.1:5000/tts", cha_name="可莉",
             timeout: int = 20) -> None:
        if not text.strip():
            print("[TTSPlayer] 空文本，忽略")
            return

        def _download_and_play():
            try:
                resp = requests.get(f"{base_url}?text={text}&cha_name={cha_name}", timeout=timeout)
                resp.raise_for_status()
            except Exception as e:
                print(f"[TTSPlayer] 请求失败: {e}")
                return

            audio_bytes = resp.content
            # TTS 返回的是 WAV 原始字节
            try:
                wav = wave.open(io.BytesIO(audio_bytes))
                wave_obj = sa.WaveObject(
                    wav.readframes(wav.getnframes()),
                    wav.getnchannels(),
                    wav.getsampwidth(),
                    wav.getframerate()
                )
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except Exception as e:
                print(f"[TTSPlayer] 播放失败: {e}")

        threading.Thread(target=_download_and_play, daemon=True).start()