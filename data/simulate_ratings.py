# -*- coding: utf-8 -*-
"""
模拟演示用户评分生成
结合类型偏好、TMDB 贝叶斯口碑与影评均分，采用单连接批量写入（executemany），
同时保留真实注册用户的评分数据。
"""
import random
import re

from db.connection import execute_query, get_connection
from utils.logger import get_logger

logger = get_logger("data.simulate")

PREFERENCES = {
    "alice": {"科幻", "动作", "冒险"},
    "bob":   {"科幻", "悬疑", "惊悚"},
    "carol": {"剧情", "爱情", "家庭"},
    "dave":  {"剧情", "历史", "战争"},
    "erin":  {"动作", "犯罪", "惊悚"},
    "frank": {"喜剧", "动画", "奇幻"},
    "admin": {"科幻", "剧情"},
}


def simulate_ratings(seed=42):
    """基于 TMDB 评价与偏好批量生成演示用户评分，保留真实注册用户数据。"""
    rng = random.Random(seed)
    users = {r["username"]: r["id"] for r in execute_query("SELECT id, username FROM users")}
    movies = execute_query("SELECT id, genre, vote_average, vote_count FROM movies")
    review_rows = execute_query(
        "SELECT movie_id, AVG(rating) AS avg_r FROM reviews WHERE rating > 0 GROUP BY movie_id"
    )
    review_avg = {r["movie_id"]: float(r["avg_r"]) for r in review_rows}

    valid_votes = [m["vote_average"] for m in movies if (m.get("vote_count") or 0) > 0]
    c_mean = sum(valid_votes) / len(valid_votes) if valid_votes else 6.8
    m_prior = 500.0

    # 随片库规模动态控制抽样密度，保证每个演示账号约 80~140 条有效评分
    n_movies = max(1, len(movies))
    pos_rate = min(1.0, 260.0 / n_movies) if n_movies > 300 else 1.0
    neg_rate = min(0.25, 70.0 / n_movies) if n_movies > 300 else 0.25

    rows_to_insert = []
    for username, prefs in PREFERENCES.items():
        uid = users.get(username)
        if not uid:
            continue
        for movie in movies:
            genres = {g.strip() for g in re.split(r"[/,、，\s]+", movie["genre"] or "") if g.strip()}
            v = movie.get("vote_count") or 0
            r = movie.get("vote_average") or c_mean
            wr = (v / (v + m_prior)) * r + (m_prior / (v + m_prior)) * c_mean
            if movie["id"] in review_avg:
                wr = 0.75 * wr + 0.25 * review_avg[movie["id"]]

            overlap = len(genres & prefs)
            if overlap > 0:
                if rng.random() > pos_rate:
                    continue
                if wr >= 7.7 or (overlap >= 2 and wr >= 7.2):
                    score = 5
                    comment = "题材完全对胃口，TMDB 口碑名副其实！"
                elif wr >= 6.4:
                    score = 4
                    comment = "整体制作不错，值得一看。"
                else:
                    score = 3
                    comment = "题材喜欢，但成片中规中矩。"
            else:
                if rng.random() > neg_rate:
                    continue
                if wr >= 8.2:
                    score = 4
                    comment = "虽然不是常看类型，但口碑极佳。"
                elif wr >= 6.6:
                    score = 3
                    comment = "随便看看，还算合格。"
                elif wr >= 5.5:
                    score = 2
                    comment = "不太合口味。"
                else:
                    score = 1
                    comment = "评价与体验都不太理想。"

            rows_to_insert.append((uid, movie["id"], score, comment))

    demo_ids = [users[u] for u in PREFERENCES if u in users]
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if demo_ids:
                ph = ",".join(["%s"] * len(demo_ids))
                cursor.execute(f"DELETE FROM ratings WHERE user_id IN ({ph})", tuple(demo_ids))
            if rows_to_insert:
                cursor.executemany(
                    "INSERT INTO ratings (user_id, movie_id, score, comment) VALUES (%s,%s,%s,%s)",
                    rows_to_insert,
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    count = len(rows_to_insert)
    logger.info("模拟评分批量生成完成：%s 条", count)
    return count


if __name__ == "__main__":
    n = simulate_ratings()
    total = execute_query("SELECT COUNT(*) c FROM ratings")[0]["c"]
    print(f"已生成模拟评分 {n} 条，当前共 {total} 条")