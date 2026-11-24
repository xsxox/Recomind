-- ============================================================
-- Recomind 电影智能推荐系统 - 数据库初始化脚本
-- 使用方法（二选一）：
--   1) 命令行执行：mysql -u root -p < init_database.sql
--   2) 双击 init_database.bat
-- 说明：程序启动时也会自动建库建表，本脚本用于手动初始化或答辩演示。
-- ============================================================

CREATE DATABASE IF NOT EXISTS recomind
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE recomind;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username      VARCHAR(50)  NOT NULL UNIQUE        COMMENT '登录用户名',
    password      VARCHAR(255) NOT NULL               COMMENT '密码哈希',
    nickname      VARCHAR(50)  DEFAULT NULL           COMMENT '昵称',
    gender        VARCHAR(10)  DEFAULT NULL           COMMENT '性别',
    age           INT          DEFAULT NULL           COMMENT '年龄',
    register_time DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 电影表
CREATE TABLE IF NOT EXISTS movies (
    id           INT AUTO_INCREMENT PRIMARY KEY  COMMENT '电影ID',
    title        VARCHAR(200) NOT NULL           COMMENT '片名',
    director     VARCHAR(100) DEFAULT NULL       COMMENT '导演',
    studio       VARCHAR(100) DEFAULT NULL       COMMENT '制片/发行公司',
    genre        VARCHAR(50)  DEFAULT NULL       COMMENT '类型',
    release_year INT          DEFAULT NULL       COMMENT '上映年份',
    description  TEXT                            COMMENT '剧情简介（用于NLP特征提取）',
    poster_color VARCHAR(20)  DEFAULT '#4A90D9'  COMMENT '海报占位颜色'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='电影表';

-- 评分表
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

-- 浏览历史表
CREATE TABLE IF NOT EXISTS browse_history (
    id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    user_id     INT  NOT NULL                   COMMENT '用户ID',
    movie_id    INT  NOT NULL                   COMMENT '电影ID',
    browse_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
    CONSTRAINT fk_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_history_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='浏览历史表';
