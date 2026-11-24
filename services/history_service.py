# -*- coding: utf-8 -*-
"""
浏览历史服务
记录用户浏览电影的行为，用于冷启动阶段的推荐兜底。
"""
from db.connection import execute_query, execute_update
from utils.logger import get_logger

logger = get_logger("services.history")


class HistoryService:
    """浏览历史业务逻辑。"""

    def record(self, user_id, movie_id):
        """记录一次浏览。"""
        return execute_update(
            "INSERT INTO browse_history (user_id, movie_id) VALUES (%s, %s)",
            (user_id, movie_id),
        )

    def get_user_history(self, user_id, limit=20):
        """返回用户最近浏览记录（按时间倒序）。"""
        rows = execute_query(
            "SELECT * FROM browse_history WHERE user_id=%s "
            "ORDER BY browse_time DESC, id DESC LIMIT %s",
            (user_id, limit),
        )
        return rows

    def clear_user_history(self, user_id):
        return execute_update("DELETE FROM browse_history WHERE user_id=%s", (user_id,))

    def count_history(self):
        rows = execute_query("SELECT COUNT(*) AS c FROM browse_history")
        return rows[0]["c"] if rows else 0
