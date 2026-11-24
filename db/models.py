# -*- coding: utf-8 -*-
"""
数据模型与建表语句模块
定义系统所需的数据库表结构（DDL）以及对应的数据实体类。
"""
from dataclasses import dataclass, field
from datetime import datetime


# ==================== 建表语句（按外键依赖顺序排列） ====================

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username      VARCHAR(50)  NOT NULL UNIQUE        COMMENT '登录用户名',
    password      VARCHAR(255) NOT NULL               COMMENT '密码哈希',
    nickname      VARCHAR(50)  DEFAULT NULL           COMMENT '昵称',
    gender        VARCHAR(10)  DEFAULT NULL           COMMENT '性别',
    age           INT          DEFAULT NULL           COMMENT '年龄',
    register_time DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
"""

CREATE_MOVIES_TABLE = """
CREATE TABLE IF NOT EXISTS movies (
    id           INT AUTO_INCREMENT PRIMARY KEY  COMMENT '电影ID',
    title        VARCHAR(200) NOT NULL           COMMENT '片名',
    director     VARCHAR(100) DEFAULT NULL       COMMENT '导演',
    studio       VARCHAR(100) DEFAULT NULL       COMMENT '制片/发行公司',
    genre        VARCHAR(50)  DEFAULT NULL       COMMENT '类型',
    release_year INT          DEFAULT NULL       COMMENT '上映年份',
    description  TEXT                            COMMENT '剧情简介（用于NLP特征提取）',
    poster_color VARCHAR(20)  DEFAULT '#4A90D9'  COMMENT '海报占位颜色',
    poster_url   VARCHAR(500) DEFAULT NULL       COMMENT '在线海报地址',
    keywords     VARCHAR(500) DEFAULT NULL       COMMENT 'TMDB 关键词',
    tmdb_id      INT          DEFAULT NULL       COMMENT 'TMDB 电影ID',
    vote_average DOUBLE       DEFAULT 0          COMMENT 'TMDB 平均评分',
    vote_count   INT          DEFAULT 0          COMMENT 'TMDB 评分人数',
    UNIQUE KEY uk_tmdb_id (tmdb_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='电影表';
"""

CREATE_RATINGS_TABLE = """
CREATE TABLE IF NOT EXISTS ratings (
    id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '评分ID',
    user_id     INT  NOT NULL                   COMMENT '用户ID',
    movie_id    INT  NOT NULL                   COMMENT '电影ID',
    score       INT  NOT NULL                   COMMENT '评分(1-5)',
    comment     TEXT                            COMMENT '评语',
    rating_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '评分时间',
    UNIQUE KEY uk_user_movie (user_id, movie_id),
    CONSTRAINT fk_rating_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rating_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评分表';
"""

CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS browse_history (
    id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    user_id     INT  NOT NULL                   COMMENT '用户ID',
    movie_id    INT  NOT NULL                   COMMENT '电影ID',
    browse_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
    CONSTRAINT fk_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_history_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='浏览历史表';
"""

CREATE_REVIEWS_TABLE = """
CREATE TABLE IF NOT EXISTS reviews (
    id         INT AUTO_INCREMENT PRIMARY KEY COMMENT '影评ID',
    movie_id   INT NOT NULL                   COMMENT '电影ID',
    author     VARCHAR(100) DEFAULT NULL      COMMENT '作者',
    content    TEXT                           COMMENT '影评内容',
    rating     DOUBLE DEFAULT NULL            COMMENT '作者评分',
    created_at VARCHAR(50) DEFAULT NULL       COMMENT '发布时间',
    CONSTRAINT fk_review_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='影评表';
"""

CREATE_USER_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS user_settings (
    user_id          INT PRIMARY KEY COMMENT '用户ID',
    preferred_genres VARCHAR(200) DEFAULT '' COMMENT '偏好类型（逗号分隔）',
    recommend_top_n  INT DEFAULT 12 COMMENT '推荐条数',
    enable_content   TINYINT DEFAULT 1 COMMENT '启用内容推荐',
    enable_item_cf   TINYINT DEFAULT 1 COMMENT '启用物品协同过滤',
    enable_user_cf   TINYINT DEFAULT 1 COMMENT '启用用户协同过滤',
    CONSTRAINT fk_setting_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户设置表';
"""

# 按依赖顺序组织，供初始化脚本依次执行
ALL_TABLES_SQL = [
    CREATE_USERS_TABLE,
    CREATE_MOVIES_TABLE,
    CREATE_RATINGS_TABLE,
    CREATE_HISTORY_TABLE,
    CREATE_REVIEWS_TABLE,
    CREATE_USER_SETTINGS_TABLE,
]


# ==================== 数据实体类 ====================

@dataclass
class User:
    """用户实体。"""
    id: int = 0
    username: str = ""
    password: str = ""
    nickname: str = ""
    gender: str = ""
    age: int = 0
    register_time: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, row: dict) -> "User":
        return cls(
            id=row.get("id", 0),
            username=row.get("username", ""),
            password=row.get("password", ""),
            nickname=row.get("nickname") or "",
            gender=row.get("gender") or "",
            age=row.get("age") or 0,
            register_time=row.get("register_time") or datetime.now(),
        )


@dataclass
class Movie:
    """电影实体。"""
    id: int = 0
    title: str = ""
    director: str = ""
    studio: str = ""
    genre: str = ""
    release_year: int = 0
    description: str = ""
    poster_color: str = "#4A90D9"
    poster_url: str = ""
    keywords: str = ""
    tmdb_id: int = 0
    vote_average: float = 0.0
    vote_count: int = 0

    @classmethod
    def from_dict(cls, row: dict) -> "Movie":
        return cls(
            id=row.get("id", 0),
            title=row.get("title", ""),
            director=row.get("director") or "",
            studio=row.get("studio") or "",
            genre=row.get("genre") or "",
            release_year=row.get("release_year") or 0,
            description=row.get("description") or "",
            poster_color=row.get("poster_color") or "#4A90D9",
            poster_url=row.get("poster_url") or "",
            keywords=row.get("keywords") or "",
            tmdb_id=row.get("tmdb_id") or 0,
            vote_average=float(row.get("vote_average") or 0),
            vote_count=int(row.get("vote_count") or 0),
        )

    def text(self) -> str:
        """拼接用于 NLP 特征提取的文本。"""
        return " ".join(filter(None, [self.title, self.director, self.genre, self.keywords, self.description]))


@dataclass
class Rating:
    """评分实体。"""
    id: int = 0
    user_id: int = 0
    movie_id: int = 0
    score: int = 0
    comment: str = ""
    rating_time: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, row: dict) -> "Rating":
        return cls(
            id=row.get("id", 0),
            user_id=row.get("user_id", 0),
            movie_id=row.get("movie_id", 0),
            score=row.get("score", 0),
            comment=row.get("comment") or "",
            rating_time=row.get("rating_time") or datetime.now(),
        )


@dataclass
class Review:
    """影评实体（来自 TMDB）。"""
    id: int = 0
    movie_id: int = 0
    author: str = ""
    content: str = ""
    rating: float = 0.0
    created_at: str = ""

    @classmethod
    def from_dict(cls, row: dict) -> "Review":
        return cls(
            id=row.get("id", 0),
            movie_id=row.get("movie_id", 0),
            author=row.get("author") or "匿名",
            content=row.get("content") or "",
            rating=float(row.get("rating") or 0),
            created_at=row.get("created_at") or "",
        )
