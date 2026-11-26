# -*- coding: utf-8 -*-
"""
全局配置模块 (v2.0 升级版)
集中管理数据库连接参数、项目路径与推荐算法参数，方便统一修改。

新增配置项：
  - SVD 矩阵分解参数
  - 语义嵌入权重
  - 情感分析开关
  - 评估参数
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

# 混合推荐各路权重（四路：内容+物品CF+用户CF+SVD）
HYBRID_CONTENT_WEIGHT = 0.20   # 内容推荐权重
HYBRID_ITEM_CF_WEIGHT = 0.30   # 物品协同过滤权重
HYBRID_USER_CF_WEIGHT = 0.25   # 用户协同过滤权重
HYBRID_SVD_WEIGHT = 0.25       # SVD 矩阵分解权重（新增）

# 内容特征权重（三路：TF-IDF + LDA + 语义嵌入）
TFIDF_WEIGHT = 0.30           # TF-IDF 关键词权重
TOPIC_WEIGHT = 0.15           # LDA 主题权重（原 TOPIC_WEIGHT，降低以让位语义嵌入）
EMBED_WEIGHT = 0.55           # 语义嵌入权重（新增，Sentence-BERT / LSA）

# NLP 参数
LDA_TOPICS = 20               # LDA 主题数量
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # 语义嵌入模型名（新增）

# SVD 矩阵分解参数（新增）
SVD_FACTORS = 50              # 隐因子维度
SVD_ITER = 10                 # SVD 迭代次数

# 重排参数
MMR_LAMBDA = 0.7              # MMR 重排的相关度权重（多样性权重为 1-MMR_LAMBDA）

# 评估参数
EVAL_TOP_K = 10               # 评估时使用的 Top-K
EVAL_RATIO = 0.2              # 留出集比例
EVAL_SEED = 42                # 随机种子

# ==================== 界面参数 ====================
APP_NAME = "Recomind 智能推荐系统"
APP_VERSION = "2.0.0"         # 版本升级至 2.0

