# -*- coding: utf-8 -*-
"""
个人观影空间 (v3.0 全面升级版)
================================
彻底重塑个人页面，告别干瘪列表：
  1. 顶部个人名片 Hero 横幅：发光头像 + AI 自动计算“观影人格称号” + 一键编辑资料弹窗
  2. 四维统计玻璃卡片：带冷青发光进度条（已评影片 / 平均打分 / 浏览足迹 / 评论正面率）
  3. 双栏分析区：
     - 左侧：自绘 SmoothRadarChart 发光平滑品味雷达图 + 偏好 Top 排名条
     - 右侧：我的高分挚爱迷你海报墙（点击直达详情）
  4. 底部：现代卡片流「观影与评价足迹」（星级、类型胶囊、NLP 情感徽章、短评摘要）
"""
from __future__ import annotations

import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QDialog, QFrame, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QProgressBar, QPushButton,
                             QScrollArea, QSpinBox, QVBoxLayout, QWidget)

from ui.widgets import (FlowContainer, MovieCard, SmoothRadarChart,
                        clear_layout, make_icon)
from utils.logger import get_logger

logger = get_logger("ui.profile")


class EditProfileDialog(QDialog):
    """编辑个人资料弹窗。"""

    def __init__(self, user, user_service, parent=None):
        super().__init__(parent)
        self.user = user
        self.user_service = user_service
        self.setWindowTitle("编辑个人资料")
        self.setFixedSize(400, 340)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(12)

        title = QLabel("编辑个人资料")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(title)

        layout.addWidget(QLabel("昵称"))
        self.nick_edit = QLineEdit(self.user.nickname or self.user.username)
        layout.addWidget(self.nick_edit)

        layout.addWidget(QLabel("性别"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["保密", "男", "女"])
        if self.user.gender in ("男", "女", "保密"):
            self.gender_combo.setCurrentText(self.user.gender)
        layout.addWidget(self.gender_combo)

        layout.addWidget(QLabel("年龄"))
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.age_spin.setValue(int(self.user.age or 0))
        layout.addWidget(self.age_spin)

        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("保存修改")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        nick = self.nick_edit.text().strip() or self.user.username
        gender = self.gender_combo.currentText()
        age = self.age_spin.value()
        try:
            from db.connection import execute_update
            execute_update(
                "UPDATE users SET nickname=%s, gender=%s, age=%s WHERE id=%s",
                (nick, gender, age, self.user.id),
            )
            self.user.nickname = nick
            self.user.gender = gender
            self.user.age = age
            self.accept()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "保存失败", f"更新资料失败：{exc}")


