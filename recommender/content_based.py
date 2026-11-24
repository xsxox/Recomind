# -*- coding: utf-8 -*-
"""
基于内容的推荐算法（Content-Based Filtering）
利用电影文本（片名/导演/类型/简介）的 TF-IDF 向量与余弦相似度，
推荐与目标电影或目标文本最相似的电影。
"""
from nlp.feature import TextFeatureExtractor
from utils.logger import get_logger

logger = get_logger("recommender.content")


class ContentBasedRecommender:
    """基于内容的推荐器。"""

    def __init__(self):
        self.extractor = TextFeatureExtractor()
        self.movies = []          # list[Movie]
        self.id_to_index = {}    # movie_id -> 矩阵行下标
        self.matrix = None

    def fit(self, movies):
        """根据电影列表构建 TF-IDF 特征矩阵。"""
        self.movies = list(movies)
        self.id_to_index = {b.id: i for i, b in enumerate(self.movies)}
        texts = [b.text() for b in self.movies]
        self.matrix = self.extractor.fit_transform(texts)
        return self

    # ---------- 对外接口 ----------

    def recommend_by_movie(self, movie_id, top_n=10, exclude_ids=None):
        """返回与指定电影内容最相似的电影列表 [(Movie, score)]。"""
        if self.matrix is None or movie_id not in self.id_to_index:
            return []
        exclude = set(exclude_ids or []) | {movie_id}
        idx = self.id_to_index[movie_id]
        sims = self.extractor.similarity(self.matrix[idx])
        return self._top_results(sims, top_n, exclude)

    def recommend_by_movies(self, movie_ids, top_n=10, exclude_ids=None):
        """根据多部电影（如用户偏好的影片）聚合兴趣向量进行推荐。"""
        if self.matrix is None:
            return []
        indices = [self.id_to_index[bid] for bid in movie_ids if bid in self.id_to_index]
        if not indices:
            return []
        exclude = set(exclude_ids or []) | set(movie_ids)

        # 将多部电影的向量相加作为用户兴趣向量（余弦相似度对缩放不敏感）
        interest = self.matrix[indices[0]]
        for i in indices[1:]:
            interest = interest + self.matrix[i]
        sims = self.extractor.similarity(interest)
        return self._top_results(sims, top_n, exclude)

    def recommend_by_text(self, text, top_n=10, exclude_ids=None):
        """根据一段文本（如搜索关键词/偏好描述）推荐相似电影。"""
        if self.matrix is None or not text:
            return []
        exclude = set(exclude_ids or [])
        vec = self.extractor.transform([text])
        sims = self.extractor.similarity(vec)
        return self._top_results(sims, top_n, exclude)

    # ---------- 内部工具 ----------

    def _top_results(self, sims, top_n, exclude_ids):
        """按相似度降序，过滤排除项，返回前 top_n 条。"""
        if len(sims) == 0:
            return []
        order = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)
        results = []
        for i in order:
            movie = self.movies[i]
            if movie.id in exclude_ids:
                continue
            if sims[i] <= 0:  # 无相似性的结果不推荐
                continue
            results.append((movie, float(sims[i])))
            if len(results) >= top_n:
                break
        return results
