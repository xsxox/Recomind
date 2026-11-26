# -*- coding: utf-8 -*-
"""
主题特征提取模块
使用 LDA（隐含狄利克雷分配）主题模型抽取隐含主题分布，用于增强内容推荐语义表达。
"""
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from nlp.text_processor import segment
from utils.logger import get_logger

logger = get_logger("nlp.topic")


class TopicExtractor:
    """LDA 主题提取器。"""

    def __init__(self, n_topics=20, max_features=2000, random_state=42):
        self.n_topics = n_topics
        self.max_features = max_features
        self.random_state = random_state
        self.vectorizer = CountVectorizer(token_pattern=r"(?u)\S+", max_features=max_features)
        self.lda = None
        self.topic_matrix = None

    def fit_transform(self, texts):
        """拟合 LDA 并返回文档-主题分布矩阵。"""
        segmented = [segment(t) for t in texts]
        if not any(segmented):
            self.topic_matrix = None
            self.lda = None
            return None
        counts = self.vectorizer.fit_transform(segmented)
        n_docs = counts.shape[0]
        if n_docs < 3 or counts.shape[1] == 0:
            self.topic_matrix = None
            self.lda = None
            return None
        n_components = max(2, min(self.n_topics, n_docs - 1))
        self.lda = LatentDirichletAllocation(
            n_components=n_components,
            random_state=self.random_state,
            max_iter=10,
            learning_method="batch",
            n_jobs=1,
        )
        self.topic_matrix = self.lda.fit_transform(counts)
        return self.topic_matrix

    def transform(self, texts):
        """将新文本转换为文档-主题分布（未命中任何词表词时置为全 0）。"""
        if isinstance(texts, str):
            texts = [texts]
        if self.lda is None:
            return None
        counts = self.vectorizer.transform([segment(t) for t in texts])
        dist = self.lda.transform(counts)
        for i in range(counts.shape[0]):
            if counts[i].nnz == 0:
                dist[i] = 0.0
        return dist

    def similarity(self, vector):
        """计算 vector 与语料中各文档主题分布的余弦相似度。"""
        if self.topic_matrix is None or vector is None:
            return np.array([])
        return cosine_similarity(vector, self.topic_matrix).flatten()