class ProfilePage(QWidget):
    """全面升级版个人观影空间页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.body = QWidget()
        self.body.setStyleSheet("background: transparent;")
        self.root = QVBoxLayout(self.body)
        self.root.setContentsMargins(22, 12, 22, 28)
        self.root.setSpacing(18)

        self.scroll.setWidget(self.body)
        outer.addWidget(self.scroll)
        self.refresh()

    def refresh(self):
        clear_layout(self.root)
        user = self.main.get_user()
        if not user:
            self.root.addWidget(QLabel("请先登录"))
            self.root.addStretch()
            return

        data = self._fetch_user_analytics(user)
        self._build_hero_banner(user, data)
        self._build_stats_row(data)
        self._build_middle_analytics(user, data)
        self._build_timeline_cards(data)
        self.root.addStretch()

    # ------------------------------------------------------------------
    # 数据聚合与人格推断
    # ------------------------------------------------------------------

    def _fetch_user_analytics(self, user):
        rating_rows = []
        hist_rows = []
        try:
            from db.connection import execute_query
            rating_rows = execute_query(
                "SELECT r.movie_id, r.score, r.comment, r.rating_time, "
                "m.title, m.genre, m.release_year, m.poster_url, m.poster_color, m.vote_average "
                "FROM ratings r JOIN movies m ON r.movie_id=m.id "
                "WHERE r.user_id=%s ORDER BY r.rating_time DESC",
                (user.id,),
            )
            hist_rows = execute_query(
                "SELECT h.watch_time, h.movie_id, m.title, m.genre, m.release_year, r.score, r.comment "
                "FROM history h JOIN movies m ON h.movie_id=m.id "
                "LEFT JOIN ratings r ON r.user_id=h.user_id AND r.movie_id=h.movie_id "
                "WHERE h.user_id=%s ORDER BY h.watch_time DESC LIMIT 12",
                (user.id,),
            )
        except Exception:
            logger.exception("加载个人空间数据失败")

        rating_count = len(rating_rows)
        avg_score = round(sum(r["score"] for r in rating_rows) / rating_count, 2) if rating_count else 0.0

        # 按类型聚合平均分
        genre_scores: dict[str, list[float]] = {}
        for r in rating_rows:
            for g in re.split(r"[/,、，\s]+", r.get("genre") or ""):
                g = g.strip()
                if g:
                    genre_scores.setdefault(g, []).append(float(r["score"]))

        top_genres = sorted(
            ((g, sum(vs) / len(vs), len(vs)) for g, vs in genre_scores.items()),
            key=lambda x: (x[1] * 0.7 + min(3, x[2]) * 0.3),
            reverse=True,
        )

        # 评论情感分析
        pos_pct = 0
        sent_count = 0
        try:
            from nlp.sentiment import get_analyzer
            analyzer = get_analyzer()
            comments = [r["comment"] for r in rating_rows if (r.get("comment") or "").strip()]
            if comments:
                sent_count = len(comments)
                pos = sum(1 for c in comments if analyzer.score(c) >= 0.65)
                pos_pct = int(round(pos / sent_count * 100))
        except Exception:
            pass

        # 观影人格称号
        persona = self._infer_persona(top_genres, rating_count)
        return {
            "rating_rows": rating_rows,
            "hist_rows": hist_rows,
            "rating_count": rating_count,
            "avg_score": avg_score,
            "hist_count": len(hist_rows),
            "pos_pct": pos_pct,
            "sent_count": sent_count,
            "top_genres": top_genres,
            "persona": persona,
        }

    def _infer_persona(self, top_genres, rating_count):
        if rating_count == 0 or not top_genres:
            return "初入影院 · 探索新世界"
        main_g = top_genres[0][0]
        mapping = {
            "科幻": "星际漫游者 · 硬核科幻探索家",
            "悬疑": "迷雾解谜人 · 烧脑反转爱好者",
            "犯罪": "暗夜侦探 · 罪案心理学派",
            "动作": "肾上腺素收藏家 · 视效动作控",
            "剧情": "银幕诗人 · 深度叙事鉴赏家",
            "喜剧": "快乐制造机 · 轻松治愈派",
            "动画": "造梦旅人 · 二次元与奇幻爱好者",
            "爱情": "浪漫主义者 · 心动时刻记录员",
        }
        return mapping.get(main_g, f"资深影迷 · {main_g}类型鉴赏家")

    # ------------------------------------------------------------------
    # 1. 顶部个人名片 Hero 横幅
    # ------------------------------------------------------------------

    def _build_hero_banner(self, user, data):
        hero = QFrame()
        hero.setObjectName("panel")
        hero.setStyleSheet(
            "QFrame#panel {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            "    stop:0 rgba(45, 212, 191, 45), stop:0.45 #10171B, stop:1 #0C1012);"
            "  border: 1px solid rgba(94, 234, 212, 0.16); border-radius: 22px;"
            "}"
        )
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(26, 22, 26, 22)
        hl.setSpacing(20)

        display = user.nickname or user.username
        avatar = QLabel((display[0] if display else "U").upper())
        avatar.setFixedSize(72, 72)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6EE7B7,stop:1 #0EA5E9);"
            "color:#06211B; font-size:28px; font-weight:bold; border-radius:36px;"
        )
        hl.addWidget(avatar)

        col = QVBoxLayout()
        col.setSpacing(6)

        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_lbl = QLabel(display)
        name_lbl.setStyleSheet("color:#F8FAFC; font-size:22px; font-weight:bold;")
        name_row.addWidget(name_lbl)

        persona_pill = QLabel(data["persona"])
        persona_pill.setStyleSheet(
            "background-color: rgba(94, 234, 212, 0.15); color: #5EEAD4;"
            "border: 1px solid rgba(94, 234, 212, 0.30); border-radius: 10px;"
            "padding: 3px 12px; font-size: 12px; font-weight: bold;"
        )
        name_row.addWidget(persona_pill)
        name_row.addStretch()
        col.addLayout(name_row)

        meta_parts = [f"@{user.username}"]
        if user.gender:
            meta_parts.append(user.gender)
        if user.age:
            meta_parts.append(f"{user.age} 岁")
        if hasattr(user, "register_time") and user.register_time:
            try:
                reg = user.register_time.strftime("%Y-%m") if hasattr(user.register_time, "strftime") else str(user.register_time)[:7]
                meta_parts.append(f"{reg} 加入")
            except Exception:
                pass
        meta_lbl = QLabel("  ·  ".join(meta_parts))
        meta_lbl.setStyleSheet("color:#94A3B8; font-size:13px;")
        col.addWidget(meta_lbl)

        hl.addLayout(col, 1)

        edit_btn = QPushButton("编辑资料")
        edit_btn.setObjectName("secondaryBtn")
        edit_btn.setIcon(make_icon("edit", "#E2E8F0", 15))
        edit_btn.setMinimumHeight(38)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(self._open_edit_dialog)
        hl.addWidget(edit_btn)

        self.root.addWidget(hero)

    def _open_edit_dialog(self):
        user = self.main.get_user()
        dlg = EditProfileDialog(user, self.main.user_service, self)
        if dlg.exec_() == QDialog.Accepted:
            self.main.refresh_user_display()
            self.refresh()

    # ------------------------------------------------------------------
    # 2. 四维统计玻璃卡片（带冷青发光进度条）
    # ------------------------------------------------------------------

    def _build_stats_row(self, data):
        row = QHBoxLayout()
        row.setSpacing(14)

        sent_val = f"{data['pos_pct']}%" if data["sent_count"] else "暂无"
        cards = [
            ("已评影片", str(data["rating_count"]), "部作品已打分", min(100, data["rating_count"] * 5), "#5EEAD4"),
            ("平均打分", f"{data['avg_score']:.1f}", "满分 5.0", int(data["avg_score"] * 20), "#FBBF24"),
            ("浏览足迹", str(data["hist_count"]), "最近观影详情", min(100, data["hist_count"] * 8), "#38BDF8"),
            ("评论情感正面率", sent_val, f"基于 {data['sent_count']} 条影评分析", data["pos_pct"], "#34D399"),
        ]
        for title, val, sub, pct, color in cards:
            card = QFrame()
            card.setObjectName("statCard")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(18, 16, 18, 14)
            cl.setSpacing(6)

            t = QLabel(title)
            t.setStyleSheet("color:#6B7C85; font-size:12px; font-weight:bold;")
            v = QLabel(val)
            v.setStyleSheet(f"color:{color}; font-size:24px; font-weight:bold;")
            s = QLabel(sub)
            s.setStyleSheet("color:#94A3B8; font-size:11px;")

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(max(4, pct))
            bar.setTextVisible(False)
            bar.setFixedHeight(4)
            bar.setStyleSheet(
                f"QProgressBar {{ background: rgba(255,255,255,0.06); border-radius: 2px; }}"
                f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}"
            )

            cl.addWidget(t)
            cl.addWidget(v)
            cl.addWidget(s)
            cl.addWidget(bar)
            row.addWidget(card, 1)

        self.root.addLayout(row)

    # ------------------------------------------------------------------
    # 3. 中部双栏：左品味雷达图 + 右我的高分挚爱海报墙
    # ------------------------------------------------------------------

    def _build_middle_analytics(self, user, data):
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        # 左栏：自绘发光平滑雷达图
        left_panel = QFrame()
        left_panel.setObjectName("panel")
        lp = QVBoxLayout(left_panel)
        lp.setContentsMargins(20, 18, 20, 18)
        lp.setSpacing(10)

        l_title = QLabel("观影品味雷达")
        l_title.setObjectName("sectionTitle")
        lp.addWidget(l_title)

        radar_items = [(g, min(1.0, avg / 5.0), avg) for g, avg, _c in data["top_genres"][:6]]
        radar = SmoothRadarChart(radar_items)
        lp.addWidget(radar, 1)

        if data["top_genres"]:
            chips = QHBoxLayout()
            chips.setSpacing(6)
            for g, avg, cnt in data["top_genres"][:4]:
                lbl = QLabel(f"{g} · {avg:.1f}分")
                lbl.setStyleSheet(
                    "background-color: rgba(94, 234, 212, 0.10); color: #5EEAD4;"
                    "border-radius: 8px; padding: 3px 10px; font-size: 11px; font-weight: bold;"
                )
                chips.addWidget(lbl)
            chips.addStretch()
            lp.addLayout(chips)

        mid_row.addWidget(left_panel, 4)

        # 右栏：我的高分挚爱海报墙（评分 >= 4）
        right_panel = QFrame()
        right_panel.setObjectName("panel")
        rp = QVBoxLayout(right_panel)
        rp.setContentsMargins(20, 18, 20, 18)
        rp.setSpacing(12)

        r_head = QHBoxLayout()
        r_title = QLabel("我的高分挚爱")
        r_title.setObjectName("sectionTitle")
        r_sub = QLabel("点击海报可重新打分或查看详情")
        r_sub.setObjectName("subText")
        r_head.addWidget(r_title)
        r_head.addStretch()
        r_head.addWidget(r_sub)
        rp.addLayout(r_head)

        fav_rows = [r for r in data["rating_rows"] if r["score"] >= 4][:4]
        if fav_rows:
            from db.models import Movie
            fav_flow = FlowContainer(h_spacing=14, v_spacing=14, margin=0)
            for r in fav_rows:
                mv = Movie(
                    id=r["movie_id"],
                    title=r["title"],
                    genre=r.get("genre") or "",
                    release_year=r.get("release_year") or 0,
                    poster_url=r.get("poster_url") or "",
                    poster_color=r.get("poster_color") or "#2DD4BF",
                    vote_average=float(r.get("vote_average") or 0),
                )
                card = MovieCard(mv, score=float(r["score"]), compact=True)
                card.clicked.connect(self._open_movie_by_id)
                fav_flow.flow.addWidget(card)
            rp.addWidget(fav_flow, 1)
        else:
            empty = QLabel("还没有给任何电影打 4~5 分，去「个性推荐」或「影片库」发现喜欢的电影吧！")
            empty.setWordWrap(True)
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #6B7C85; font-size: 13px; padding: 40px 10px;")
            rp.addWidget(empty, 1)

        mid_row.addWidget(right_panel, 6)
        self.root.addLayout(mid_row)

    def _open_movie_by_id(self, movie):
        try:
            full = self.main.movie_service.get_movie(movie.id)
            self.main.open_detail(full or movie)
        except Exception:
            self.main.open_detail(movie)

    # ------------------------------------------------------------------
    # 4. 底部：现代卡片流观影与评价足迹
    # ------------------------------------------------------------------

    def _build_timeline_cards(self, data):
        sec_title = QLabel("最近观影与评价足迹")
        sec_title.setObjectName("sectionTitle")
        self.root.addWidget(sec_title)

        rows = data["hist_rows"]
        if not rows:
            lbl = QLabel("暂无观影记录，去逛逛电影吧")
            lbl.setStyleSheet("color:#6B7C85; font-size:13px;")
            self.root.addWidget(lbl)
            return

        from nlp.sentiment import get_analyzer
        analyzer = get_analyzer()

        frame = QFrame()
        frame.setObjectName("panel")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(18, 16, 18, 16)
        fl.setSpacing(10)

        for r in rows:
            item_box = QFrame()
            item_box.setObjectName("subPanel")
            row_w = QHBoxLayout(item_box)
            row_w.setContentsMargins(14, 10, 14, 10)
            row_w.setSpacing(12)

            ts = str(r.get("watch_time", ""))[:16]
            t_lbl = QLabel(ts)
            t_lbl.setFixedWidth(122)
            t_lbl.setStyleSheet("color:#6B7C85; font-size:12px;")
            row_w.addWidget(t_lbl)

            title_col = QVBoxLayout()
            title_col.setSpacing(2)
            title_lbl = QLabel(r.get("title", ""))
            title_lbl.setStyleSheet("color:#F8FAFC; font-size:14px; font-weight:bold;")
            title_col.addWidget(title_lbl)

            cmt = (r.get("comment") or "").strip()
            if cmt:
                cmt_lbl = QLabel(cmt[:68] + ("…" if len(cmt) > 68 else ""))
                cmt_lbl.setStyleSheet("color:#94A3B8; font-size:12px;")
                title_col.addWidget(cmt_lbl)
            row_w.addLayout(title_col, 1)

            genre_lbl = QLabel((r.get("genre") or "").split("/")[0])
            genre_lbl.setStyleSheet(
                "color:#5EEAD4; background:rgba(45,212,191,0.12); border-radius:8px; "
                "padding:3px 9px; font-size:12px;"
            )
            row_w.addWidget(genre_lbl)

            if cmt:
                s_label = analyzer.label(cmt)
                s_map = {
                    "positive": ("正面", "rgba(52,211,153,0.16)", "#34D399"),
                    "neutral": ("中性", "rgba(56,189,248,0.14)", "#7DD3FC"),
                    "negative": ("负面", "rgba(251,191,36,0.16)", "#FBBF24"),
                }
                st, bg, fg = s_map.get(s_label, s_map["neutral"])
                sb = QLabel(st)
                sb.setStyleSheet(f"background:{bg}; color:{fg}; border-radius:8px; padding:3px 8px; font-size:11px; font-weight:bold;")
                row_w.addWidget(sb)

            score = r.get("score")
            if score:
                score_lbl = QLabel(f"★ {score}/5")
                score_lbl.setStyleSheet("color:#FBBF24; font-size:13px; font-weight:bold;")
                row_w.addWidget(score_lbl)

            fl.addWidget(item_box)

        self.root.addWidget(frame)
