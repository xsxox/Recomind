# -*- coding: utf-8 -*-
"""
全局配置模块
集中管理数据库连接参数、项目路径与推荐算法参数，方便统一修改。

使用方法：修改本文件中的常量即可，无需改动其它代码。
"""
import os

# 项目根目录（本文件所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== 数据库配置 ====================
# 请根据本机 MySQL 实际情况修改，尤其是 password。
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "fx666",         # TODO: 改成你本机 MySQL 的密码
    "charset": "utf8mb4",
    "database": "recomind",      # 系统使用的数据库名（初始化时自动创建）
}

# ==================== TMDB 海报配置 ====================
# 在 https://www.themoviedb.org/settings/api 免费申请 API Key 后填入下方
TMDB_API_KEY = "e9912cf8b40c6b1a82bcc310258a932d"
TMDB_LANGUAGE = "zh-CN"

# ==================== 路径配置 ====================
DATA_DIR = os.path.join(BASE_DIR, "data")
STOPWORDS_FILE = os.path.join(DATA_DIR, "stopwords.txt")
LOG_FILE = os.path.join(BASE_DIR, "recomind.log")

# ==================== 推荐算法参数 ====================
CONTENT_TOP_N = 10            # 内容推荐返回条数
COLLAB_TOP_N = 10             # 协同过滤推荐返回条数
HYBRID_TOP_N = 12             # 混合推荐返回条数
HYBRID_CONTENT_WEIGHT = 0.2   # 混合推荐中内容推荐的权重
HYBRID_ITEM_CF_WEIGHT = 0.5   # 混合推荐中物品协同过滤的权重
HYBRID_USER_CF_WEIGHT = 0.3   # 混合推荐中用户协同过滤的权重
TOPIC_WEIGHT = 0.2            # 内容相似度中 LDA 主题的权重（TF-IDF 权重为 1-TOPIC_WEIGHT）
LDA_TOPICS = 20               # LDA 主题数量
MMR_LAMBDA = 0.7              # MMR 重排的相关度权重（多样性权重为 1-MMR_LAMBDA）
EVAL_TOP_K = 10               # 评估时使用的 Top-K

# ==================== 界面参数 ====================
APP_NAME = "Recomind 智能推荐系统"
APP_VERSION = "1.0.0"
