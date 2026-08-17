"""
语音处理
"""
import requests
from src.multimodel_cs.config.setting import settings
import subprocess


def speech_to_text(file_bytes:bytes):
    headers = {
        "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}"
    }

    files = {
        "file": ("audio.wav", file_bytes, "audio/wav"),
    }

    data = {
        "model":settings.ASR_MODEL,
        "language":"auto"
    }

    response = requests.post(
        f"{settings.SILICONFLOW_BASE_URL}/audio/transcriptions",
        headers=headers,
        files=files,
        data=data
    )

    if response.status_code == 200:
        return response.json()["text"]
    else :
        raise Exception(f"ASR Error {response.status_code},{response.text}")

def convert_audio_to_16k_mono_wav(raw_bytes: bytes) -> bytes:
    """
    支持 m4a / webm / mp3 输入，输出16000Hz 单声道PCM wav
    依赖：系统安装ffmpeg，并且环境变量PATH可调用ffmpeg命令
    """
    cmd = [
        "ffmpeg",
        "-i", "pipe:0",       # 输入来自管道字节
        "-ac", "1",           # 单声道
        "-ar", "16000",       # 采样率16k
        "-f", "wav",
        "-y",                 # 覆盖输出，不询问
        "pipe:1"              # 输出到stdout管道
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = proc.communicate(input=raw_bytes)
    if proc.returncode != 0:
        err_msg = err.decode("utf‑8", errors="ignore")
        raise Exception(f"音频转码失败：{err_msg}")
    return out