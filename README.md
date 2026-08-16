先来分析系统结构：
.env        存储API_key这样的环境变量
config.py   配置信息
# 前端配置
static      静态文件
gradio_app.py
chat.html
# 接入数据进行处理
modules     数据处理模块
    llm.py      
    asr.py
    tts.py
    detector.py
    # 进行优化
    rag.py
    vlm.py
# 后端配置
api         后端
    routes.py   路由
# 数据层
chat.db     数据库

# 主页面
app.py

# 配置环境
conda create -n multimodel_cs_env python=3.10
conda activate multimodel_cs_env
pip install -r requirements.txt


# YOLO目标检测时，遇见问题
原始的YOLO11，使用的是COCO数据集，是没有关于女装的标签的，所以需要自己训练一个模型。

# 训练模型
## 1. 准备数据集
从百度上或者购物软件上下载图片，然后进行标注，标注的工具可以使用labelImg，标注的格式使用YOLO格式。
当然也可以从网上搜索 "服装异常识别" 数据集，但是可能需要自己标注整理，甚至付费。

## 2. 训练模型
from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolo11n.pt")
    results = model.train(
        data="datasets/defect.yaml",
        epochs=5,
        imgsz=640,
        batch=8,
        lr0=0.001,
        name="defect_v5"
    )

## 3. 测试模型
    # 使用微调后的模型进行预测
    model = YOLO("runs/detect/defect_v5-2/weights/best.pt")
    results = model.predict(source="static/test.jpg", conf=0.1)
    print(results[0].boxes.cls)

## 对微调模型测试后，发现问题
1. 数据质量不高、数据量不多，导致模型训练效果不好。
2. 电商客服的实际场景中，图像质量不高，可能会出现模糊、遮挡等问题。还有就是对于女装衣服来说，衣服破洞 和 实际上设计的破洞牛仔裤容易混淆，导致模型识别错误。
3. 后面我们可以考虑直接使用VLM模型，来识别图像中的问题。再结合实际场景，来进行优化。


# 启动页面
1. 启动后端     python app.py
2. 启动gradio前端     python gradio_app.py
    出现ffmpeg的错误，需要安装ffmpeg，然后将ffmpeg的路径添加到环境变量中。【找到models路径下的安装包，解压，配置环境变量】
3. 启动html前端
    python -m http.server 8080
    然后在浏览器 输入 http://localhost:8080/chat.html 即可访问。

# 关于 RAG 优化
1. 准备好的有一些数据，大家可以直接使用 data目录下的knowledge_base.json
2. embedding模型，大家也直接使用 models下的bge_small_zh


