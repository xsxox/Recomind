"""
电影详情对话框
暗夜影院大气层背景头图 + 无边框 2:3 海报 + TMDB 影评双列卡片 + 相似电影海报墙。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QScrollArea, QTextEdit,
                             QVBoxLayout, QWidget)

from ui.widgets import (FlowContainer, MovieCard, MoviePoster, StarRating,
                        clear_layout, harmonize_color, populate_grid)
from utils.logger import get_logger

logger = get_logger("ui.detail")


class DetailDialog(QDialog):
    """电影详情对话框。"""

    def __init__(self, movie, main, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.main = main
        self.setWindowTitle("电影详情")
        self.setMinimumSize(1020, 800)
        self._build_shell()
        self.load_movie(movie)

    def _build_shell(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content.setObjectName("detailContent")
        self.content.setStyleSheet("QWidget#detailContent { background-color: #07090E; }")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 32)
        self.content_layout.setSpacing(22)
        scroll.setWidget(self.content)
        root.addWidget(scroll)

    def load_movie(self, movie):
        self.movie = movie
        self.setWindowTitle(f"电影详情 - {movie.title}")
        self._rebuild()
        user = self.main.get_user()
        if user:
            try:
                self.main.history_service.record(user.id, movie.id)
            except Exception:  # noqa: BLE001
                logger.exception("记录浏览历史失败")

    def _rebuild(self):
        clear_layout(self.content_layout)
        movie = self.movie
        top_c, _bot_c = harmonize_color(movie.poster_color)

        # ---- 随海报色温晕染的暗色沉浸头图 ----
        hero = QFrame()
        hero.setObjectName("detailHero")
        hero.setStyleSheet(
            f"QFrame#detailHero {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"    stop:0 rgba({top_c.red()}, {top_c.green()}, {top_c.blue()}, 115), "
            f"    stop:1 #07090E);"
            f"  border-bottom: 1px solid rgba(148, 163, 184, 0.12);"
            f"}}"
        )
        header = QHBoxLayout(hero)
        header.setContentsMargins(36, 32, 36, 30)
        header.setSpacing(28)

        cover = MoviePoster(movie, radius=14, large=True)
        cover.setFixedSize(190, 278)
        header.addWidget(cover, 0, Qt.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(12)

        title = QLabel(movie.title)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF; background: transparent;")
        title.setWordWrap(True)
        info.addWidget(title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        for text in [
            f"导演：{movie.director or '未知'}",
            movie.studio or "未知制片公司",
            movie.genre or "未分类",
            f"{movie.release_year} 年" if movie.release_year else "年份未知",
        ]:
            pill = QLabel(text)
            pill.setStyleSheet(
                "background-color: rgba(255,255,255,0.08); color: #E2E8F0;"
                "border: 1px solid rgba(255,255,255,0.12); border-radius: 8px;"
                "padding: 5px 12px; font-size: 13px; font-weight: 500;"
            )
            meta_row.addWidget(pill)
        meta_row.addStretch()
        info.addLayout(meta_row)

        self.avg_label = QLabel(self._rating_text(movie))
        self.avg_label.setStyleSheet(
            "background-color: rgba(245, 158, 11, 0.16); color: #FBBF24;"
            "border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 8px;"
            "padding: 7px 14px; font-size: 14px; font-weight: bold;"
        )
        info.addWidget(self.avg_label, 0, Qt.AlignLeft)

        desc_box = QLabel(movie.description or "暂无简介")
        desc_box.setWordWrap(True)
        desc_box.setStyleSheet("color: #CBD5E1; font-size: 15px; background: transparent; padding-top: 4px;")
        info.addWidget(desc_box)
        info.addStretch()

        header.addLayout(info, 1)
        self.content_layout.addWidget(hero)

        # ---- 内容主体 ----
        body = QVBoxLayout()
        body.setContentsMargins(36, 4, 36, 0)
        body.setSpacing(22)

        rate_panel = QFrame()
        rate_panel.setObjectName("panel")
        rate_layout = QVBoxLayout(rate_panel)
        rate_layout.setContentsMargins(24, 20, 24, 20)
        rate_layout.setSpacing(12)

        rate_title = QLabel("我的观影评价")
        rate_title.setObjectName("sectionTitle")
        rate_layout.addWidget(rate_title)

        self.stars = StarRating()
        rate_layout.addWidget(self.stars)

        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("分享你的观后感或短评（选填）...")
        self.comment_edit.setFixedHeight(88)
        rate_layout.addWidget(self.comment_edit)

        self.submit_btn = QPushButton("发布评分")
        self.submit_btn.setMinimumHeight(40)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self._submit_rating)
        rate_row = QHBoxLayout()
        rate_row.addWidget(self.submit_btn)
        rate_row.addStretch()
        rate_layout.addLayout(rate_row)
        body.addWidget(rate_panel)

        reviews = self.main.movie_service.list_reviews(movie.id, limit=4)
        if reviews:
            rv_title = QLabel("精选影评 · 来自 TMDB")
            rv_title.setObjectName("sectionTitle")
            body.addWidget(rv_title)

            rv_grid = QGridLayout()
            rv_grid.setSpacing(14)
            for idx, review in enumerate(reviews):
                card = QFrame()
                card.setObjectName("panel")
                cl = QVBoxLayout(card)
                cl.setContentsMargins(18, 16, 18, 16)
                cl.setSpacing(8)

                head_row = QHBoxLayout()
                head_row.setSpacing(8)
                initial = (review.author or "U")[0].upper()
                av = QLabel(initial)
                av.setFixedSize(28, 28)
                av.setAlignment(Qt.AlignCenter)
                av.setStyleSheet(
                    "background-color: rgba(14, 165, 233, 0.18); color: #38BDF8;"
                    "font-size: 13px; font-weight: bold; border-radius: 14px;"
                )
                author_lbl = QLabel(review.author or "影迷")
                author_lbl.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 14px;")
                head_row.addWidget(av)
                head_row.addWidget(author_lbl)
                head_row.addStretch()

                # NLP 情感极性徽章
                try:
                    from nlp.sentiment import get_analyzer
                    sent_label = get_analyzer().label(review.content or "")
                    sent_styles = {
                        "positive": ("正面评价", "rgba(16, 185, 129, 0.16)", "#34D399"),
                        "neutral": ("中性评价", "rgba(56, 189, 248, 0.14)", "#7DD3FC"),
                        "negative": ("负面评价", "rgba(245, 158, 11, 0.16)", "#FBBF24"),
                    }
                    s_txt, s_bg, s_fg = sent_styles.get(sent_label, sent_styles["neutral"])
                    sent_badge = QLabel(s_txt)
                    sent_badge.setStyleSheet(
                        f"background-color: {s_bg}; color: {s_fg};"
                        "border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: bold;"
                    )
                    head_row.addWidget(sent_badge)
                except Exception:
                    pass

                if review.rating:
                    score_lbl = QLabel(f"★ {review.rating:.0f}")
                    score_lbl.setStyleSheet(
                        "background-color: rgba(245, 158, 11, 0.16); color: #FBBF24;"
                        "border-radius: 6px; padding: 2px 8px; font-size: 12px; font-weight: bold;"
                    )
                    head_row.addWidget(score_lbl)

                cl.addLayout(head_row)

                text = review.content or ""
                if len(text) > 220:
                    text = text[:220] + "…"
                content_lbl = QLabel(text)
                content_lbl.setWordWrap(True)
                content_lbl.setStyleSheet("color: #94A3B8; font-size: 13px;")
                cl.addWidget(content_lbl)
                cl.addStretch()

                r, c = divmod(idx, 2)
                rv_grid.addWidget(card, r, c)
            body.addLayout(rv_grid)

        sim_title = QLabel("相似电影推荐")
        sim_title.setObjectName("sectionTitle")
        body.addWidget(sim_title)

        self.sim_container = FlowContainer(h_spacing=18, v_spacing=20, margin=0)
        self.sim_grid = self.sim_container.flow
        body.addWidget(self.sim_container)

        self.content_layout.addLayout(body)

        user = self.main.get_user()
        if user:
            rating = self.main.rating_service.get_user_rating(user.id, movie.id)
            if rating:
                self.stars.set_score(rating.score)
                self.comment_edit.setPlainText(rating.comment or "")

        self._load_similar()

    def _rating_text(self, movie):
        parts = []
        if movie.vote_count and movie.vote_average:
            parts.append(f"TMDB ★ {movie.vote_average:.1f} · {movie.vote_count} 人评价")
        avg, cnt = self.main.rating_service.get_movie_avg_score(movie.id)
        if cnt:
            parts.append(f"本站 {avg} 分 · {cnt} 人")
        return "　|　".join(parts) if parts else "暂无评分，欢迎写下第一条影评"

    def _load_similar(self):
        try:
            results = self.main.recommend_service.similar_movies(self.movie.id, top_n=8)
        except Exception:  # noqa: BLE001
            logger.exception("相似推荐失败")
            results = []
        if not results:
            empty = QLabel("暂无相似电影")
            empty.setObjectName("cardInfo")
            self.sim_grid.addWidget(empty)
            return
        cards = []
        for movie, score in results:
            card = MovieCard(movie, score=score)
            card.clicked.connect(self.load_book if hasattr(self, "load_book") else self.load_movie)
            cards.append(card)
        populate_grid(self.sim_grid, cards)

    def _submit_rating(self):
        user = self.main.get_user()
        if not user:
            return
        score = self.stars.value()
        if score <= 0:
            QMessageBox.warning(self, "提示", "请先点击星星选择评分")
            return
        comment = self.comment_edit.toPlainText().strip()
        try:
            self.main.rating_service.add_or_update_rating(user.id, self.movie.id, score, comment)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "错误", f"评分提交失败：{exc}")
            return
        self.main.recommend_service.invalidate_cache()
        QMessageBox.information(self, "成功", "评分已提交")
        self.avg_label.setText(self._rating_text(self.movie))