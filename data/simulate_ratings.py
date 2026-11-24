# -*- coding: utf-8 -*-
"""
模拟用户评分生成
TMDB 不提供用户级评分，为演示协同过滤，按“类型偏好 + 少量跨类型”的规则生成较稠密的评分，
使不同用户之间存在口味重叠，从而让协同过滤与内容推荐能够产生有效信号。
可直接运行：python -m data.simulate_ratings
"""
import random

from db.connection import execute_query, execute_update
from utils.logger import get_logger

logger = get_logger("data.simulate")

# 演示用户的类型偏好
PREFERENCES = {
    "alice": {"科幻", "动作", "冒险"},   # 大片控
    "bob":   {"科幻", "悬疑", "惊悚"},   # 科幻悬疑控
    "carol": {"剧情", "爱情", "家庭"},   # 文艺情感
    "dave":  {"剧情", "历史", "战争"},   # 历史剧情
    "erin":  {"动作", "犯罪", "惊悚"},   # 动作犯罪
    "frank": {"喜剧", "动画", "奇幻"},   # 合家欢
    "admin": {"科幻", "剧情"},           # 综合
}


def simulate_ratings(seed=42):
    """清空并重新生成模拟评分，返回评分条数。"""
    rng = random.Random(seed)
    users = {r["username"]: r["id"] for r in execute_query("SELECT id, username FROM users")}
    movies = execute_query("SELECT id, genre, vote_average FROM movies")

    execute_update("DELETE FROM ratings")
    count = 0
    for username, prefs in PREFERENCES.items():
        uid = users.get(username)
        if not uid:
            continue
        for movie in movies:
            genres = set((movie["genre"] or "").split("/"))
            vote = movie["vote_average"] or 0
            if genres & prefs:
                score = 5 if vote >= 7.5 else 4
                comment = "非常喜欢，强烈推荐。"
            else:
                # 少量非偏好电影，制造负样本与交叉重叠
                if rng.random() > 0.25:
                    continue
                score = 3 if vote >= 7.0 else 2
                comment = "随便看看。"
            execute_update(
                "INSERT INTO ratings (user_id, movie_id, score, comment) VALUES (%s,%s,%s,%s)",
                (uid, movie["id"], score, comment),
            )
            count += 1
    logger.info("模拟评分生成完成：%s 条", count)
    return count


if __name__ == "__main__":
    n = simulate_ratings()
    total = execute_query("SELECT COUNT(*) c FROM ratings")[0]["c"]
    print(f"已生成模拟评分 {n} 条，当前共 {total} 条")
