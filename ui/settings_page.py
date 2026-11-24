# -*- coding: utf-8 -*-
"""
设置页
配置推荐偏好（偏好类型、推荐条数、推荐算法开关），保存后作用于个性推荐。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QSpinBox, QVBoxLayout, QWidget)

from ui.widgets import apply_shadow
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

    def _section_title(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("sectionTitle")
        return lbl

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(16)

        title = QLabel("设置")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("panel")
        apply_shadow(card, blur=18, y_offset=4, alpha=12)
        c = QVBoxLayout(card)
        c.setContentsMargins(24, 22, 24, 22)
        c.setSpacing(14)

        c.addWidget(self._section_title("推荐偏好"))

        c.addWidget(QLabel("偏好类型（可多选）"))
        genre_row = QHBoxLayout()
        genre_row.setSpacing(8)
        for g in ALL_GENRES:
            cb = QCheckBox(g)
            cb.setCursor(Qt.PointingHandCursor)
            self.genre_checks[g] = cb
            genre_row.addWidget(cb)
        genre_row.addStretch()
        c.addLayout(genre_row)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.addWidget(QLabel("推荐条数"))
        self.top_spin = QSpinBox()
        self.top_spin.setRange(5, 50)
        self.top_spin.setValue(12)
        self.top_spin.setMinimumHeight(38)
        self.top_spin.setMinimumWidth(80)
        top_row.addWidget(self.top_spin)
        top_row.addSpacing(24)
        top_row.addWidget(QLabel("推荐算法"))
        self.check_content = QCheckBox("内容推荐")
        self.check_item = QCheckBox("物品协同过滤")
        self.check_user = QCheckBox("用户协同过滤")
        for cb in (self.check_content, self.check_item, self.check_user):
            cb.setCursor(Qt.PointingHandCursor)
            top_row.addWidget(cb)
        top_row.addStretch()
        c.addLayout(top_row)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("保存设置")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)
        btn_row.addStretch()
        c.addLayout(btn_row)

        hint = QLabel("保存后，「个性推荐」页会按此偏好重新生成推荐。")
        hint.setObjectName("subText")
        c.addWidget(hint)

        root.addWidget(card)
        root.addStretch()

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
        QMessageBox.information(self, "成功", "设置已保存，请到「个性推荐」页刷新查看效果")
