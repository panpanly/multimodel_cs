import json
import os
import logging
import chromadb
from chromadb.config import Settings

from src.multimodel_cs.config.setting import settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ProductRAG:
    def __init__(self,kb_path:str = str(settings.KB_PATH)):
        """
        初始化产品知识库RAG系统
        :param kb_path:
        """
        # 加载嵌入模型
        self.encoder = SentenceTransformer(str(settings.EMBEDDING_MODEL_PATH))
        # 初始化chromaDB客户端，allow_reset=True 允许重置数据库  anonymized_telemetry=False 禁用匿名遥测
        self.client = chromadb.Client(Settings(allow_reset=True,anonymized_telemetry=False))
        # 获取或新建向量知识库
        self.collection = self.client.get_or_create_collection(name="product_kb")
        if self.collection.count() == 0 and os.path.exists(kb_path):
            # 加载知识库
            self._load_knowledge_base(kb_path)

    def _load_knowledge_base(self,kb_path:str):
        """
        从JSON文件中加载知识库
        :param kb_path:
        :return:
        """
        with open(kb_path,'r',encoding='utf-8') as f:
            kb_data = json.load(f)
        docs = []
        metas = []
        ids = []
        embeddings = []
        # 类似于项目一中，使用langchain框架进行文件加载，分块、埃安如、存储的过程
        for idx,item in enumerate(kb_data):
            text = f"{item['title']}\n{item['content']}"
            docs.append(text)
            metas.append({"source":item['title']})
            ids.append(str(idx))
            embeddings.append(self.encoder.encode(text).tolist())
        self.collection.add(embeddings=embeddings,documents=docs,metadatas=metas,ids=ids)

    def retrieve(self,query:str,top_k:int = 2):
        """
        检索最相似的文档
        :param query: 文本
        :param top_k: 返回k条数据
        :return:
        """
        if self.collection.count() == 0:
            return ""
        query_embedding = self.encoder.encode(query).tolist()
        results = self.collection.query(query_embedding=[query_embedding],n_results=top_k)
        docs = results.get("documents",[[]])[0]
        return "\n".join(docs) if docs else ""



