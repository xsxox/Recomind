# -*- coding: utf-8 -*-
"""
界面样式模块
现代极简浅色风格（Apple Movies / Linear / Notion 设计语言）。
"""

STYLE_SHEET = """
* {
    font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 15px;
    color: #111827;
}

QMainWindow, QDialog {
    background-color: #F6F7FB;
}

/* ---------- 极简白色侧边栏 ---------- */
QFrame#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #EAECEF;
}

QLabel#brandTitle {
    color: #111827;
    font-size: 21px;
    font-weight: bold;
    letter-spacing: 0.5px;
}

QLabel#brandSub {
    color: #9CA3AF;
    font-size: 12px;
    font-weight: 500;
}

QPushButton#navBtn {
    background-color: transparent;
    color: #4B5563;
    border: none;
    border-radius: 10px;
    padding: 11px 14px;
    text-align: left;
    font-size: 15px;
    font-weight: 500;
    outline: none;
}

QPushButton#navBtn:hover {
    background-color: #F3F4F6;
    color: #111827;
}

QPushButton#navBtn:checked {
    background-color: #EEF2FF;
    color: #4F46E5;
    font-weight: bold;
}

QFrame#userCard {
    background-color: #F8FAFC;
    border: 1px solid #EAECEF;
    border-radius: 14px;
}

QLabel#userAvatar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);
    color: #FFFFFF;
    font-size: 16px;
    font-weight: bold;
    border-radius: 19px;
}

QLabel#userName {
    color: #111827;
    font-size: 14px;
    font-weight: bold;
}

QLabel#userHandle {
    color: #6B7280;
    font-size: 12px;
}

QPushButton#logoutBtn {
    background-color: #FFFFFF;
    color: #4B5563;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 500;
    outline: none;
}

QPushButton#logoutBtn:hover {
    background-color: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FECACA;
}

/* ---------- 排版层级 ---------- */
QLabel#heroGreeting {
    font-size: 26px;
    font-weight: bold;
    color: #0F172A;
}

QLabel#pageTitle {
    font-size: 24px;
    font-weight: bold;
    color: #0F172A;
}

QLabel#sectionTitle {
    font-size: 18px;
    font-weight: bold;
    color: #111827;
}

QLabel#subText {
    font-size: 14px;
    color: #6B7280;
}

QLabel#cardTitle {
    font-size: 15px;
    font-weight: bold;
    color: #111827;
}

QLabel#cardAuthor {
    font-size: 13px;
    color: #6B7280;
}

QLabel#cardInfo {
    font-size: 14px;
    color: #6B7280;
}

QLabel#catPill {
    background-color: #F3F4F6;
    color: #4B5563;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 12px;
    font-weight: 500;
}

QLabel#matchPill {
    background-color: #EEF2FF;
    color: #4F46E5;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 12px;
    font-weight: bold;
}

/* ---------- 卡片容器 ---------- */
QFrame#panel {
    background-color: #FFFFFF;
    border: 1px solid #EAECEF;
    border-radius: 16px;
}

QFrame#spotlightBar {
    background-color: #FFFFFF;
    border: 1.5px solid #E5E7EB;
    border-radius: 16px;
}

QFrame#movieCard {
    background-color: #FFFFFF;
    border: 1px solid #EAECEF;
    border-radius: 16px;
}

QFrame#movieCard:hover {
    border: 1.5px solid #6366F1;
    background-color: #FFFFFF;
}

QFrame#statCard {
    background-color: #FFFFFF;
    border: 1px solid #EAECEF;
    border-radius: 16px;
}

QLabel#statNumber {
    font-size: 28px;
    font-weight: bold;
    color: #111827;
}

QLabel#statLabel {
    font-size: 13px;
    color: #6B7280;
    font-weight: 500;
}

/* ---------- 按钮 ---------- */
QPushButton {
    background-color: #4F46E5;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
    outline: none;
}

QPushButton:hover {
    background-color: #4338CA;
}

QPushButton:pressed {
    background-color: #3730A3;
}

QPushButton#secondaryBtn {
    background-color: #FFFFFF;
    color: #374151;
    border: 1px solid #E5E7EB;
    font-weight: 500;
}

QPushButton#secondaryBtn:hover {
    background-color: #F9FAFB;
    border: 1px solid #D1D5DB;
    color: #111827;
}

QPushButton#dangerBtn {
    background-color: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FECACA;
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background-color: #EF4444;
    color: #FFFFFF;
    border: 1px solid #EF4444;
}

QPushButton#chipBtn {
    background-color: #FFFFFF;
    color: #4B5563;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#chipBtn:hover {
    background-color: #EEF2FF;
    color: #4F46E5;
    border: 1px solid #C7D2FE;
}

/* ---------- 分段胶囊切换器 ---------- */
QFrame#segmentBox {
    background-color: #EDEFF5;
    border-radius: 12px;
}

QPushButton#segmentBtn {
    background-color: transparent;
    color: #6B7280;
    border: none;
    border-radius: 9px;
    padding: 8px 18px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#segmentBtn:hover {
    color: #111827;
}

QPushButton#segmentBtn:checked {
    background-color: #FFFFFF;
    color: #111827;
    font-weight: bold;
}

/* ---------- 现代填充态输入框 ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #F3F4F6;
    border: 1.5px solid transparent;
    border-radius: 10px;
    padding: 9px 14px;
    font-size: 15px;
    color: #111827;
    selection-background-color: #4F46E5;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    background-color: #FFFFFF;
    border: 1.5px solid #4F46E5;
}

QLineEdit#spotlightInput {
    background-color: transparent;
    border: none;
    padding: 8px 6px;
    font-size: 16px;
    color: #111827;
}

QLineEdit#spotlightInput:focus {
    background-color: transparent;
    border: none;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 4px;
    selection-background-color: #EEF2FF;
    selection-color: #4F46E5;
    font-size: 14px;
    outline: 0;
}

QComboBox QAbstractItemView::item {
    min-height: 36px;
    padding: 4px 10px;
    border-radius: 6px;
}

/* ---------- 现代无网格线表格 ---------- */
QTableWidget {
    background-color: #FFFFFF;
    alternate-background-color: #FAFAFC;
    border: none;
    font-size: 14px;
    selection-background-color: #EEF2FF;
    selection-color: #1E1B4B;
    outline: 0;
}

QTableWidget::item {
    padding: 10px 12px;
    border-bottom: 1px solid #F1F5F9;
}

QHeaderView::section {
    background-color: #FFFFFF;
    color: #6B7280;
    padding: 12px 12px;
    border: none;
    border-bottom: 1.5px solid #EAECEF;
    font-size: 13px;
    font-weight: bold;
}

/* ---------- 滚动条 & 弹窗 ---------- */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 0;
}

QScrollBar::handle:vertical {
    background: #D1D5DB;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #9CA3AF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMessageBox {
    background-color: #FFFFFF;
}

QMessageBox QLabel {
    font-size: 15px;
    color: #111827;
}
"""


def genre_color(genre):
    """根据类型返回海报颜色（兜底默认色）。"""
    from data.sample_data import CATEGORY_COLORS, DEFAULT_COLOR
    return CATEGORY_COLORS.get(genre, DEFAULT_COLOR)