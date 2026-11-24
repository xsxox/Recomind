# -*- coding: utf-8 -*-
"""
数据库连接管理模块
封装 PyMySQL 的建连、查询与写操作，统一异常处理，供服务层调用。
"""
import pymysql
import pymysql.cursors

import config
from utils.logger import get_logger

logger = get_logger("db.connection")


def get_connection(with_database=True):
    """获取数据库连接。

    :param with_database: 是否选择目标数据库。建库阶段（数据库尚不存在）传 False。
    :return: pymysql.Connection 对象
    """
    kwargs = {
        "host": config.DB_CONFIG["host"],
        "port": config.DB_CONFIG["port"],
        "user": config.DB_CONFIG["user"],
        "password": config.DB_CONFIG["password"],
        "charset": config.DB_CONFIG["charset"],
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }
    if with_database:
        kwargs["database"] = config.DB_CONFIG["database"]
    return pymysql.connect(**kwargs)


def execute_query(sql, params=None, with_database=True):
    """执行查询，返回结果列表（每行是一个 dict）。"""
    conn = get_connection(with_database)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def execute_update(sql, params=None, with_database=True):
    """执行插入/更新/删除，返回 (受影响行数, 自增主键)。"""
    conn = get_connection(with_database)
    try:
        with conn.cursor() as cursor:
            rows = cursor.execute(sql, params)
            last_id = cursor.lastrowid
        conn.commit()
        return rows, last_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_connection():
    """检测数据库是否可用，返回 (是否可用, 提示信息)。"""
    try:
        conn = get_connection()
        conn.close()
        return True, "连接成功"
    except Exception as exc:  # noqa: BLE001
        logger.exception("数据库连接失败")
        return False, str(exc)
