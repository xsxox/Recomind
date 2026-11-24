# -*- coding: utf-8 -*-
"""
数据管理页
采用三栏 KPI 卡片 + 分段胶囊切换器 + 现代无网格线数据表。
"""
from datetime import datetime

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QComboBox, QDialog, QFrame, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QSpinBox, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget)

from services.movie_service import MovieService
from services.rating_service import RatingService
from services.user_service import UserService
from ui.styles import genre_color
from ui.widgets import apply_shadow, make_icon
from utils.logger import get_logger

logger = get_logger("ui.manage")

MOVIE_HEADERS = ["ID", "片名", "导演", "制片公司", "类型", "上映年份"]
USER_HEADERS = ["ID", "用户名", "昵称", "性别", "年龄", "注册时间"]
RATING_HEADERS = ["ID", "用户", "电影", "评分", "评语", "评分时间"]


class MovieEditDialog(QDialog):
    """新增/编辑电影的现代化表单对话框。"""

    def __init__(self, movie=None, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.setWindowTitle("编辑电影" if movie else "新增电影")
        self.setFixedSize(560, 650)
        self._build()

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #374151; font-size: 13px; font-weight: bold;")
        return lbl

    def _build(self):
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 26)
        layout.setSpacing(10)

        heading = QLabel("编辑电影信息" if self.movie else "新增馆藏电影")
        heading.setStyleSheet("font-size: 22px; font-weight: bold; color: #111827;")
        layout.addWidget(heading)
        layout.addSpacing(8)

        layout.addWidget(self._label("片名 *"))
        self.title_edit = QLineEdit()
        self.title_edit.setMinimumHeight(42)
        self.title_edit.setPlaceholderText("请输入完整片名")
        layout.addWidget(self.title_edit)

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        c1, c2 = QVBoxLayout(), QVBoxLayout()
        c1.setSpacing(4)
        c2.setSpacing(4)
        c1.addWidget(self._label("导演"))
        self.director_edit = QLineEdit()
        self.director_edit.setMinimumHeight(42)
        c1.addWidget(self.director_edit)

        c2.addWidget(self._label("制片公司"))
        self.studio_edit = QLineEdit()
        self.studio_edit.setMinimumHeight(42)
        c2.addWidget(self.studio_edit)
        row1.addLayout(c1)
        row1.addLayout(c2)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        c3, c4 = QVBoxLayout(), QVBoxLayout()
        c3.setSpacing(4)
        c4.setSpacing(4)
        c3.addWidget(self._label("类型"))
        self.genre_combo = QComboBox()
        self.genre_combo.setMinimumHeight(42)
        self.genre_combo.setEditable(True)
        self.genre_combo.addItems(["科幻", "动作", "剧情", "喜剧", "动画", "悬疑", "犯罪", "爱情", "历史", "战争", "奇幻"])
        c3.addWidget(self.genre_combo)

        c4.addWidget(self._label("上映年份"))
        self.year_spin = QSpinBox()
        self.year_spin.setMinimumHeight(42)
        self.year_spin.setRange(0, 2100)
        self.year_spin.setValue(datetime.now().year)
        c4.addWidget(self.year_spin)
        row2.addLayout(c3)
        row2.addLayout(c4)
        layout.addLayout(row2)

        layout.addWidget(self._label("内容简介（用于 NLP 特征提取）"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMinimumHeight(160)
        self.desc_edit.setPlaceholderText("输入电影简介或内容摘要...")
        layout.addWidget(self.desc_edit, 1)

        layout.addSpacing(10)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setMinimumHeight(42)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("保存电影")
        save_btn.setMinimumHeight(42)
        save_btn.clicked.connect(self._on_save)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        if self.movie:
            self.title_edit.setText(self.movie.title)
            self.director_edit.setText(self.movie.director)
            self.studio_edit.setText(self.movie.studio)
            self.genre_combo.setCurrentText(self.movie.genre)
            self.year_spin.setValue(self.movie.release_year or datetime.now().year)
            self.desc_edit.setPlainText(self.movie.description)

    def _on_save(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "提示", "片名不能为空")
            return
        self.accept()

    def values(self):
        return {
            "title": self.title_edit.text().strip(),
            "director": self.director_edit.text().strip(),
            "studio": self.studio_edit.text().strip(),
            "genre": self.genre_combo.currentText().strip(),
            "release_year": self.year_spin.value(),
            "description": self.desc_edit.toPlainText().strip(),
            "poster_color": genre_color(self.genre_combo.currentText().strip()),
        }


class ManagePage(QWidget):
    """数据管理页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.movie_service = MovieService()
        self.user_service = UserService()
        self.rating_service = RatingService()
        self._seg_buttons = []
        self._build()
        self.refresh_all()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(18)

        # 标题
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("数据管理")
        title.setObjectName("pageTitle")
        subtitle = QLabel("统一维护电影语料库、用户档案与真实评分交互记录")
        subtitle.setObjectName("subText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        root.addLayout(title_box)

        # 三栏 KPI 卡片
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.movies_stat_val, card1 = self._make_stat_card("馆藏电影", "movie", "#4F46E5", "#EEF2FF")
        self.users_stat_val, card2 = self._make_stat_card("注册用户", "users", "#0284C7", "#E0F2FE")
        self.ratings_stat_val, card3 = self._make_stat_card("评分记录", "star", "#D97706", "#FEF3C7")
        stats_row.addWidget(card1)
        stats_row.addWidget(card2)
        stats_row.addWidget(card3)
        root.addLayout(stats_row)

        # 主白卡容器（顶部胶囊切换 + 表格内容）
        main_card = QFrame()
        main_card.setObjectName("panel")
        apply_shadow(main_card, blur=20, y_offset=4, alpha=12)
        card_layout = QVBoxLayout(main_card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(14)

        top_bar = QHBoxLayout()
        seg = QFrame()
        seg.setObjectName("segmentBox")
        seg_layout = QHBoxLayout(seg)
        seg_layout.setContentsMargins(4, 4, 4, 4)
        seg_layout.setSpacing(4)

        for idx, name in enumerate(["电影管理", "用户管理", "评分数据"]):
            btn = QPushButton(name)
            btn.setObjectName("segmentBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _c, i=idx: self._switch_tab(i))
            self._seg_buttons.append(btn)
            seg_layout.addWidget(btn)
        self._seg_buttons[0].setChecked(True)

        top_bar.addWidget(seg)
        top_bar.addStretch()

        refresh_btn = QPushButton("  刷新数据")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.setIcon(make_icon("refresh", "#374151", 16))
        refresh_btn.setIconSize(QSize(16, 16))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_all)
        top_bar.addWidget(refresh_btn)

        card_layout.addLayout(top_bar)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_movie_tab())
        self.stack.addWidget(self._build_user_tab())
        self.stack.addWidget(self._build_rating_tab())
        card_layout.addWidget(self.stack, 1)

        root.addWidget(main_card, 1)

    def _switch_tab(self, index):
        for i, btn in enumerate(self._seg_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def _make_stat_card(self, label_text, icon_name, accent_color, bg_color):
        card = QFrame()
        card.setObjectName("statCard")
        apply_shadow(card, blur=16, y_offset=3, alpha=12)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)

        icon_box = QLabel()
        icon_box.setFixedSize(50, 50)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setPixmap(make_icon(icon_name, accent_color, 24).pixmap(24, 24))
        icon_box.setStyleSheet(f"background-color: {bg_color}; border-radius: 13px;")

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        val_lbl = QLabel("0")
        val_lbl.setObjectName("statNumber")
        lbl = QLabel(label_text)
        lbl.setObjectName("statLabel")
        text_col.addWidget(val_lbl)
        text_col.addWidget(lbl)

        layout.addWidget(icon_box)
        layout.addLayout(text_col, 1)
        return val_lbl, card

    # ---------- 各视图 ----------

    def _build_movie_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.add_btn = QPushButton("  新增电影")
        self.add_btn.setIcon(make_icon("plus", "#FFFFFF", 16))
        self.add_btn.setIconSize(QSize(16, 16))
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_movie)

        self.edit_btn = QPushButton("  编辑选中")
        self.edit_btn.setObjectName("secondaryBtn")
        self.edit_btn.setIcon(make_icon("edit", "#374151", 16))
        self.edit_btn.setIconSize(QSize(16, 16))
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self._edit_movie)

        self.del_movie_btn = QPushButton("  删除选中")
        self.del_movie_btn.setObjectName("dangerBtn")
        self.del_movie_btn.setIcon(make_icon("trash", "#DC2626", 16))
        self.del_movie_btn.setIconSize(QSize(16, 16))
        self.del_movie_btn.setCursor(Qt.PointingHandCursor)
        self.del_movie_btn.clicked.connect(self._delete_movie)

        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.del_movie_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.movie_table = self._make_table(MOVIE_HEADERS)
        layout.addWidget(self.movie_table)
        return widget

    def _build_user_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(12)

        btn_row = QHBoxLayout()
        self.del_user_btn = QPushButton("  删除选中用户")
        self.del_user_btn.setObjectName("dangerBtn")
        self.del_user_btn.setIcon(make_icon("trash", "#DC2626", 16))
        self.del_user_btn.setIconSize(QSize(16, 16))
        self.del_user_btn.setCursor(Qt.PointingHandCursor)
        self.del_user_btn.clicked.connect(self._delete_user)
        btn_row.addWidget(self.del_user_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.user_table = self._make_table(USER_HEADERS)
        layout.addWidget(self.user_table)
        return widget

    def _build_rating_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 0)
        self.rating_table = self._make_table(RATING_HEADERS)
        layout.addWidget(self.rating_table)
        return widget

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
        table.verticalHeader().setDefaultSectionSize(48)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        return table

    # ---------- 数据刷新 ----------

    def refresh_all(self):
        self._refresh_stats()
        self._refresh_movies()
        self._refresh_users()
        self._refresh_ratings()

    def _refresh_stats(self):
        self.movies_stat_val.setText(str(self.movie_service.count_movies()))
        self.users_stat_val.setText(str(self.user_service.count_users()))
        self.ratings_stat_val.setText(str(self.rating_service.count_ratings()))

    def _refresh_movies(self):
        movies = self.movie_service.list_movies()
        self.movie_table.setRowCount(len(movies))
        for row, b in enumerate(movies):
            values = [str(b.id), b.title, b.director, b.studio, b.genre, str(b.release_year or "")]
            for col, val in enumerate(values):
                self.movie_table.setItem(row, col, QTableWidgetItem(val))

    def _refresh_users(self):
        users = self.user_service.list_users()
        self.user_table.setRowCount(len(users))
        for row, u in enumerate(users):
            reg_time = u.register_time.strftime("%Y-%m-%d %H:%M") if u.register_time else ""
            values = [str(u.id), u.username, u.nickname, u.gender, str(u.age or ""), reg_time]
            for col, val in enumerate(values):
                self.user_table.setItem(row, col, QTableWidgetItem(val))

    def _refresh_ratings(self):
        ratings = self.rating_service.list_ratings_with_names()
        self.rating_table.setRowCount(len(ratings))
        for row, r in enumerate(ratings):
            rtime = r["rating_time"].strftime("%Y-%m-%d %H:%M") if r.get("rating_time") else ""
            values = [
                str(r["id"]),
                r["username"],
                r["title"],
                f"{r['score']} 分",
                r["comment"] or "",
                rtime,
            ]
            for col, val in enumerate(values):
                self.rating_table.setItem(row, col, QTableWidgetItem(val))

    # ---------- 电影增删改 ----------

    def _add_movie(self):
        dlg = MovieEditDialog(parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        v = dlg.values()
        try:
            self.movie_service.add_movie(v["title"], v["director"], v["studio"],
                                       v["genre"], v["release_year"],
                                       v["description"], v["poster_color"])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "错误", f"新增失败：{exc}")
            return
        self.refresh_all()

    def _edit_movie(self):
        row = self.movie_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要编辑的电影")
            return
        movie_id = int(self.movie_table.item(row, 0).text())
        movie = self.movie_service.get_movie(movie_id)
        dlg = MovieEditDialog(movie=movie, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        v = dlg.values()
        try:
            self.movie_service.update_movie(movie_id, v["title"], v["director"], v["studio"],
                                          v["genre"], v["release_year"],
                                          v["description"], v["poster_color"])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "错误", f"编辑失败：{exc}")
            return
        self.refresh_all()

    def _delete_movie(self):
        row = self.movie_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要删除的电影")
            return
        movie_id = int(self.movie_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", "删除电影会同时删除其评分与浏览记录，确定删除？") != QMessageBox.Yes:
            return
        self.movie_service.delete_movie(movie_id)
        self.refresh_all()

    def _delete_user(self):
        row = self.user_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要删除的用户")
            return
        user_id = int(self.user_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", "确定删除该用户及其全部数据？") != QMessageBox.Yes:
            return
        self.user_service.delete_user(user_id)
        self.refresh_all()