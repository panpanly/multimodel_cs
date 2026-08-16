"""
语音处理
"""
import requests
from src.multimodel_cs.config.setting import settings


def speech_to_text(file_bytes:bytes):
    headers = {
        "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}"
    }

    files = {
        "file": ("audio.wav", file_bytes, "audio/wav"),
    }

    data = {
        "model":settings.ASR_MODEL,
        "language":"zh"
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