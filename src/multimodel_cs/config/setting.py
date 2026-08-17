from pydantic import BaseModel
from typing import Literal
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings(BaseModel):
    # LLM超时时间（秒）
    LLM_TIMEOUT:int = 30
    # 大模型重试次数
    LLM_MAX_RETRIES: int = 3
    # 大模型重试间隔时间（秒）
    LLM_RETRY_DELAY: int = 2
    # 最大历史对话长度
    MAX_HISTORY_LENGTH:int = 10
    # 单次模型对话中传入的token数量
    MAX_TOTAL_TOKENS:int = 10000

    # 项目基本配置
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent.resolve()

    # 数据存储
    KB_PATH: Path = BASE_DIR / "data/knowledge_base.json"
    # 本地向量模型地址
    EMBEDDING_MODEL_PATH: str = BASE_DIR / "models" / "bge_small_zh"
    # 静态资源路径
    STATIC_PATH:str = BASE_DIR / "static"

    # SiliconFlow配置
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY")
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL_NAME: str = "Qwen/Qwen2.5-7B-Instruct"

    # 大模型配置
    LLM_MODEL:str = "Qwen/Qwen2.5-7B-Instruct"
    ASR_MODEL:str = "FunAudioLLM/SenseVoiceSmall"
    TTS_MODEL:str = "FunAudioLLM/CosyVoice2-0.5B"
    YOLO_MODEL:str = "yolo11n.pt"
    VLM_MODEL:str = "Qwen/Qwen3-VL-8B-Instruct"

    # 数据库
    SQLITE_DB:str = "chat.db"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = BASE_DIR / "app.log"

    #语音合成的参数 "中文女声 晓晓"
    VOICE:str = "zh-CN-XiaoxiaoNeural"

    # 允许跨域访问链接
    ALLOW_ORIGINS:list[str] = ["http://localhost:8080", "http://localhost:3000", "http://127.0.0.1:8080","http://localhost:63342"]









settings = Settings()


