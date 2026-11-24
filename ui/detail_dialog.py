# -*- coding: utf-8 -*-
"""
电影详情对话框
Apple Movies 风格随海报色调渲染的沉浸式详情页。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QScrollArea, QTextEdit, QVBoxLayout,
                             QWidget)

from ui.widgets import (MovieCard, MoviePoster, FlowContainer, StarRating,
                        apply_shadow, clear_layout, harmonize_color,
                        populate_grid)
from utils.logger import get_logger

logger = get_logger("ui.detail")


class DetailDialog(QDialog):
    """电影详情对话框。"""

    def __init__(self, movie, main, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.main = main
        self.setWindowTitle("电影详情")
        self.setMinimumSize(1000, 780)
        self._build_shell()
        self.load_movie(movie)

    def _build_shell(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content.setObjectName("detailContent")
        self.content.setStyleSheet("QWidget#detailContent { background-color: #F6F7FB; }")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 28)
        self.content_layout.setSpacing(20)
        scroll.setWidget(self.content)
        root.addWidget(scroll)

    def load_movie(self, movie):
        """载入并展示一部电影的详情（用于切换相似电影）。"""
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

        # ---- 随海报色彩自动调制的顶部沉浸氛围区 ----
        hero = QFrame()
        hero.setObjectName("detailHero")
        hero.setStyleSheet(
            f"QFrame#detailHero {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 rgba({top_c.red()}, {top_c.green()}, {top_c.blue()}, 28), "
            f"stop:1 #FFFFFF); border-bottom: 1px solid #EAECEF; }}"
        )
        header = QHBoxLayout(hero)
        header.setContentsMargins(36, 30, 36, 30)
        header.setSpacing(28)

        cover = MoviePoster(movie, radius=12, large=True)
        cover.setFixedSize(172, 238)
        apply_shadow(cover, blur=28, y_offset=8, alpha=45)
        header.addWidget(cover, 0, Qt.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(12)

        title = QLabel(movie.title)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #0F172A; background: transparent;")
        title.setWordWrap(True)
        info.addWidget(title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        for text in [
            movie.director or "未知",
            movie.studio or "未知制片公司",
            movie.genre or "未类型",
            f"{movie.release_year} 年" if movie.release_year else "年份未知",
        ]:
            pill = QLabel(text)
            pill.setStyleSheet(
                "background-color: rgba(255,255,255,0.85); color: #374151;"
                "border: 1px solid #E5E7EB; border-radius: 8px;"
                "padding: 5px 12px; font-size: 13px; font-weight: 500;"
            )
            meta_row.addWidget(pill)
        meta_row.addStretch()
        info.addLayout(meta_row)

        avg, cnt = self.main.rating_service.get_movie_avg_score(movie.id)
        rating_text = f"综合评分 {avg} 分  ·  {cnt} 人评价" if cnt else "暂无评价，欢迎写下你的第一条影评"
        self.avg_label = QLabel(rating_text)
        self.avg_label.setStyleSheet(
            "background-color: #FEF3C7; color: #B45309; border-radius: 8px;"
            "padding: 7px 14px; font-size: 14px; font-weight: bold;"
        )
        info.addWidget(self.avg_label, 0, Qt.AlignLeft)

        desc_box = QLabel(movie.description or "暂无简介")
        desc_box.setWordWrap(True)
        desc_box.setStyleSheet("color: #4B5563; font-size: 15px; background: transparent; padding-top: 4px;")
        info.addWidget(desc_box)
        info.addStretch()

        header.addLayout(info, 1)
        self.content_layout.addWidget(hero)

        # ---- 内容主体区 ----
        body = QVBoxLayout()
        body.setContentsMargins(32, 4, 32, 0)
        body.setSpacing(20)

        rate_panel = QFrame()
        rate_panel.setObjectName("panel")
        apply_shadow(rate_panel, blur=18, y_offset=4, alpha=12)
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
        self.comment_edit.setFixedHeight(92)
        rate_layout.addWidget(self.comment_edit)

        self.submit_btn = QPushButton("发布评分")
        self.submit_btn.setMinimumHeight(42)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self._submit_rating)
        rate_row = QHBoxLayout()
        rate_row.addWidget(self.submit_btn)
        rate_row.addStretch()
        rate_layout.addLayout(rate_row)
        body.addWidget(rate_panel)

        sim_title = QLabel("相似电影推荐 · 基于 NLP 内容语义计算")
        sim_title.setObjectName("sectionTitle")
        body.addWidget(sim_title)

        self.sim_container = FlowContainer(h_spacing=18, v_spacing=18)
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
            card.clicked.connect(self.load_movie)
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
        QMessageBox.information(self, "成功", "评分已提交")
        avg, cnt = self.main.rating_service.get_movie_avg_score(self.movie.id)
        self.avg_label.setText(f"综合评分 {avg} 分  ·  {cnt} 人评价")