# -*- coding: utf-8 -*-
"""
评分服务
负责评分的添加/修改、查询，以及基于评分的统计（平均分、热门电影）。
"""
from db import models
from db.connection import execute_query, execute_update
from utils.logger import get_logger

logger = get_logger("services.rating")


class RatingService:
    """评分业务逻辑。"""

    def add_or_update_rating(self, user_id, movie_id, score, comment=""):
        """新增或更新评分（同一用户对同一部电影仅保留一条）。"""
        existing = self.get_user_rating(user_id, movie_id)
        if existing:
            rows, _ = execute_update(
                "UPDATE ratings SET score=%s, comment=%s, rating_time=NOW() "
                "WHERE user_id=%s AND movie_id=%s",
                (score, comment, user_id, movie_id),
            )
            return rows
        rows, _ = execute_update(
            "INSERT INTO ratings (user_id, movie_id, score, comment) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, movie_id, score, comment),
        )
        return rows

    def get_user_rating(self, user_id, movie_id):
        rows = execute_query(
            "SELECT * FROM ratings WHERE user_id=%s AND movie_id=%s",
            (user_id, movie_id),
        )
        return models.Rating.from_dict(rows[0]) if rows else None

    def get_user_ratings(self, user_id):
        rows = execute_query("SELECT * FROM ratings WHERE user_id=%s ORDER BY rating_time DESC", (user_id,))
        return [models.Rating.from_dict(r) for r in rows]

    def get_all_ratings(self):
        """返回全部评分（供协同过滤使用）。"""
        rows = execute_query("SELECT user_id, movie_id, score FROM ratings")
        return [{"user_id": r["user_id"], "movie_id": r["movie_id"], "score": r["score"]} for r in rows]

    def get_movie_avg_score(self, movie_id):
        """返回 (平均分, 评分人数)。"""
        rows = execute_query(
            "SELECT AVG(score) AS avg_score, COUNT(*) AS cnt FROM ratings WHERE movie_id=%s",
            (movie_id,),
        )
        if rows and rows[0]["cnt"]:
            return round(float(rows[0]["avg_score"]), 1), rows[0]["cnt"]
        return 0.0, 0

    def get_popular_movies(self, top_n=10):
        """按平均分与评分人数返回热门电影 [(movie_id, avg_score, count)]。"""
        rows = execute_query(
            "SELECT movie_id, AVG(score) AS avg_score, COUNT(*) AS cnt "
            "FROM ratings GROUP BY movie_id "
            "ORDER BY avg_score DESC, cnt DESC LIMIT %s",
            (top_n,),
        )
        return [(r["movie_id"], round(float(r["avg_score"]), 1), r["cnt"]) for r in rows]

    def list_ratings_with_names(self):
        """联表查询评分详情（含用户名与片名），供管理页展示。"""
        rows = execute_query(
            "SELECT r.id, u.username, b.title, r.score, r.comment, r.rating_time "
            "FROM ratings r "
            "JOIN users u ON r.user_id = u.id "
            "JOIN movies b ON r.movie_id = b.id "
            "ORDER BY r.rating_time DESC, r.id DESC"
        )
        return rows

    def delete_rating(self, rating_id):
        return execute_update("DELETE FROM ratings WHERE id=%s", (rating_id,))

    def count_ratings(self):
        rows = execute_query("SELECT COUNT(*) AS c FROM ratings")
        return rows[0]["c"] if rows else 0
