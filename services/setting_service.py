# -*- coding: utf-8 -*-
"""
用户设置服务
负责用户推荐偏好（偏好类型、Top-N、算法开关）的读取与保存。
"""
from db.connection import execute_query, execute_update
from utils.logger import get_logger

logger = get_logger("services.setting")

DEFAULTS = {
    "preferred_genres": "",
    "recommend_top_n": 12,
    "enable_content": True,
    "enable_item_cf": True,
    "enable_user_cf": True,
}


class SettingService:
    """用户设置业务逻辑。"""

    def get_settings(self, user_id):
        rows = execute_query("SELECT * FROM user_settings WHERE user_id=%s", (user_id,))
        if not rows:
            return dict(DEFAULTS)
        r = rows[0]
        return {
            "preferred_genres": r.get("preferred_genres") or "",
            "recommend_top_n": r.get("recommend_top_n") or DEFAULTS["recommend_top_n"],
            "enable_content": bool(r.get("enable_content", 1)),
            "enable_item_cf": bool(r.get("enable_item_cf", 1)),
            "enable_user_cf": bool(r.get("enable_user_cf", 1)),
        }

    def save_settings(self, user_id, preferred_genres="", recommend_top_n=12,
                      enable_content=True, enable_item_cf=True, enable_user_cf=True):
        params = (
            preferred_genres.strip(), recommend_top_n,
            int(bool(enable_content)), int(bool(enable_item_cf)), int(bool(enable_user_cf)),
        )
        exists = execute_query("SELECT user_id FROM user_settings WHERE user_id=%s", (user_id,))
        if exists:
            execute_update(
                "UPDATE user_settings SET preferred_genres=%s, recommend_top_n=%s, "
                "enable_content=%s, enable_item_cf=%s, enable_user_cf=%s WHERE user_id=%s",
                params + (user_id,),
            )
        else:
            execute_update(
                "INSERT INTO user_settings (user_id, preferred_genres, recommend_top_n, "
                "enable_content, enable_item_cf, enable_user_cf) VALUES (%s,%s,%s,%s,%s,%s)",
                (user_id,) + params,
            )
