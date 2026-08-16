"""
用模型单例获取大模型客户端
"""
from langchain_openai import ChatOpenAI
import logging
from dotenv import load_dotenv
from src.multimodel_cs.config.setting import settings

logger = logging.getLogger(__name__)

load_dotenv()

class LLMClient:
    def __init__(self):
        self.llm = None
        self._initialoze_client()

    def _initialoze_client(self):
        """ 初始化大模型调用 """
        try:
            self._llm = ChatOpenAI(
                model=settings.SILICONFLOW_MODEL_NAME,
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_BASE_URL,
                temperature=0.1,
                verbose=True
            )
        except Exception as e:
            raise logger.error(f"初始化大模型失败：{str(e)}")

    def get_llm(self):
        return self._llm

_llm_client = None

def get_llm_client():
    """获取大模型单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client