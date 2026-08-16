import edge_tts # Edge浏览器自带的语音合成工具
import tempfile # 临时文件
from src.multimodel_cs.config.setting import settings


# 语音合成的函数
async def text_to_speech(text:str) -> bytes:
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, # 关闭自动删除
        suffix=".mp3" # 指定文件后缀
    )
    temp_file.close()  # 关闭文件句柄，后面edge_tts直接往这个文件中写数据
    tts_engine = edge_tts.Communicate(text,settings.VOICE)
    await tts_engine.save(temp_file.name)
    return temp_file.name