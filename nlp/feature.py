# -*- coding: utf-8 -*-
"""
特征提取模块
基于 scikit-learn 的 TF-IDF 将文本转换为向量，并用余弦相似度衡量文本相似程度。
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from nlp.text_processor import segment
from utils.logger import get_logger

logger = get_logger("nlp.feature")


class TextFeatureExtractor:
    """TF-IDF 特征提取器。"""

    def __init__(self):
        # 文本已由 jieba 分词并用空格连接，这里按空白切分即可
        self.vectorizer = TfidfVectorizer(token_pattern=r"(?u)\S+")
        self.matrix = None  # 语料 TF-IDF 稀疏矩阵

    def fit_transform(self, texts):
        """拟合语料并返回 TF-IDF 矩阵。"""
        segmented = [segment(t) for t in texts]
        # 若语料全为空文本，返回 None，由调用方处理
        if not any(segmented):
            self.matrix = None
            return None
        self.matrix = self.vectorizer.fit_transform(segmented)
        return self.matrix

    def transform(self, texts):
        """将新文本转换为 TF-IDF 向量（需先 fit_transform）。"""
        if isinstance(texts, str):
            texts = [texts]
        return self.vectorizer.transform([segment(t) for t in texts])

    def similarity(self, vector):
        """计算 vector 与语料中每一条文本的余弦相似度，返回一维数组。"""
        if self.matrix is None:
            return []
        return cosine_similarity(vector, self.matrix).flatten()
