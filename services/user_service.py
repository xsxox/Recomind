# -*- coding: utf-8 -*-
"""
用户服务
负责用户注册、登录、查询与删除。
"""
from db import models
from db.connection import execute_query, execute_update
from utils.logger import get_logger
from utils.security import hash_password, verify_password

logger = get_logger("services.user")


class UserService:
    """用户业务逻辑。"""

    def register(self, username, password, nickname="", gender="", age=0):
        """注册新用户，成功返回 (user_id, None)，失败返回 (None, 错误信息)。"""
        username = username.strip()
        if not username or not password:
            return None, "用户名和密码不能为空"
        if len(password) < 4:
            return None, "密码长度不能少于 4 位"

        exists = execute_query("SELECT id FROM users WHERE username=%s", (username,))
        if exists:
            return None, "用户名已存在"

        hashed = hash_password(password)
        try:
            _, user_id = execute_update(
                "INSERT INTO users (username, password, nickname, gender, age) "
                "VALUES (%s, %s, %s, %s, %s)",
                (username, hashed, nickname, gender, age),
            )
            return user_id, None
        except Exception as exc:  # noqa: BLE001
            logger.exception("注册失败")
            return None, str(exc)

    def login(self, username, password):
        """登录校验，成功返回 (User, None)，失败返回 (None, 错误信息)。"""
        rows = execute_query("SELECT * FROM users WHERE username=%s", (username.strip(),))
        if not rows:
            return None, "用户不存在"
        user = models.User.from_dict(rows[0])
        if not verify_password(password, user.password):
            return None, "密码错误"
        return user, None

    def get_user(self, user_id):
        rows = execute_query("SELECT * FROM users WHERE id=%s", (user_id,))
        return models.User.from_dict(rows[0]) if rows else None

    def list_users(self):
        rows = execute_query("SELECT * FROM users ORDER BY id")
        return [models.User.from_dict(r) for r in rows]

    def count_users(self):
        rows = execute_query("SELECT COUNT(*) AS c FROM users")
        return rows[0]["c"] if rows else 0

    def delete_user(self, user_id):
        return execute_update("DELETE FROM users WHERE id=%s", (user_id,))
