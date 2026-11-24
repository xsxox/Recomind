# -*- coding: utf-8 -*-
"""
示例数据导入脚本
将 data/sample_data.py 中的电影、用户与评分写入数据库。
可直接运行：python -m data.seed_data
"""
from data.sample_data import CATEGORY_COLORS, DEFAULT_COLOR, MOVIES, RATINGS, USERS
from db.connection import execute_query, execute_update
from db.init_db import init_database
from utils.logger import get_logger
from utils.security import hash_password

logger = get_logger("data.seed")


def _clear_all():
    """清空业务数据（按外键依赖顺序删除）。"""
    execute_update("DELETE FROM browse_history")
    execute_update("DELETE FROM ratings")
    execute_update("DELETE FROM movies")
    execute_update("DELETE FROM users")


def seed(force=False):
    """导入示例数据。force=True 时先清空再导入。"""
    init_database()

    count = execute_query("SELECT COUNT(*) AS c FROM movies")[0]["c"]
    if count > 0 and not force:
        logger.info("数据库中已有 %s 部电影，跳过导入（如需重置请使用 force=True）", count)
        return

    if force:
        _clear_all()
        logger.info("已清空旧数据")

    # 1. 导入电影
    title_to_id = {}
    for m in MOVIES:
        color = CATEGORY_COLORS.get(m["genre"], DEFAULT_COLOR)
        _, mid = execute_update(
            "INSERT INTO movies (title, director, studio, genre, release_year, description, poster_color) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (m["title"], m["director"], m["studio"], m["genre"], m["year"], m["desc"], color),
        )
        title_to_id[m["title"]] = mid

    # 2. 导入用户（已存在的用户复用，不重复插入）
    username_to_id = {}
    for u in USERS:
        existing = execute_query("SELECT id FROM users WHERE username=%s", (u["username"],))
        if existing:
            username_to_id[u["username"]] = existing[0]["id"]
            continue
        _, uid = execute_update(
            "INSERT INTO users (username, password, nickname, gender, age) VALUES (%s, %s, %s, %s, %s)",
            (u["username"], hash_password(u["password"]), u["nickname"], u["gender"], u["age"]),
        )
        username_to_id[u["username"]] = uid

    # 3. 导入评分
    for username, title, score, comment in RATINGS:
        uid = username_to_id.get(username)
        mid = title_to_id.get(title)
        if uid and mid:
            execute_update(
                "INSERT INTO ratings (user_id, movie_id, score, comment) VALUES (%s, %s, %s, %s)",
                (uid, mid, score, comment),
            )

    logger.info("示例数据导入完成：电影 %s 部，用户 %s 人，评分 %s 条",
                len(MOVIES), len(USERS), len(RATINGS))
    return True


if __name__ == "__main__":
    try:
        seed(force=True)
        print("示例数据导入成功！")
    except Exception as exc:  # noqa: BLE001
        logger.exception("示例数据导入失败")
        print("导入失败：", exc)
