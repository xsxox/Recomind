# -*- coding: utf-8 -*-
"""
用户画像页面 (User Profile & Taste Analytics)
===============================================
升级版用户中心，新增：
  1. 偏好雷达图（按类型统计评分）
  2. 情感分析摘要（评论情绪分布）
  3. 推荐解释性卡片（"为什么推荐这部电影"）
  4. 观影历程时间线
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
                             QPushButton)

from utils.logger import get_logger

logger = get_logger("ui.profile")


def _make_figure(figsize=(5, 3.5)):
    try:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas  # type: ignore
        from matplotlib.figure import Figure  # type: ignore
        import matplotlib
        matplotlib.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans", "Arial Unicode MS"]
        matplotlib.rcParams["axes.unicode_minus"] = False
        fig = Figure(figsize=figsize, tight_layout=True)
        canvas = Canvas(fig)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return fig, canvas
    except Exception:
        return None, None


class ProfilePage(QWidget):
    """升级版用户画像与品味分析页面。"""

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
        self.root.setContentsMargins(36, 26, 36, 32)
        self.root.setSpacing(22)

        self.scroll.setWidget(self.body)
        outer.addWidget(self.scroll)

        self.refresh()

    def refresh(self):
        """重新渲染整个页面（评分变更后调用）。"""
        # 清空旧内容
        while self.root.count():
            item = self.root.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        user = self.main.get_user()
        if not user:
            self.root.addWidget(QLabel("请先登录"))
            self.root.addStretch()
            return

        self._build_header(user)
        self._build_stats_row(user)
        self._build_genre_chart(user)
        self._build_history_section(user)
        self.root.addStretch()

    # ------------------------------------------------------------------
    # 顶部用户信息
    # ------------------------------------------------------------------

    def _build_header(self, user):
        frame = QFrame()
        frame.setObjectName("panel")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # 头像
        display = user.nickname or user.username
        avatar = QLabel((display[0] if display else "U").upper())
        avatar.setFixedSize(64, 64)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #38BDF8,stop:1 #0284C7);"
            "color:#FFFFFF; font-size:26px; font-weight:bold; border-radius:32px;"
        )
        layout.addWidget(avatar)

        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        name_lbl = QLabel(display)
        name_lbl.setStyleSheet("color:#F8FAFC; font-size:20px; font-weight:bold;")
        info_col.addWidget(name_lbl)

        meta_parts = []
        if user.gender:
            meta_parts.append(user.gender)
        if user.age:
            meta_parts.append(f"{user.age} 岁")
        if hasattr(user, "register_time") and user.register_time:
            try:
                reg = user.register_time.strftime("%Y 年 %m 月加入") if hasattr(user.register_time, "strftime") else str(user.register_time)[:7]
                meta_parts.append(reg)
            except Exception:
                pass
        meta_lbl = QLabel("  ·  ".join(meta_parts) if meta_parts else "电影爱好者")
        meta_lbl.setStyleSheet("color:#64748B; font-size:14px;")
        info_col.addWidget(meta_lbl)
        layout.addLayout(info_col)
        layout.addStretch()

        self.root.addWidget(frame)

    # ------------------------------------------------------------------
    # 统计卡片行
    # ------------------------------------------------------------------

    def _build_stats_row(self, user):
        row = QHBoxLayout()
        row.setSpacing(12)

        try:
            from db.connection import execute_query
            cnt = execute_query("SELECT COUNT(*) as c FROM ratings WHERE user_id=%s", (user.id,))
            rating_count = cnt[0]["c"] if cnt else 0

            avg = execute_query("SELECT AVG(score) as a FROM ratings WHERE user_id=%s", (user.id,))
            avg_score = round(float(avg[0]["a"] or 0), 2) if avg and avg[0]["a"] else 0.0

            hist = execute_query("SELECT COUNT(*) as c FROM history WHERE user_id=%s", (user.id,))
            hist_count = hist[0]["c"] if hist else 0

            # 情感分析统计
            comments = execute_query("SELECT comment FROM ratings WHERE user_id=%s AND comment IS NOT NULL AND comment != ''", (user.id,))
            if comments:
                from nlp.sentiment import get_analyzer
                analyzer = get_analyzer()
                scores_sent = [analyzer.score(r["comment"]) for r in comments]
                avg_sent = sum(scores_sent) / len(scores_sent)
                pos_pct = int(sum(1 for s in scores_sent if s >= 0.65) / len(scores_sent) * 100)
                sent_text = f"{pos_pct}% 正面"
            else:
                sent_text = "暂无"
        except Exception:
            rating_count, avg_score, hist_count, sent_text = 0, 0.0, 0, "暂无"

        cards = [
            ("📽️  已评影片", str(rating_count), "部"),
            ("⭐  平均评分", f"{avg_score:.1f}", "/ 5.0"),
            ("👁️  浏览历史", str(hist_count), "部"),
            ("💬  评论情感", sent_text, "正面评价"),
        ]
        for title, val, unit in cards:
            card = QFrame()
            card.setObjectName("panel")
            card.setMinimumWidth(140)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 14, 16, 14)
            cl.setSpacing(3)
            QLabel(title).setParent(None)
            t = QLabel(title)
            t.setStyleSheet("color:#64748B; font-size:12px;")
            cl.addWidget(t)
            v = QLabel(val)
            v.setStyleSheet("color:#F8FAFC; font-size:22px; font-weight:bold;")
            cl.addWidget(v)
            u = QLabel(unit)
            u.setStyleSheet("color:#94A3B8; font-size:12px;")
            cl.addWidget(u)
            row.addWidget(card)
        row.addStretch()
        self.root.addLayout(row)

    # ------------------------------------------------------------------
    # 类型偏好雷达图
    # ------------------------------------------------------------------

    def _build_genre_chart(self, user):
        sec_title = QLabel("🎭  类型偏好分析")
        sec_title.setObjectName("sectionTitle")
        self.root.addWidget(sec_title)

        frame = QFrame()
        frame.setObjectName("panel")
        frame.setMinimumHeight(280)
        fl = QHBoxLayout(frame)
        fl.setContentsMargins(12, 12, 12, 12)

        try:
            from db.connection import execute_query
            rows = execute_query(
                "SELECT m.genre, AVG(r.score) as avg_score, COUNT(*) as cnt "
                "FROM ratings r JOIN movies m ON r.movie_id=m.id "
                "WHERE r.user_id=%s GROUP BY m.genre ORDER BY cnt DESC LIMIT 8",
                (user.id,)
            )
        except Exception:
            rows = []

        if rows:
            self._draw_genre_radar(fl, rows)
        else:
            lbl = QLabel("暂无足够评分数据来生成偏好分析（至少需评价 3 部不同类型影片）")
            lbl.setStyleSheet("color:#64748B; font-size:13px;")
            lbl.setAlignment(Qt.AlignCenter)
            fl.addWidget(lbl)

        self.root.addWidget(frame)

    def _draw_genre_radar(self, layout, rows):
        import re

        # 展开复合类型
        genre_scores: dict[str, list[float]] = {}
        for r in rows:
            genres_raw = re.split(r"[/,、，\s]+", r["genre"] or "")
            for g in genres_raw:
                g = g.strip()
                if g:
                    if g not in genre_scores:
                        genre_scores[g] = []
                    genre_scores[g].append(float(r["avg_score"] or 0))

        # 取前 8 个类型
        genre_avg = {g: sum(vs) / len(vs) for g, vs in genre_scores.items()}
        top_genres = sorted(genre_avg.items(), key=lambda x: -x[1])[:8]

        fig, canvas = _make_figure(figsize=(5, 3.5))
        if fig is None:
            return

        import numpy as np
        labels = [g for g, _ in top_genres]
        values = [v / 5.0 for _, v in top_genres]  # 归一化到 [0,1]
        N = len(labels)
        if N < 3:
            return

        angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
        angles += angles[:1]
        values += values[:1]

        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor("#0B0E16")
        fig.patch.set_facecolor("#101521")
        ax.plot(angles, values, linewidth=2, color="#38BDF8")
        ax.fill(angles, values, alpha=0.22, color="#0EA5E9")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, color="#CBD5E1", size=10)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["1", "2", "3", "4", "5"], color="#64748B", size=8)
        ax.spines["polar"].set_color("#1E293B")
        ax.set_title("类型偏好雷达（平均评分）", color="#F8FAFC", pad=12, fontsize=11)
        canvas.draw()
        layout.addWidget(canvas)

        # 右侧文字排名
        rank_col = QVBoxLayout()
        rank_col.setSpacing(6)
        rank_lbl = QLabel("偏好排名")
        rank_lbl.setStyleSheet("color:#94A3B8; font-size:12px; font-weight:bold;")
        rank_col.addWidget(rank_lbl)
        for i, (g, v) in enumerate(top_genres[:6]):
            stars = "★" * round(v) + "☆" * (5 - round(v))
            row_lbl = QLabel(f"{i+1}. {g}  {stars}  {v:.1f}")
            row_lbl.setStyleSheet("color:#CBD5E1; font-size:12px;")
            rank_col.addWidget(row_lbl)
        rank_col.addStretch()
        layout.addLayout(rank_col)

    # ------------------------------------------------------------------
    # 观影历史时间线（最近 10 条）
    # ------------------------------------------------------------------

    def _build_history_section(self, user):
        sec_title = QLabel("🕐  最近观影记录")
        sec_title.setObjectName("sectionTitle")
        self.root.addWidget(sec_title)

        try:
            from db.connection import execute_query
            rows = execute_query(
                "SELECT h.watch_time, m.title, m.genre, r.score "
                "FROM history h "
                "JOIN movies m ON h.movie_id=m.id "
                "LEFT JOIN ratings r ON r.user_id=h.user_id AND r.movie_id=h.movie_id "
                "WHERE h.user_id=%s ORDER BY h.watch_time DESC LIMIT 10",
                (user.id,)
            )
        except Exception:
            rows = []

        if not rows:
            lbl = QLabel("暂无观影记录")
            lbl.setStyleSheet("color:#64748B; font-size:13px;")
            self.root.addWidget(lbl)
            return

        frame = QFrame()
        frame.setObjectName("panel")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(10)

        for r in rows:
            row_w = QHBoxLayout()
            # 时间
            ts = str(r.get("watch_time", ""))[:16]
            t_lbl = QLabel(ts)
            t_lbl.setFixedWidth(130)
            t_lbl.setStyleSheet("color:#64748B; font-size:12px;")
            row_w.addWidget(t_lbl)

            # 片名
            title_lbl = QLabel(r.get("title", ""))
            title_lbl.setStyleSheet("color:#E2E8F0; font-size:14px; font-weight:500;")
            row_w.addWidget(title_lbl, 1)

            # 类型
            genre_lbl = QLabel(r.get("genre", "") or "")
            genre_lbl.setStyleSheet(
                "color:#7DD3FC; background:rgba(14,165,233,0.16); border-radius:8px; "
                "padding:2px 8px; font-size:12px;"
            )
            row_w.addWidget(genre_lbl)

            # 评分
            score = r.get("score")
            if score:
                score_lbl = QLabel(f"{'★' * int(score)}  {score}/5")
                score_lbl.setStyleSheet("color:#FBBF24; font-size:12px;")
                row_w.addWidget(score_lbl)
            fl.addLayout(row_w)

        self.root.addWidget(frame)
