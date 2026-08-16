"""
LLM模块 主要处理系统提示，API调用链等
"""
import time

from pyexpat.errors import messages

from src.multimodel_cs.config.setting import settings
import logging
import re
from src.multimodel_cs.prompts.main import CUSTOMER_SYSTEM_PROMPT
from openai import OpenAI


logger = logging.getLogger(__name__)

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.SILICONFLOW_BASE_URL,
    timeout=settings.LLM_TIMEOUT
)

# 历史对话消息
class ChatHistoryManage:
    """ 聊天历史处理器 - 维护多轮对话上下文"""
    def __init__(self, max_history_length:int = 10, max_total_tokens:int = 10000):
        """ 初始化对话历史容器 """
        self.history = []
        self.max_history_length = max_history_length or settings.MAX_HISTORY_LENGTH
        self.max_total_tokens = max_total_tokens or settings.MAX_TOTAL_TOKENS

    def add_message(self,role:str,content:str):
        """ 添加消息到历史记录 """
        # 清理内容，移除一些可能的格式规范
        clean_content = re.sub(r"^\s*(user|assistant)\s*[:：]?\s*", "", content.strip())
        clean_content = re.sub(r"\s+", " ", clean_content).strip()  # 移除多余空格
        self.history.append({"role":role,"content":clean_content})
        self._trim_history()

    def _trim_history(self):
        """ 修剪历史记录，确保不超过最大长度和总tokens数"""
        # 1、先按length限制修剪（保留最近的对话）
        # 2、*2的原因是，用户+助手的对话是一对一的
        while len(self.history) > settings.MAX_HISTORY_LENGTH * 2:
            self.history.pop(0)

        # 2、再按tokens限制修剪
        # 简单估算，1 token 约等于4个字符
        total_chars = sum(len(msg['content']) for msg in self.history)
        while total_chars > settings.MAX_TOTAL_TOKENS * 4 and len(self.history) > 2:
            removed = self.history.pop(0)
            total_chars -= len(removed["content"])

    def get_messages(self):
        """ 获取完整的对话消息列表（但是不含系统提示词）"""
        return self.history.copy()

    def get_full_context(self):
        """ 获取完整的对话上下文，包括系统提示词，用户API调用"""
        return [{"role":"system","content":CUSTOMER_SYSTEM_PROMPT}] + self.history.copy()

def parse_intent_from_reply(reply):
    """从助手回复中解析意图"""
    intent_match = re.search(r"【（咨询|投诉|售后）】",reply)
    if intent_match:
        return intent_match.group(1)
    return '咨询'

def clean_reply_content(reply:str):
    """ 清理助手回复内容，移除异常标记和格式 """
    # 移除 user/assinstant 标记
    reply = re.sub(r"\b(usr|assistant)\b\s*[:：]?\s*", "", reply)
    # 移除多余的引号
    reply = re.sub(r'[""\']+', "", reply)
    # 移除多余的换行符和空格
    reply = re.sub(r"\n{3,}", "\n\n", reply)
    reply = re.sub(r" +", " ", reply)
    # 移除开头和结尾的空白
    reply = reply.strip()
    # 如果回复内容太短或者只有数字，使用默认回复
    if len(reply) < 5 or reply.isdigit():
        reply = "【咨询】抱歉，我暂时无法理解您的问题。请提供更多详细信息。"
    return reply

def generate_response(user_text:str, image_features:str="", chat_history:ChatHistoryManage = None):
    """生成回答"""
    content = user_text
    if image_features:
        content += f"\n图片检测：{image_features}"

    # 如果提供了对话历史，使用完整上下文
    if chat_history:
        chat_history.add_message("user",user_text)
        messages = chat_history.get_full_context()
    else:
        # 没有对话历史，就是第一轮对话，构建messages
        messages = [
            {"role":"system","content":CUSTOMER_SYSTEM_PROMPT},
            {"role":"user","content":content}
        ]

    # 重试机制
    for attempt in range(settings.LLM_MAX_RETRIES):
        try:
            print(f"正在生成回复... 第{attempt+1}次尝试")
            response = client.chat.completions.create(
                model=settings.SILICONFLOW_MODEL_NAME,
                messages=messages,
                temperature=0.5,
                max_tokens=1024,
            )
            reply = response.choices[0].message.content.strip()
            print(f"LLM开始回复：{reply[:200]}...")
            # 清洗回复的内容
            clean_reply = clean_reply_content(reply)
            print(f"LLM清理回复：{clean_reply[:200]}...")
            # 提取意图
            intent = parse_intent_from_reply(clean_reply)
            if not re.search(r"【(咨询|投诉|售后)】", clean_reply):
                clean_reply = f"【咨询】{clean_reply}"
            # 如果有对话历史，保存助手回复
            if chat_history:
                chat_history.add_message("assistant",clean_reply)
            print("LLM请求成功")
            return {
                "intent":intent,
                "slots":{"product":"","issue":""},
                "reply":clean_reply
            }
        except Exception as e:
            print(f"LLM请求失败：{str(e)}")
            if attempt < settings.LLM_MAX_RETRIES -1:
                time.sleep(settings.LLM_RETRY_DELAY)
                continue
            else:
                error_reply = "【咨询】服务暂时不可用，请稍后重试。"
                if chat_history:
                    chat_history.add_message("assistant",error_reply)
                return {
                    "intent":"咨询",
                    "slots":{"product":"","issue":""},
                    "reply":error_reply
                }

def generate_response_with_rag(user_text:str,
                               image_features:str="",
                               chat_history:ChatHistoryManage = None,
                               extra_context:str =""):
    """集成RAG优化，改造的LLM回复函数"""
    if extra_context:
        combined_text = f"【系统提示】请基于以下参考信息回答客户问题，不要编造。【参考信息】：\n{extra_context}\n\n【用户问题】：{user_text}"
    else :
        combined_text = user_text
    return generate_response(combined_text,image_features,chat_history)