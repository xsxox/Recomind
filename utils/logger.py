# -*- coding: utf-8 -*-
"""
日志模块
统一配置控制台与文件日志，方便调试与记录运行状态。
"""
import logging
import sys

import config

_initialized = False


def get_logger(name="recomind"):
    """获取一个已配置的 logger。"""
    global _initialized
    logger = logging.getLogger(name)
    if _initialized:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 文件输出
    try:
        file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        # 文件日志不可用时不影响程序运行
        pass

    _initialized = True
    return logger
