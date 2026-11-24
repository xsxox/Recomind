# -*- coding: utf-8 -*-
"""
电影服务
负责电影的增删改查与关键词检索。
"""
from db import models
from db.connection import execute_query, execute_update
from utils.logger import get_logger

logger = get_logger("services.movie")


class MovieService:
    """电影业务逻辑。"""

    def list_movies(self):
        rows = execute_query("SELECT * FROM movies ORDER BY id")
        return [models.Movie.from_dict(r) for r in rows]

    def get_movie(self, movie_id):
        rows = execute_query("SELECT * FROM movies WHERE id=%s", (movie_id,))
        return models.Movie.from_dict(rows[0]) if rows else None

    def search_movies(self, keyword):
        """按片名/导演/类型/简介模糊搜索。"""
        keyword = (keyword or "").strip()
        if not keyword:
            return self.list_movies()
        like = f"%{keyword}%"
        rows = execute_query(
            "SELECT * FROM movies WHERE title LIKE %s OR director LIKE %s "
            "OR genre LIKE %s OR description LIKE %s ORDER BY id",
            (like, like, like, like),
        )
        return [models.Movie.from_dict(r) for r in rows]

    def add_movie(self, title, director="", studio="", genre="",
                  release_year=0, description="", poster_color="#4A90D9"):
        _, movie_id = execute_update(
            "INSERT INTO movies (title, director, studio, genre, "
            "release_year, description, poster_color) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (title, director, studio, genre, release_year, description, poster_color),
        )
        return movie_id

    def update_movie(self, movie_id, title, director="", studio="", genre="",
                     release_year=0, description="", poster_color="#4A90D9"):
        rows, _ = execute_update(
            "UPDATE movies SET title=%s, director=%s, studio=%s, genre=%s, "
            "release_year=%s, description=%s, poster_color=%s WHERE id=%s",
            (title, director, studio, genre, release_year, description, poster_color, movie_id),
        )
        return rows

    def delete_movie(self, movie_id):
        return execute_update("DELETE FROM movies WHERE id=%s", (movie_id,))

    def count_movies(self):
        rows = execute_query("SELECT COUNT(*) AS c FROM movies")
        return rows[0]["c"] if rows else 0
