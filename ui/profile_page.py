# -*- coding: utf-8 -*-
"""
个人中心页
查看/编辑个人资料、修改密码、管理我的评分与浏览历史。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QSpinBox,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ui.widgets import apply_shadow
from utils.logger import get_logger

logger = get_logger("ui.profile")


class ProfilePage(QWidget):
    """个人中心页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self._build()
        self.refresh()

    def _section_title(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("sectionTitle")
        return lbl

    def _make_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.NoFocus)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(44)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        return table

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(16)

        title = QLabel("个人中心")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # 资料卡片
        card = QFrame()
        card.setObjectName("panel")
        apply_shadow(card, blur=18, y_offset=4, alpha=12)
        c = QVBoxLayout(card)
        c.setContentsMargins(24, 22, 24, 22)
        c.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(16)
        self.avatar = QLabel()
        self.avatar.setObjectName("userAvatar")
        self.avatar.setFixedSize(54, 54)
        self.avatar.setAlignment(Qt.AlignCenter)
        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827;")
        self.handle_label = QLabel()
        self.handle_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        name_col.addWidget(self.name_label)
        name_col.addWidget(self.handle_label)
        top.addWidget(self.avatar)
        top.addLayout(name_col, 1)
        self.stats_label = QLabel()
        self.stats_label.setObjectName("scoreBadge")
        top.addWidget(self.stats_label)
        c.addLayout(top)

        form = QHBoxLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("昵称"))
        self.nickname_edit = QLineEdit()
        self.nickname_edit.setMinimumHeight(38)
        form.addWidget(self.nickname_edit, 1)
        form.addWidget(QLabel("性别"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女", "其他"])
        self.gender_combo.setMinimumHeight(38)
        self.gender_combo.setMinimumWidth(90)
        form.addWidget(self.gender_combo)
        form.addWidget(QLabel("年龄"))
        self.age_spin = QSpinBox()
        self.age_spin.setRange(1, 120)
        self.age_spin.setMinimumHeight(38)
        self.age_spin.setMinimumWidth(80)
        form.addWidget(self.age_spin)
        c.addLayout(form)

        btn_row = QHBoxLayout()
        self.save_profile_btn = QPushButton("保存资料")
        self.save_profile_btn.setMinimumHeight(40)
        self.save_profile_btn.setCursor(Qt.PointingHandCursor)
        self.save_profile_btn.clicked.connect(self._save_profile)
        btn_row.addWidget(self.save_profile_btn)
        btn_row.addStretch()
        c.addLayout(btn_row)
        root.addWidget(card)

        # 修改密码卡片
        pwd_card = QFrame()
        pwd_card.setObjectName("panel")
        apply_shadow(pwd_card, blur=18, y_offset=4, alpha=12)
        pc = QVBoxLayout(pwd_card)
        pc.setContentsMargins(24, 20, 24, 20)
        pc.setSpacing(10)
        pc.addWidget(self._section_title("修改密码"))
        pwd_form = QHBoxLayout()
        pwd_form.setSpacing(10)
        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.Password)
        self.old_pwd.setPlaceholderText("原密码")
        self.old_pwd.setMinimumHeight(38)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.Password)
        self.new_pwd.setPlaceholderText("新密码")
        self.new_pwd.setMinimumHeight(38)
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.Password)
        self.confirm_pwd.setPlaceholderText("确认新密码")
        self.confirm_pwd.setMinimumHeight(38)
        pwd_form.addWidget(self.old_pwd)
        pwd_form.addWidget(self.new_pwd)
        pwd_form.addWidget(self.confirm_pwd)
        pc.addLayout(pwd_form)
        pwd_btn_row = QHBoxLayout()
        self.pwd_btn = QPushButton("修改密码")
        self.pwd_btn.setMinimumHeight(40)
        self.pwd_btn.setCursor(Qt.PointingHandCursor)
        self.pwd_btn.clicked.connect(self._change_password)
        pwd_btn_row.addWidget(self.pwd_btn)
        pwd_btn_row.addStretch()
        pc.addLayout(pwd_btn_row)
        root.addWidget(pwd_card)

        # 我的评分
        root.addWidget(self._section_title("我的评分"))
        rating_bar = QHBoxLayout()
        self.del_rating_btn = QPushButton("删除选中评分")
        self.del_rating_btn.setObjectName("dangerBtn")
        self.del_rating_btn.setCursor(Qt.PointingHandCursor)
        self.del_rating_btn.clicked.connect(self._delete_rating)
        rating_bar.addWidget(self.del_rating_btn)
        rating_bar.addStretch()
        root.addLayout(rating_bar)
        self.rating_table = self._make_table(["ID", "电影", "类型", "评分", "评语"])
        root.addWidget(self.rating_table, 2)

        # 我的浏览历史
        root.addWidget(self._section_title("我的浏览历史"))
        hist_bar = QHBoxLayout()
        self.clear_hist_btn = QPushButton("清空历史")
        self.clear_hist_btn.setObjectName("secondaryBtn")
        self.clear_hist_btn.setCursor(Qt.PointingHandCursor)
        self.clear_hist_btn.clicked.connect(self._clear_history)
        hist_bar.addWidget(self.clear_hist_btn)
        hist_bar.addStretch()
        root.addLayout(hist_bar)
        self.history_table = self._make_table(["ID", "电影", "类型", "浏览时间"])
        root.addWidget(self.history_table, 1)

    def refresh(self):
        user = self.main.get_user()
        display = user.nickname or user.username
        self.avatar.setText(display[0].upper() if display else "U")
        self.name_label.setText(display)
        self.handle_label.setText(f"@{user.username}")
        self.nickname_edit.setText(user.nickname or "")
        self.gender_combo.setCurrentText(user.gender or "其他")
        self.age_spin.setValue(user.age or 20)

        rated = self.main.rating_service.count_user_ratings(user.id)
        hist = self.main.history_service.count_user_history(user.id)
        self.stats_label.setText(f"评分 {rated} · 浏览 {hist}")

        self._refresh_ratings()
        self._refresh_history()

    def _refresh_ratings(self):
        user = self.main.get_user()
        rows = self.main.rating_service.get_user_ratings_with_movies(user.id)
        self.rating_table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            values = [str(r["id"]), r["title"], r["genre"] or "", f"{r['score']} 分", r["comment"] or ""]
            for col, val in enumerate(values):
                self.rating_table.setItem(row, col, QTableWidgetItem(val))

    def _refresh_history(self):
        user = self.main.get_user()
        rows = self.main.history_service.get_user_history_with_movies(user.id)
        self.history_table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            t = r["browse_time"].strftime("%Y-%m-%d %H:%M") if r.get("browse_time") else ""
            values = [str(r["id"]), r["title"], r["genre"] or "", t]
            for col, val in enumerate(values):
                self.history_table.setItem(row, col, QTableWidgetItem(val))

    # ---------- 事件 ----------

    def _save_profile(self):
        user = self.main.get_user()
        try:
            self.main.user_service.update_profile(
                user.id, self.nickname_edit.text().strip(),
                self.gender_combo.currentText(), self.age_spin.value(),
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "错误", f"保存失败：{exc}")
            return
        self.main.current_user = self.main.user_service.get_user(user.id)
        self.main.refresh_user_display()
        QMessageBox.information(self, "成功", "资料已更新")
        self.refresh()

    def _change_password(self):
        user = self.main.get_user()
        old = self.old_pwd.text()
        new = self.new_pwd.text()
        confirm = self.confirm_pwd.text()
        if new != confirm:
            QMessageBox.warning(self, "提示", "两次输入的新密码不一致")
            return
        ok, err = self.main.user_service.change_password(user.id, old, new)
        if not ok:
            QMessageBox.warning(self, "失败", err)
            return
        QMessageBox.information(self, "成功", "密码已修改")
        self.old_pwd.clear()
        self.new_pwd.clear()
        self.confirm_pwd.clear()

    def _delete_rating(self):
        row = self.rating_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要删除的评分")
            return
        rid = int(self.rating_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", "确定删除这条评分？") != QMessageBox.Yes:
            return
        self.main.rating_service.delete_rating(rid)
        self.refresh()

    def _clear_history(self):
        user = self.main.get_user()
        if QMessageBox.question(self, "确认", "确定清空全部浏览历史？") != QMessageBox.Yes:
            return
        self.main.history_service.clear_user_history(user.id)
        self.refresh()
