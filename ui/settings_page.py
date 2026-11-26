# -*- coding: utf-8 -*-
"""
偏好设置页
暗夜流式类型胶囊 + 推荐引擎策略配置，支持 20~200 部多页推荐规模调节。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QScrollArea, QSpinBox, QVBoxLayout,
                             QWidget)

from ui.widgets import FlowContainer
from utils.logger import get_logger

logger = get_logger("ui.settings")

ALL_GENRES = ["科幻", "动作", "剧情", "喜剧", "动画", "悬疑", "犯罪", "爱情",
              "历史", "战争", "奇幻", "惊悚", "冒险", "家庭", "音乐"]


class SettingsPage(QWidget):
    """设置页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.genre_checks = {}
        self._build()
        self.refresh()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("settingsScrollContent")
        content.setStyleSheet("QWidget#settingsScrollContent { background: transparent; }")

        root = QVBoxLayout(content)
        root.setContentsMargins(36, 26, 36, 30)
        root.setSpacing(18)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("偏好设置")
        title.setObjectName("pageTitle")
        subtitle = QLabel("定制你喜欢的影片类型、推荐总规模及混合算法策略")
        subtitle.setObjectName("subText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        root.addLayout(title_box)

        genre_card = QFrame()
        genre_card.setObjectName("panel")
        g_layout = QVBoxLayout(genre_card)
        g_layout.setContentsMargins(24, 22, 24, 22)
        g_layout.setSpacing(12)

        g_title = QLabel("感兴趣的电影类型")
        g_title.setObjectName("sectionTitle")
        g_sub = QLabel("点击标签多选偏好题材，保存后立即作用于「个性推荐」排序与冷启动")
        g_sub.setObjectName("subText")
        g_layout.addWidget(g_title)
        g_layout.addWidget(g_sub)

        chip_container = FlowContainer(h_spacing=10, v_spacing=10, margin=0)
        for g in ALL_GENRES:
            btn = QPushButton(g)
            btn.setObjectName("genreChip")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self.genre_checks[g] = btn
            chip_container.flow.addWidget(btn)
        g_layout.addWidget(chip_container)
        root.addWidget(genre_card)

        algo_card = QFrame()
        algo_card.setObjectName("panel")
        a_layout = QVBoxLayout(algo_card)
        a_layout.setContentsMargins(24, 22, 24, 22)
        a_layout.setSpacing(16)

        a_title = QLabel("推荐引擎配置")
        a_title.setObjectName("sectionTitle")
        a_layout.addWidget(a_title)

        top_row = QHBoxLayout()
        top_text = QVBoxLayout()
        top_text.setSpacing(2)
        t_lbl = QLabel("个性推荐片单规模")
        t_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #F8FAFC;")
        t_desc = QLabel("每页展示 20 部电影，建议设置 60 ~ 120 部以便多页浏览（范围 20 - 200）")
        t_desc.setObjectName("subText")
        top_text.addWidget(t_lbl)
        top_text.addWidget(t_desc)

        self.top_spin = QSpinBox()
        self.top_spin.setRange(20, 200)
        self.top_spin.setSingleStep(20)
        self.top_spin.setValue(80)
        self.top_spin.setMinimumHeight(40)
        self.top_spin.setMinimumWidth(110)

        top_row.addLayout(top_text, 1)
        top_row.addWidget(self.top_spin)
        a_layout.addLayout(top_row)

        algo_row = QHBoxLayout()
        algo_row.setSpacing(14)
        self.check_content, c1 = self._make_algo_box(
            "内容推荐 (NLP)",
            "基于简介、类型、关键词与 TMDB 影评的 TF-IDF + LDA 语义相似度"
        )
        self.check_item, c2 = self._make_algo_box(
            "物品协同过滤 (Item-CF)",
            "基于评分矩阵计算影片关联度，推荐相似高分作品"
        )
        self.check_user, c3 = self._make_algo_box(
            "用户协同过滤 (User-CF)",
            "发现口味相近的影迷圈子，推荐同好高分佳作"
        )
        algo_row.addWidget(c1)
        algo_row.addWidget(c2)
        algo_row.addWidget(c3)
        a_layout.addLayout(algo_row)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("保存并应用到推荐")
        self.save_btn.setMinimumHeight(42)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)
        btn_row.addStretch()
        a_layout.addLayout(btn_row)

        root.addWidget(algo_card)
        root.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _make_algo_box(self, title, desc):
        box = QFrame()
        box.setObjectName("subPanel")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        cb = QCheckBox(title)
        cb.setCursor(Qt.PointingHandCursor)
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setStyleSheet("color: #94A3B8; font-size: 13px; padding-left: 30px;")

        layout.addWidget(cb)
        layout.addWidget(d)
        layout.addStretch()
        return cb, box

    def refresh(self):
        user = self.main.get_user()
        s = self.main.setting_service.get_settings(user.id)
        preferred = {g.strip() for g in (s["preferred_genres"] or "").split(",") if g.strip()}
        for g, cb in self.genre_checks.items():
            cb.setChecked(g in preferred)
        self.top_spin.setValue(s["recommend_top_n"])
        self.check_content.setChecked(s["enable_content"])
        self.check_item.setChecked(s["enable_item_cf"])
        self.check_user.setChecked(s["enable_user_cf"])

    def _save(self):
        user = self.main.get_user()
        genres = [g for g, cb in self.genre_checks.items() if cb.isChecked()]
        self.main.setting_service.save_settings(
            user.id, ",".join(genres), self.top_spin.value(),
            self.check_content.isChecked(),
            self.check_item.isChecked(),
            self.check_user.isChecked(),
        )
        self.main.recommend_page.refresh()
        QMessageBox.information(self, "成功", "偏好设置已保存，「个性推荐」已同步刷新")