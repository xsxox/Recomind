# -*- coding: utf-8 -*-
"""
个性推荐页
Top 1 今日主推聚光灯横幅 + 语义检索 + 每页 20 部多页翻页海报墙。
"""
from datetime import datetime

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)

from ui.widgets import (FlowContainer, MovieCard, MoviePoster, clear_layout,
                        harmonize_color, make_icon, populate_grid)
from utils.logger import get_logger

logger = get_logger("ui.recommend")

PAGE_SIZE = 20


class RecommendPage(QWidget):
    """个性推荐页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self._hero_movie = None
        self._raw_items = []
        self._all_items = []
        self._high_rated_only = False
        self._current_page = 1
        self._build()

    def _greeting_text(self):
        hour = datetime.now().hour
        period = "上午好" if hour < 12 else ("下午好" if hour < 18 else "晚上好")
        user = self.main.get_user()
        name = (user.nickname or user.username) if user else "影迷"
        return f"{period}，{name}"

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        body = QWidget()
        body.setObjectName("recScrollBody")
        body.setStyleSheet("QWidget#recScrollBody { background: transparent; }")

        root = QVBoxLayout(body)
        root.setContentsMargins(36, 26, 36, 32)
        root.setSpacing(20)

        # 顶栏：问候 + 快速语义检索条 + 刷新
        top = QHBoxLayout()
        top.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel(self._greeting_text())
        title.setObjectName("pageTitle")
        sub = QLabel("为你精选的混合个性化片单")
        sub.setObjectName("subText")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        top.addLayout(title_col)
        top.addStretch()

        spot = QFrame()
        spot.setObjectName("spotlightBar")
        spot.setFixedWidth(440)
        spot_l = QHBoxLayout(spot)
        spot_l.setContentsMargins(12, 4, 6, 4)
        spot_l.setSpacing(6)
        ic = QLabel()
        ic.setPixmap(make_icon("sparkles", "#38BDF8", 17).pixmap(17, 17))
        spot_l.addWidget(ic)
        self.kw_input = QLineEdit()
        self.kw_input.setObjectName("spotlightInput")
        self.kw_input.setPlaceholderText("输入情绪、场景或主题词秒找电影...")
        self.kw_input.returnPressed.connect(self._keyword_recommend)
        spot_l.addWidget(self.kw_input, 1)
        self.kw_btn = QPushButton("探索")
        self.kw_btn.setMinimumHeight(34)
        self.kw_btn.setCursor(Qt.PointingHandCursor)
        self.kw_btn.clicked.connect(self._keyword_recommend)
        spot_l.addWidget(self.kw_btn)
        top.addWidget(spot)

        self.refresh_btn = QPushButton(" 刷新片单")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.setIcon(make_icon("refresh", "#E4E4E7", 16))
        self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.setMinimumHeight(42)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        # 流媒体情绪/题材快捷胶囊筛选栏
        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self._quick_chips = []
        quick_tags = [
            ("全部精选", ""),
            ("科幻烧脑", "科幻 太空 烧脑"),
            ("悬疑反转", "悬疑 推理 犯罪"),
            ("高分治愈", "剧情 温暖 治愈"),
            ("动作爽片", "动作 冒险 刺激"),
            ("浪漫爱情", "爱情 浪漫 青春"),
            ("奇幻动画", "动画 奇幻 冒险"),
        ]
        for idx, (label, query) in enumerate(quick_tags):
            cbtn = QPushButton(label)
            cbtn.setObjectName("chipBtn")
            cbtn.setCheckable(True)
            cbtn.setChecked(idx == 0)
            cbtn.setCursor(Qt.PointingHandCursor)
            cbtn.clicked.connect(lambda _c, i=idx, q=query: self._on_quick_chip(i, q))
            self._quick_chips.append(cbtn)
            chip_row.addWidget(cbtn)
        chip_row.addStretch()

        self.high_score_btn = QPushButton("★ 仅看高分 (≥7.5)")
        self.high_score_btn.setObjectName("chipBtn")
        self.high_score_btn.setCheckable(True)
        self.high_score_btn.setCursor(Qt.PointingHandCursor)
        self.high_score_btn.clicked.connect(self._toggle_high_score)
        chip_row.addWidget(self.high_score_btn)
        root.addLayout(chip_row)

        # 今日首选焦点横幅
        self.hero_frame = QFrame()
        self.hero_frame.setObjectName("heroSpot")
        self.hero_layout = QHBoxLayout(self.hero_frame)
        self.hero_layout.setContentsMargins(28, 24, 28, 24)
        self.hero_layout.setSpacing(26)
        root.addWidget(self.hero_frame)

        # 分区标题 + 页码提示
        sec_row = QHBoxLayout()
        self.status_label = QLabel("更多为你精选")
        self.status_label.setObjectName("sectionTitle")
        self.page_summary = QLabel()
        self.page_summary.setObjectName("subText")
        sec_row.addWidget(self.status_label)
        sec_row.addStretch()
        sec_row.addWidget(self.page_summary)
        root.addLayout(sec_row)

        # 无边框海报墙
        self.container = FlowContainer(h_spacing=22, v_spacing=24, margin=0)
        self.grid = self.container.flow
        root.addWidget(self.container)

        # 底部分页导航条
        self.pager_wrap = QWidget()
        self.pager_wrap.setStyleSheet("background: transparent;")
        self.pager_layout = QHBoxLayout(self.pager_wrap)
        self.pager_layout.setContentsMargins(0, 8, 0, 4)
        self.pager_layout.setSpacing(8)
        root.addWidget(self.pager_wrap)

        root.addStretch()

        self.scroll.setWidget(body)
        outer.addWidget(self.scroll)

    def _render_hero(self, movie, score, reason):
        clear_layout(self.hero_layout)
        self._hero_movie = movie
        top_c, _bot_c = harmonize_color(movie.poster_color)
        self.hero_frame.setStyleSheet(
            f"QFrame#heroSpot {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 rgba({top_c.red()}, {top_c.green()}, {top_c.blue()}, 100), "
            f"    stop:0.48 #0F172A, stop:1 #090D16);"
            f"  border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 20px;"
            f"}}"
        )

        poster = MoviePoster(movie, radius=14, large=True)
        poster.setFixedSize(160, 232)
        self.hero_layout.addWidget(poster)

        col = QVBoxLayout()
        col.setSpacing(10)

        tag_row = QHBoxLayout()
        tag_row.setSpacing(8)
        top_badge = QLabel(f"TODAY'S TOP PICK · {int(round(min(1.0, score) * 100))}% 匹配")
        top_badge.setStyleSheet(
            "background-color: #0284C7; color: #FFFFFF; border-radius: 6px;"
            "padding: 4px 11px; font-size: 11px; font-weight: bold; letter-spacing: 0.4px;"
        )
        tag_row.addWidget(top_badge)

        if reason:
            r_badge = QLabel(reason)
            r_badge.setStyleSheet(
                "background-color: rgba(255,255,255,0.10); color: #E2E8F0; border-radius: 6px;"
                "padding: 4px 10px; font-size: 12px;"
            )
            tag_row.addWidget(r_badge)
        tag_row.addStretch()
        col.addLayout(tag_row)

        t_lbl = QLabel(movie.title)
        t_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF; background: transparent;")
        t_lbl.setWordWrap(True)
        col.addWidget(t_lbl)

        meta_parts = [
            f"{movie.release_year} 年" if movie.release_year else "",
            movie.genre or "",
            f"导演：{movie.director}" if movie.director else "",
            f"TMDB ★ {movie.vote_average:.1f}" if movie.vote_average else "",
        ]
        meta_lbl = QLabel("  ·  ".join([p for p in meta_parts if p]))
        meta_lbl.setStyleSheet("color: #CBD5E1; font-size: 13px; background: transparent;")
        col.addWidget(meta_lbl)

        desc = (movie.description or "暂无剧情简介").strip()
        if len(desc) > 130:
            desc = desc[:130] + "…"
        d_lbl = QLabel(desc)
        d_lbl.setWordWrap(True)
        d_lbl.setStyleSheet("color: #94A3B8; font-size: 14px; background: transparent;")
        col.addWidget(d_lbl)

        col.addStretch()
        cta = QPushButton("查看影片详情与影评")
        cta.setMinimumHeight(40)
        cta.setCursor(Qt.PointingHandCursor)
        cta.clicked.connect(lambda: self.main.open_detail(movie))
        col.addWidget(cta, 0, Qt.AlignLeft)

        self.hero_layout.addLayout(col, 1)
        self.hero_frame.show()

    def _go_page(self, page, scroll_top=True):
        total = len(self._all_items)
        if total == 0:
            self.page_summary.setText("")
            clear_layout(self.pager_layout)
            self.pager_wrap.hide()
            return

        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(1, min(total_pages, page))
        self._current_page = page

        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_items = self._all_items[start:end]

        cards = []
        for movie, score in page_items:
            card = MovieCard(movie, score=score)
            card.clicked.connect(self.main.open_detail)
            cards.append(card)
        populate_grid(self.grid, cards)

        self.page_summary.setText(f"第 {page} / {total_pages} 页 · 共 {total} 部（每页 {PAGE_SIZE} 部）")
        self._rebuild_pager(page, total_pages)
        if scroll_top:
            self.scroll.verticalScrollBar().setValue(0)

    def _rebuild_pager(self, page, total_pages):
        clear_layout(self.pager_layout)
        if total_pages <= 1:
            self.pager_wrap.hide()
            return

        self.pager_wrap.show()
        self.pager_layout.addStretch()

        prev_btn = QPushButton("← 上一页")
        prev_btn.setObjectName("secondaryBtn")
        prev_btn.setMinimumHeight(38)
        prev_btn.setEnabled(page > 1)
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.clicked.connect(lambda: self._go_page(page - 1))
        self.pager_layout.addWidget(prev_btn)

        # 页码按钮（最多展示前后窗口页码）
        for p in range(1, total_pages + 1):
            btn = QPushButton(str(p))
            btn.setFixedSize(40, 38)
            btn.setCursor(Qt.PointingHandCursor)
            if p == page:
                btn.setStyleSheet(
                    "QPushButton { background-color: #0284C7; color: #FFFFFF;"
                    "border-radius: 9px; font-weight: bold; padding: 0px; }"
                )
            else:
                btn.setObjectName("secondaryBtn")
                btn.setStyleSheet(
                    "QPushButton { background-color: #101521; color: #CBD5E1;"
                    "border: 1px solid rgba(148,163,184,0.14); border-radius: 9px; padding: 0px; }"
                    "QPushButton:hover { background-color: #1A2336; color: #FFFFFF; }"
                )
            btn.clicked.connect(lambda _c, target=p: self._go_page(target))
            self.pager_layout.addWidget(btn)

        next_btn = QPushButton("下一页 →")
        next_btn.setObjectName("secondaryBtn")
        next_btn.setMinimumHeight(38)
        next_btn.setEnabled(page < total_pages)
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.clicked.connect(lambda: self._go_page(page + 1))
        self.pager_layout.addWidget(next_btn)

        self.pager_layout.addStretch()

    def _toggle_high_score(self):
        self._high_rated_only = self.high_score_btn.isChecked()
        self._apply_filters(scroll_top=True)

    def _apply_filters(self, scroll_top=False):
        items = list(self._raw_items)
        if self._high_rated_only:
            items = [(m, sc) for m, sc in items if (getattr(m, "vote_average", 0) or 0) >= 7.5]
        self._all_items = items
        if not items:
            populate_grid(self.grid, [])
            self._go_page(1, scroll_top=False)
            empty = QLabel("当前筛选条件下暂无匹配电影，试试关闭「仅看高分」或切换关键词。")
            empty.setObjectName("cardInfo")
            self.grid.addWidget(empty)
            return
        self._go_page(1, scroll_top=scroll_top)

    def _on_quick_chip(self, index, query):
        for i, btn in enumerate(self._quick_chips):
            btn.setChecked(i == index)
        if not query:
            self.kw_input.clear()
            self.refresh()
            return
        self.kw_input.setText(query)
        self._keyword_recommend()

    def refresh(self):
        """重新生成个性化推荐（按设置规模召回并支持 20 部/页翻页）。"""
        for i, btn in enumerate(getattr(self, "_quick_chips", [])):
            btn.setChecked(i == 0)
        user = self.main.get_user()
        settings = self.main.setting_service.get_settings(user.id)
        desired = max(20, int(settings.get("recommend_top_n") or 80))

        self.status_label.setText("更多为你精选")
        try:
            # +1 给顶部焦点横幅，下方网格整除保持 20 部/页
            results = self.main.recommend_service.recommend_for_user_explained(
                user.id, top_n=desired + 1, settings=settings
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("个性化推荐失败")
            QMessageBox.critical(self, "错误", f"推荐生成失败：{exc}")
            return

        if not results:
            self.hero_frame.hide()
            self._raw_items = []
            self._all_items = []
            populate_grid(self.grid, [])
            self._go_page(1, scroll_top=False)
            empty = QLabel("暂无推荐结果，请先去「影片库」浏览或评价几部电影。")
            empty.setObjectName("cardInfo")
            self.grid.addWidget(empty)
            return

        top_movie, top_score, top_reason = results[0]
        self._render_hero(top_movie, top_score, top_reason)

        rest = [(m, sc) for m, sc, _r in results[1:]]
        if not rest:
            self.status_label.hide()
            self._raw_items = []
            self._all_items = []
            populate_grid(self.grid, [])
            self._go_page(1, scroll_top=False)
            return

        self.status_label.show()
        self._raw_items = rest
        self._apply_filters(scroll_top=False)

    def _keyword_recommend(self):
        keyword = self.kw_input.text().strip()
        if not keyword:
            QMessageBox.information(self, "提示", "请输入关键词或偏好描述")
            return
        try:
            results = self.main.recommend_service.recommend_by_keyword(keyword, top_n=100)
        except Exception as exc:  # noqa: BLE001
            logger.exception("关键词推荐失败")
            QMessageBox.critical(self, "错误", f"推荐生成失败：{exc}")
            return

        self.hero_frame.hide()
        self.status_label.show()
        self.status_label.setText(f"“{keyword}” 的语义匹配结果")
        self._raw_items = results
        self._apply_filters(scroll_top=True)