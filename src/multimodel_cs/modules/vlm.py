"""
图片检索模型
"""
import numpy as np
import cv2
from PIL import Image
import io
import base64
import logging
from src.multimodel_cs.prompts.main import IMAGE_ANALYSIS_SYSTEM_PROMPT
from src.multimodel_cs.config.setting import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

# 初始化客户端
client = OpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.SILICONFLOW_BASE_URL
)


# 图片检测函数
def detect_defect_with_vlm(image,prompt:str = None):
    """ image 应该是numpy格式或PIL格式"""
    if isinstance(image,np.ndarray):
        image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
    buf = io.BytesIO()
    image.save(buf,format='JPEG')
    img_b64 = base64.b64decode(buf.getvalue()).decode('utf-8')

    if prompt is None:
        prompt = IMAGE_ANALYSIS_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]}
    ]

    try:
        response = client.chat.completions.create(
            model=settings.VLM_MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=512
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.info(f"图片解析出错：{str(e)}")
        return "未检测到明显异常"

