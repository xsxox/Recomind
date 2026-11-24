# -*- coding: utf-8 -*-
"""
数据库初始化模块
负责：1) 创建数据库；2) 检测并清理旧版图书表；3) 创建电影相关数据表。
可直接运行本文件，也可被主程序在启动时调用。
"""
import config
from db import models
from db.connection import execute_query, execute_update, get_connection
from utils.logger import get_logger

logger = get_logger("db.init")


def _table_exists(table_name):
    rows = execute_query(
        "SELECT COUNT(*) AS c FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
        (config.DB_CONFIG["database"], table_name),
    )
    return bool(rows and rows[0]["c"])


def create_database_if_not_exists():
    """若数据库不存在则创建（utf8mb4 字符集，支持中文）。"""
    conn = get_connection(with_database=False)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS `{}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(
                    config.DB_CONFIG["database"]
                )
            )
        conn.commit()
        logger.info("数据库 %s 已就绪", config.DB_CONFIG["database"])
    finally:
        conn.close()


def migrate_from_books():
    """检测旧版图书表：若存在 books 表，则清理相关表以切换到电影表（保留 users）。"""
    if not _table_exists("books"):
        return
    execute_update("DROP TABLE IF EXISTS browse_history")
    execute_update("DROP TABLE IF EXISTS ratings")
    execute_update("DROP TABLE IF EXISTS books")
    logger.info("检测到旧版图书表，已清理并切换到电影数据表")


def create_tables():
    """按依赖顺序创建全部数据表。"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for statement in models.ALL_TABLES_SQL:
                cursor.execute(statement)
        conn.commit()
        logger.info("数据表已创建/校验完成")
    finally:
        conn.close()


def _column_exists(table, column):
    rows = execute_query(
        "SELECT COUNT(*) AS c FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        (config.DB_CONFIG["database"], table, column),
    )
    return bool(rows and rows[0]["c"])


def ensure_movie_columns():
    """为旧版 movies 表补充 TMDB 字段（幂等）。"""
    if not _column_exists("movies", "tmdb_id"):
        execute_update(
            "ALTER TABLE movies ADD COLUMN tmdb_id INT DEFAULT NULL COMMENT 'TMDB 电影ID'"
        )
        try:
            execute_update("ALTER TABLE movies ADD UNIQUE KEY uk_tmdb_id (tmdb_id)")
        except Exception:  # noqa: BLE001
            pass
        logger.info("已为 movies 表添加 tmdb_id 字段")
    if not _column_exists("movies", "vote_average"):
        execute_update(
            "ALTER TABLE movies ADD COLUMN vote_average DOUBLE DEFAULT 0 COMMENT 'TMDB 平均评分'"
        )
    if not _column_exists("movies", "vote_count"):
        execute_update(
            "ALTER TABLE movies ADD COLUMN vote_count INT DEFAULT 0 COMMENT 'TMDB 评分人数'"
        )
    if not _column_exists("movies", "keywords"):
        execute_update(
            "ALTER TABLE movies ADD COLUMN keywords VARCHAR(500) DEFAULT NULL COMMENT 'TMDB 关键词'"
        )


def ensure_poster_url_column():
    """为旧版 movies 表补充 poster_url 字段（幂等）。"""
    rows = execute_query(
        "SELECT COUNT(*) AS c FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='movies' AND COLUMN_NAME='poster_url'",
        (config.DB_CONFIG["database"],),
    )
    if not rows or rows[0]["c"] == 0:
        execute_update(
            "ALTER TABLE movies ADD COLUMN poster_url VARCHAR(500) DEFAULT NULL "
            "COMMENT '在线海报地址'"
        )
        logger.info("已为 movies 表添加 poster_url 字段")


def init_database():
    """初始化数据库与数据表（含旧版迁移）。"""
    create_database_if_not_exists()
    migrate_from_books()
    create_tables()
    ensure_poster_url_column()
    ensure_movie_columns()


if __name__ == "__main__":
    try:
        init_database()
        print("数据库初始化成功！")
    except Exception as exc:  # noqa: BLE001
        logger.exception("数据库初始化失败")
        print("数据库初始化失败：", exc)
