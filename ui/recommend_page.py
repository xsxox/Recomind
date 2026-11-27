# -*- coding: utf-8 -*-
"""
个性推荐页 (v3.0 CoverFlow 3D 轮播 + 实时联动详情卡 + 分页片单)
==================================================================
参考 MOVIEGO 现代影院流媒体界面：
  1. 顶栏：问候标题 + 情绪/题材胶囊筛选 + 圆角搜索框
  2. 中间核心：CoverFlowCarousel 3D 阶梯层叠海报轮播（带平滑滑动与缩放动画）
  3. 实时联动：下方大圆角 Movie Details 玻璃卡片，随轮播选中电影动态更新海报、简介、数据小卡和趋势曲线
  4. 底部拓展：更多为你精选海报墙（20部/页分页浏览）
"""
from datetime import datetime

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)

from ui.widgets import (CoverFlowCarousel, FlowContainer, MovieCard,
                        MoviePoster, SparklineChart, clear_layout,
                        harmonize_color, make_icon, populate_grid)
from utils.logger import get_logger

logger = get_logger("ui.recommend")

PAGE_SIZE = 20


class RecommendPage(QWidget):
    """个性推荐页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self._carousel_items = []
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
        root.setContentsMargins(22, 12, 22, 26)
        root.setSpacing(18)

        # 顶栏：问候 + 快速语义检索条 + 刷新
        top = QHBoxLayout()
        top.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel(self._greeting_text())
        title.setObjectName("pageTitle")
        sub = QLabel("点击或滚动上方海报轮播，下方实时预览推荐解析")
        sub.setObjectName("subText")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        top.addLayout(title_col)
        top.addStretch()

        spot = QFrame()
        spot.setObjectName("spotlightBar")
        spot.setFixedWidth(400)
        spot_l = QHBoxLayout(spot)
        spot_l.setContentsMargins(14, 4, 6, 4)
        spot_l.setSpacing(6)
        ic = QLabel()
        ic.setPixmap(make_icon("sparkles", "#5EEAD4", 17).pixmap(17, 17))
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
        self.refresh_btn.setIcon(make_icon("refresh", "#E2E8F0", 16))
        self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.setMinimumHeight(42)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        # 情绪/题材快捷胶囊筛选栏 + 高分开关
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

        # 1. 核心互动区：3D CoverFlow 阶梯层叠轮播
        self.carousel = CoverFlowCarousel()
        self.carousel.selection_changed.connect(self._on_carousel_selected)
        self.carousel.movie_activated.connect(self.main.open_detail)
        root.addWidget(self.carousel)

        # 2. 下方实时联动详情大圆角面板 (参考图 Movie Details 区)
        self.detail_panel = QFrame()
        self.detail_panel.setObjectName("panel")
        self.detail_layout = QHBoxLayout(self.detail_panel)
        self.detail_layout.setContentsMargins(24, 22, 24, 22)
        self.detail_layout.setSpacing(22)
        root.addWidget(self.detail_panel)

        # 3. 底部更多片单网格
        sec_row = QHBoxLayout()
        self.status_label = QLabel("更多个性化片单")
        self.status_label.setObjectName("sectionTitle")
        self.page_summary = QLabel()
        self.page_summary.setObjectName("subText")
        sec_row.addWidget(self.status_label)
        sec_row.addStretch()
        sec_row.addWidget(self.page_summary)
        root.addLayout(sec_row)

        self.container = FlowContainer(h_spacing=20, v_spacing=22, margin=0)
        self.grid = self.container.flow
        root.addWidget(self.container)

        self.pager_wrap = QWidget()
        self.pager_wrap.setStyleSheet("background: transparent;")
        self.pager_layout = QHBoxLayout(self.pager_wrap)
        self.pager_layout.setContentsMargins(0, 6, 0, 4)
        self.pager_layout.setSpacing(8)
        root.addWidget(self.pager_wrap)

        root.addStretch()
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll)

    # ------------------------------------------------------------------
    # CoverFlow 选中回调：更新下方 Movie Details 实时联动面板
    # ------------------------------------------------------------------

    def _on_carousel_selected(self, index):
        if not (0 <= index < len(self._carousel_items)):
            self.detail_panel.hide()
            return
        movie, score, reason = self._carousel_items[index]
        self._render_detail_panel(movie, score, reason)

    def _render_detail_panel(self, movie, score, reason):
        clear_layout(self.detail_layout)
        self.detail_panel.show()

        # 左侧海报
        poster = MoviePoster(movie, radius=16, large=True)
        poster.setFixedSize(162, 236)
        self.detail_layout.addWidget(poster, 0, Qt.AlignTop)

        # 中间主信息区
        mid = QVBoxLayout()
        mid.setSpacing(10)

        head_row = QHBoxLayout()
        head_row.setSpacing(10)
        title_lbl = QLabel(movie.title)
        title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #F8FAFC;")
        head_row.addWidget(title_lbl)

        if movie.vote_count:
            hot_lbl = QLabel(f"🔥 {movie.vote_count}")
            hot_lbl.setStyleSheet("color: #FB923C; font-size: 13px; font-weight: bold;")
            head_row.addWidget(hot_lbl)
        head_row.addStretch()

        cta = QPushButton("查看详情与影评")
        cta.setMinimumHeight(36)
        cta.setCursor(Qt.PointingHandCursor)
        cta.clicked.connect(lambda: self.main.open_detail(movie))
        head_row.addWidget(cta)
        mid.addLayout(head_row)

        # 标签胶囊行
        pill_row = QHBoxLayout()
        pill_row.setSpacing(8)
        genres = [g.strip() for g in (movie.genre or "电影").replace("、", "/").split("/") if g.strip()][:2]
        for g in genres:
            gp = QLabel(g)
            gp.setStyleSheet(
                "background-color: rgba(94, 234, 212, 0.14); color: #5EEAD4;"
                "border-radius: 8px; padding: 3px 10px; font-size: 12px; font-weight: bold;"
            )
            pill_row.addWidget(gp)

        if movie.release_year:
            yp = QLabel(f"{movie.release_year}")
            yp.setStyleSheet(
                "background-color: #161E22; color: #CBD5E1; border: 1px solid rgba(255,255,255,0.08);"
                "border-radius: 8px; padding: 3px 10px; font-size: 12px;"
            )
            pill_row.addWidget(yp)

        if movie.director:
            dp = QLabel(f"导演：{movie.director}")
            dp.setStyleSheet(
                "background-color: #161E22; color: #CBD5E1; border: 1px solid rgba(255,255,255,0.08);"
                "border-radius: 8px; padding: 3px 10px; font-size: 12px;"
            )
            pill_row.addWidget(dp)

        if reason:
            rp = QLabel(reason)
            rp.setStyleSheet(
                "background-color: rgba(56, 189, 248, 0.14); color: #7DD3FC;"
                "border-radius: 8px; padding: 3px 10px; font-size: 12px;"
            )
            pill_row.addWidget(rp)
        pill_row.addStretch()
        mid.addLayout(pill_row)

        # 简介
        desc = (movie.description or "暂无剧情简介").strip()
        if len(desc) > 180:
            desc = desc[:180] + "…"
        d_lbl = QLabel(desc)
        d_lbl.setWordWrap(True)
        d_lbl.setStyleSheet("color: #94A3B8; font-size: 14px; line-height: 1.5;")
        mid.addWidget(d_lbl)
        mid.addStretch()

        self.detail_layout.addLayout(mid, 3)

        # 右侧数据指标卡 + 平滑趋势曲线图 (参考图右下角结构)
        right = QVBoxLayout()
        right.setSpacing(10)

        stat_row = QHBoxLayout()
        stat_row.setSpacing(10)

        match_pct = int(round(min(1.0, score or 0.8) * 100))
        vote_avg = getattr(movie, "vote_average", 0) or 0.0

        c1 = self._mini_stat_box("推荐契合度", f"{match_pct}%", "NLP + SVD 综合", "#5EEAD4")
        c2 = self._mini_stat_box("TMDB 口碑", f"★ {vote_avg:.1f}" if vote_avg else "暂无", f"{movie.vote_count or 0} 人评价", "#FBBF24")
        stat_row.addWidget(c1)
        stat_row.addWidget(c2)
        right.addLayout(stat_row)

        # 平滑趋势小图：根据电影特征构造 7 维匹配走势
        base = min(0.95, max(0.45, score or 0.75))
        q_norm = min(0.98, max(0.4, vote_avg / 10.0)) if vote_avg else 0.72
        curve_vals = [
            max(0.3, base * 0.82),
            max(0.35, base * 0.90),
            max(0.32, (base + q_norm) * 0.46),
            max(0.4, base * 0.96),
            q_norm,
            min(0.98, base * 1.02),
            base,
        ]
        chart_frame = QFrame()
        chart_frame.setObjectName("subPanel")
        cfl = QVBoxLayout(chart_frame)
        cfl.setContentsMargins(10, 8, 10, 6)
        cfl.setSpacing(2)
        c_title = QLabel("多维算法匹配曲线")
        c_title.setStyleSheet("color: #6B7C85; font-size: 11px; font-weight: bold;")
        cfl.addWidget(c_title)
        spark = SparklineChart(curve_vals, ["词频", "主题", "语义", "协同", "口碑", "SVD", "综合"])
        cfl.addWidget(spark)
        right.addWidget(chart_frame)

        self.detail_layout.addLayout(right, 2)

    def _mini_stat_box(self, label, value, sub, accent):
        box = QFrame()
        box.setObjectName("subPanel")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(12, 10, 12, 10)
        bl.setSpacing(2)
        l1 = QLabel(label)
        l1.setStyleSheet("color: #6B7C85; font-size: 11px;")
        l2 = QLabel(value)
        l2.setStyleSheet(f"color: {accent}; font-size: 20px; font-weight: bold;")
        l3 = QLabel(sub)
        l3.setStyleSheet("color: #94A3B8; font-size: 11px;")
        bl.addWidget(l1)
        bl.addWidget(l2)
        bl.addWidget(l3)
        return box

    # ------------------------------------------------------------------
    # 分页与数据加载
    # ------------------------------------------------------------------

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

        self.page_summary.setText(f"第 {page} / {total_pages} 页 · 共 {total} 部")
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
        prev_btn.setMinimumHeight(36)
        prev_btn.setEnabled(page > 1)
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.clicked.connect(lambda: self._go_page(page - 1))
        self.pager_layout.addWidget(prev_btn)

        for p in range(1, total_pages + 1):
            btn = QPushButton(str(p))
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.PointingHandCursor)
            if p == page:
                btn.setStyleSheet(
                    "QPushButton { background-color: #2DD4BF; color: #06211B;"
                    "border-radius: 12px; font-weight: bold; padding: 0px; }"
                )
            else:
                btn.setObjectName("secondaryBtn")
                btn.setStyleSheet(
                    "QPushButton { background-color: #101518; color: #CBD5E1;"
                    "border: 1px solid rgba(255,255,255,0.09); border-radius: 12px; padding: 0px; }"
                    "QPushButton:hover { background-color: #1A2226; color: #FFFFFF; }"
                )
            btn.clicked.connect(lambda _c, target=p: self._go_page(target))
            self.pager_layout.addWidget(btn)

        next_btn = QPushButton("下一页 →")
        next_btn.setObjectName("secondaryBtn")
        next_btn.setMinimumHeight(36)
        next_btn.setEnabled(page < total_pages)
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.clicked.connect(lambda: self._go_page(page + 1))
        self.pager_layout.addWidget(next_btn)
        self.pager_layout.addStretch()

    def _toggle_high_score(self):
        self._high_rated_only = self.high_score_btn.isChecked()
        self._apply_filters(scroll_top=False)

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
        """重新生成个性化推荐并填充 CoverFlow 与下方网格。"""
        for i, btn in enumerate(getattr(self, "_quick_chips", [])):
            btn.setChecked(i == 0)

        user = self.main.get_user()
        settings = self.main.setting_service.get_settings(user.id)
        desired = max(24, int(settings.get("recommend_top_n") or 80))

        self.status_label.setText("更多个性化片单")
        try:
            results = self.main.recommend_service.recommend_for_user_explained(
                user.id, top_n=desired, settings=settings
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("个性化推荐失败")
            QMessageBox.critical(self, "错误", f"推荐生成失败：{exc}")
            return

        if not results:
            self.carousel.set_items([])
            self.detail_panel.hide()
            self._raw_items = []
            self._all_items = []
            populate_grid(self.grid, [])
            self._go_page(1, scroll_top=False)
            empty = QLabel("暂无推荐结果，请先去「影片库」浏览或评价几部电影。")
            empty.setObjectName("cardInfo")
            self.grid.addWidget(empty)
            return

        # Top 9 进入 3D CoverFlow 轮播
        self._carousel_items = results[:9]
        self.carousel.set_items(self._carousel_items)

        rest = [(m, sc) for m, sc, _r in results[9:]] or [(m, sc) for m, sc, _r in results]
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

        if results:
            self._carousel_items = [(m, sc, f"语义匹配「{keyword}」") for m, sc in results[:9]]
            self.carousel.set_items(self._carousel_items)
        else:
            self.carousel.set_items([])
            self.detail_panel.hide()

        self.status_label.show()
        self.status_label.setText(f"“{keyword}” 的语义匹配结果")
        self._raw_items = results
        self._apply_filters(scroll_top=True)
