# -*- coding: utf-8 -*-
"""
基于用户的协同过滤算法（User-Based Collaborative Filtering）
根据用户评分向量计算用户之间的相似度，再基于相似用户的评分预测目标用户对未评分电影的兴趣。
"""
import numpy as np

from utils.logger import get_logger

logger = get_logger("recommender.usercf")


class UserCFRecommender:
    """基于用户的协同过滤推荐器。"""

    def __init__(self, k=20):
        self.k = k                   # 参与预测的相似用户数量
        self.movies = []             # list[Movie]
        self.ratings = []            # list[dict]：user_id / movie_id / score
        self.user_list = []
        self.movie_list = []
        self.user_idx = {}
        self.movie_idx = {}
        self.matrix = None           # (n_users, n_movies)
        self._user_sim = None        # (n_users, n_users)

    def fit(self, movies, ratings):
        """载入电影与评分数据并构建用户相似度矩阵。"""
        self.movies = list(movies)
        self.ratings = list(ratings)
        users = sorted({r["user_id"] for r in self.ratings})
        movie_ids = [m.id for m in self.movies]
        self.user_list = users
        self.movie_list = movie_ids
        self.user_idx = {u: i for i, u in enumerate(users)}
        self.movie_idx = {bid: i for i, bid in enumerate(movie_ids)}

        self.matrix = np.zeros((len(users), len(movie_ids)))
        for r in self.ratings:
            ui = self.user_idx.get(r["user_id"])
            mi = self.movie_idx.get(r["movie_id"])
            if ui is not None and mi is not None:
                self.matrix[ui, mi] = r["score"]
        self._user_sim = self._compute_user_similarity()
        return self

    def _compute_user_similarity(self):
        """计算用户-用户余弦相似度（评分做均值中心化）。"""
        m = self.matrix
        rated = m > 0
        row_mean = np.where(rated, m, 0).sum(axis=1) / np.maximum(rated.sum(axis=1), 1)
        centered = np.where(rated, m - row_mean[:, None], 0.0)
        norms = np.linalg.norm(centered, axis=1)
        norms[norms == 0] = 1e-9
        normed = centered / norms[:, None]
        return normed @ normed.T

    def neighbors(self, user_id, k=None):
        """返回与目标用户最相似的前 k 个用户 [(user_id, sim)]。"""
        k = k or self.k
        if user_id not in self.user_idx or self._user_sim is None:
            return []
        ui = self.user_idx[user_id]
        sims = self._user_sim[ui]
        order = np.argsort(sims)[::-1]
        out = []
        for j in order:
            if j == ui:
                continue
            if sims[j] <= 0:
                continue
            out.append((self.user_list[j], float(sims[j])))
            if len(out) >= k:
                break
        return out

    def predict_scores(self, user_id):
        """预测目标用户对所有未评分电影的兴趣分，返回 {movie_index: score}。"""
        if user_id not in self.user_idx:
            return {}
        ui = self.user_idx[user_id]
        user_vec = self.matrix[ui]
        neighbors = self.neighbors(user_id)
        if not neighbors:
            return {}

        scores = {}
        for mi in range(len(self.movie_list)):
            if user_vec[mi] > 0:
                continue
            num = 0.0
            den = 0.0
            for nuid, sim in neighbors:
                nui = self.user_idx[nuid]
                r = self.matrix[nui, mi]
                if r > 0:
                    num += sim * r
                    den += abs(sim)
            if den > 0:
                scores[mi] = float(num / den)
        return scores

    def recommend(self, user_id, top_n=10):
        """为目标用户推荐未评分电影，返回 [(Movie, score)]。"""
        scores = self.predict_scores(user_id)
        if not scores:
            return []
        order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        results = []
        for mi, s in order:
            if s <= 0:
                continue
            results.append((self.movies[mi], float(s)))
            if len(results) >= top_n:
                break
        return results
