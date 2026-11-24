# -*- coding: utf-8 -*-
"""
基于物品的协同过滤算法（Item-Based Collaborative Filtering）
根据用户评分矩阵计算电影之间的相似度，再为用户推荐与其高分电影相似的电影。
"""
import numpy as np

from utils.logger import get_logger

logger = get_logger("recommender.collab")


class CollaborativeRecommender:
    """基于物品的协同过滤推荐器。"""

    def __init__(self, k=10):
        self.k = k                 # 预测时参考的最相似物品数量
        self.movies = []            # list[Movie]
        self.ratings = []          # list[dict]：user_id / movie_id / score

    def fit(self, movies, ratings):
        """载入电影与评分数据并构建评分矩阵。"""
        self.movies = list(movies)
        self.ratings = list(ratings)
        self._build_matrix()
        return self

    def _build_matrix(self):
        users = sorted({r["user_id"] for r in self.ratings})
        movie_ids = [b.id for b in self.movies]
        self.user_list = users
        self.movie_list = movie_ids
        self.user_idx = {u: i for i, u in enumerate(users)}
        self.movie_idx = {bid: i for i, bid in enumerate(movie_ids)}

        self.matrix = np.zeros((len(users), len(movie_ids)))
        for r in self.ratings:
            ui = self.user_idx.get(r["user_id"])
            bi = self.movie_idx.get(r["movie_id"])
            if ui is not None and bi is not None:
                self.matrix[ui, bi] = r["score"]

    def _item_similarity(self):
        """计算物品-物品余弦相似度（评分做均值中心化，降低个人打分习惯影响）。"""
        m = self.matrix
        rated = m > 0
        row_mean = np.where(rated, m, 0).sum(axis=1) / np.maximum(rated.sum(axis=1), 1)
        centered = np.where(rated, m - row_mean[:, None], 0.0)

        norms = np.linalg.norm(centered, axis=0)
        norms[norms == 0] = 1e-9
        normed = centered / norms
        return normed.T @ normed  # shape (n_movies, n_movies)

    def predict_scores(self, user_id):
        """预测目标用户对所有未评分电影的兴趣分，返回 {movie_index: score}。"""
        if user_id not in self.user_idx:
            return {}
        sim = self._item_similarity()
        ui = self.user_idx[user_id]
        user_vec = self.matrix[ui]
        rated_idx = np.where(user_vec > 0)[0]
        if rated_idx.size == 0:
            return {}

        scores = {}
        for bi in range(len(self.movie_list)):
            if user_vec[bi] > 0:
                continue
            s = sim[bi, rated_idx]
            # 取相似度最高的 k 个邻居
            if s.size > self.k:
                top = np.argsort(s)[::-1][:self.k]
            else:
                top = np.argsort(s)[::-1]
            sims = s[top]
            neighbor_ratings = user_vec[rated_idx[top]]
            denom = np.abs(sims).sum()
            scores[bi] = float((sims * neighbor_ratings).sum() / denom) if denom > 0 else 0.0
        return scores

    def recommend(self, user_id, top_n=10):
        """为目标用户推荐未评分电影，返回 [(Movie, score)]。"""
        scores = self.predict_scores(user_id)
        if not scores:
            return []
        order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        results = []
        for bi, s in order:
            if s <= 0:
                continue
            results.append((self.movies[bi], float(s)))
            if len(results) >= top_n:
                break
        return results
