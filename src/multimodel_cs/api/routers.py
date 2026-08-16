import base64
import os
import uuid

import cv2
import numpy as np
from fastapi import APIRouter,UploadFile,File,Form,Query
from torch.utils.serialization.config import save

from src.multimodel_cs.storage.db import init_db,load_session_history,save_chat,save_session_history
from src.multimodel_cs.modules.llm import ChatHistoryManage,generate_response_with_rag,generate_response
from src.multimodel_cs.modules.rag import ProductRAG
from src.multimodel_cs.modules.vlm import detect_defect_with_vlm
from src.multimodel_cs.modules.asr import speech_to_text
from src.multimodel_cs.modules.ttx import text_to_speech


# 定义路由
router = APIRouter()

# 初始化数据库
init_db()

# 获取或创建会话
def get_or_create_session(session_id:str):
    """ 获取或创建会话（从数据库中加载历史）"""
    chat_history = ChatHistoryManage()
    if session_id:
        history = load_session_history(session_id)
        for msg in history:
            chat_history.history.append(msg)
    return chat_history

# 保留会话历史到数据库
def save_session(chat_history:ChatHistoryManage,session_id:str):
    """ 保存会话历史到数据库（只保存新增的消息）"""
    # 获取已保存的消息数量
    existing_count = len(load_session_history(session_id))
    # 只保存新增的消息
    for msg in chat_history.history[existing_count:]:
        save_session_history(session_id,msg["role"], msg["content"])

@router.post("/api/chat/text")
async def chat_text(text:str = Form(...), session_id:str = Form(None), use_rag:bool = Form(False)):
    """文本聊天接口"""
    # 初始化会话ID
    current_session_id = session_id or str(uuid.uuid4())
    # 获取或创建会话
    chat_history = get_or_create_session(session_id)
    # 如果启用该Rags
    if use_rag:
        # 初始化RAG
        rag = ProductRAG()
        rag_context = rag.retrieve(text)
    # 基于RAG生成回复
    response = generate_response_with_rag(text,chat_history=chat_history,extra_context=rag_context)
    # 保存对话记录
    save_chat(text,response["intent"],response["reply"])
    # 保存会话历史
    save_session(chat_history,current_session_id)
    return {
        "session_id":current_session_id,
        **response
    }

@router.post("/api/chat/image")
async def chat_image(
    image:UploadFile = File(...),
    text:str = Form(""),
    session_id:str = Form(None)
):
    """ 图片聊天接口"""
    # 获取或创建会话id
    current_session_id = session_id or str(uuid.uuid4())
    # 拿到上传文件二进制
    image_bytes = await image.read()
    # bytes → numpy一维uint8数组
    image_array = np.frombuffer(image_bytes,np.uint8)
    # 解码为图片矩阵(height, width, channel)
    image_matrix = cv2.imdecode(image_array,cv2.IMREAD_COLOR)
    # 检测图像
    feature = detect_defect_with_vlm(image_matrix)
    combined_text = text if text else "请描述图片中的问题"
    # 获取或创建会话
    chat_history = get_or_create_session(current_session_id)
    # 生成回复
    response = generate_response(combined_text,feature,chat_history=chat_history)
    # 保存对话记录
    save_chat(combined_text,response["intent"],response["reply"])
    # 保存会话历史
    save_session(chat_history,current_session_id)
    return {
        "session_id": current_session_id,
        "detections":feature,
        **response
    }

@router.post("/api/chat/voice")
async def chat_voice(
        audio:UploadFile = File(...),
        text:str = Form(""),
        session_id:str = Form(None)
):
    # 获取或新建会话id
    current_session_id = session_id or str(uuid.uuid4())
    # 处理语音
    audio_bytes = await audio.read()
    print(f"接收到音频：{len(audio_bytes)} bytes")
    transcript = speech_to_text(audio_bytes)
    print(f"识别结果：{transcript}")
    # 如果没有识别到语音内容
    if not transcript.strip():
        # 获取或创建会话
        chat_history = get_or_create_session(current_session_id)
        # 保存对话到历史
        chat_history.add_message("user","[语音未识别]")
        chat_history.add_message("assistant","抱歉，我没有听清您的问题，请您再说一遍")
        # 保存会话历史
        save_session(chat_history,current_session_id)

        return {
            "session_id":current_session_id,
            "transcript":"",
            "intent":"咨询",
            "slots":{"product":"","issue":""},
            "reply":"抱歉，我没有听清您的问题，请您再说一遍",
            "audio_base64":"",
        }
    combined_text = (text + " " + transcript) if text else transcript
    # 获取或创建会话
    chat_history = get_or_create_session(current_session_id)
    # 生成回复
    response = generate_response(combined_text, chat_history=chat_history)
    # 转语音
    tts_path = await text_to_speech(response["reply"])
    with open(tts_path,'rb') as f:
        audio_base64 = base64.b64decode(f.read()).decode("utf-8")

    os.remove(tts_path)
    # 保存对话记录
    save_chat(combined_text, response["intent"], response["reply"])
    # 保存会话历史
    save_session(chat_history, current_session_id)
    return {
        "session_id": current_session_id,
        "transcript": transcript,
        "intent": response["intent"],
        "slots": response["slots"],
        "reply": response["reply"],
        "audio_base64": audio_base64
    }

