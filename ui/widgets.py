# -*- coding: utf-8 -*-
"""
通用界面组件
无边框影院海报墙卡片（Apple TV+ 风格）、矢量图标、流式布局与悬停矢量五星控件。
"""
import math

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt5.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter,
                         QPainterPath, QPen, QPixmap, QPolygonF,
                         QRadialGradient)
from PyQt5.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QLabel,
                             QLayout, QVBoxLayout, QWidget)


def apply_shadow(widget, blur=24, y_offset=6, alpha=60):
    """保留统一阴影辅助接口（暗色面板下采用克制微投影）。"""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


def harmonize_color(color_hex):
    """将类型颜色调制成沉稳的影院级配色。"""
    c = QColor(color_hex or "#6366F1")
    if not c.isValid():
        c = QColor("#6366F1")
    h = c.hueF()
    s = c.saturationF()
    if h < 0:
        return QColor("#334155"), QColor("#0F172A")
    top = QColor.fromHslF(h, min(max(s, 0.38), 0.62), 0.36)
    bottom = QColor.fromHslF(h, min(max(s, 0.44), 0.68), 0.14)
    return top, bottom


def make_icon(name, color="#94A3B8", size=20):
    """使用 QPainter 绘制高清矢量单色图标。"""
    dpr = 2
    pm = QPixmap(size * dpr, size * dpr)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    s = float(size)
    if name == "sparkles":
        path = QPainterPath()
        cx, cy, r = s * 0.45, s * 0.5, s * 0.34
        path.moveTo(cx, cy - r)
        path.quadTo(cx, cy, cx + r, cy)
        path.quadTo(cx, cy, cx, cy + r)
        path.quadTo(cx, cy, cx - r, cy)
        path.quadTo(cx, cy, cx, cy - r)
        p.drawPath(path)
        p.drawLine(QPointF(s * 0.78, s * 0.16), QPointF(s * 0.78, s * 0.34))
        p.drawLine(QPointF(s * 0.69, s * 0.25), QPointF(s * 0.87, s * 0.25))

    elif name == "bot":
        p.drawRoundedRect(QRectF(s * 0.16, s * 0.26, s * 0.68, s * 0.52), 4.0, 4.0)
        p.drawLine(QPointF(s * 0.50, s * 0.12), QPointF(s * 0.50, s * 0.26))
        p.drawEllipse(QRectF(s * 0.45, s * 0.08, s * 0.10, s * 0.10))
        p.drawEllipse(QRectF(s * 0.31, s * 0.43, s * 0.10, s * 0.10))
        p.drawEllipse(QRectF(s * 0.59, s * 0.43, s * 0.10, s * 0.10))
        p.drawLine(QPointF(s * 0.36, s * 0.64), QPointF(s * 0.64, s * 0.64))

    elif name == "search":
        p.drawEllipse(QRectF(s * 0.16, s * 0.16, s * 0.52, s * 0.52))
        p.drawLine(QPointF(s * 0.62, s * 0.62), QPointF(s * 0.84, s * 0.84))

    elif name == "layers":
        p.drawPolygon(QPolygonF([
            QPointF(s * 0.5, s * 0.14),
            QPointF(s * 0.86, s * 0.33),
            QPointF(s * 0.5, s * 0.52),
            QPointF(s * 0.14, s * 0.33),
        ]))
        p.drawPolyline(QPolygonF([
            QPointF(s * 0.14, s * 0.52),
            QPointF(s * 0.5, s * 0.71),
            QPointF(s * 0.86, s * 0.52),
        ]))
        p.drawPolyline(QPolygonF([
            QPointF(s * 0.14, s * 0.69),
            QPointF(s * 0.5, s * 0.88),
            QPointF(s * 0.86, s * 0.69),
        ]))

    elif name == "movie":
        p.drawRoundedRect(QRectF(s * 0.15, s * 0.2, s * 0.7, s * 0.6), 2.5, 2.5)
        p.drawLine(QPointF(s * 0.32, s * 0.2), QPointF(s * 0.32, s * 0.8))
        p.drawLine(QPointF(s * 0.68, s * 0.2), QPointF(s * 0.68, s * 0.8))
        p.drawLine(QPointF(s * 0.15, s * 0.5), QPointF(s * 0.32, s * 0.5))
        p.drawLine(QPointF(s * 0.68, s * 0.5), QPointF(s * 0.85, s * 0.5))

    elif name == "users":
        p.drawEllipse(QRectF(s * 0.32, s * 0.18, s * 0.28, s * 0.28))
        path = QPainterPath()
        path.moveTo(s * 0.16, s * 0.82)
        path.cubicTo(s * 0.16, s * 0.60, s * 0.76, s * 0.60, s * 0.76, s * 0.82)
        p.drawPath(path)

    elif name == "star":
        pts = []
        cx, cy = s * 0.5, s * 0.52
        r_out, r_in = s * 0.36, s * 0.16
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            r = r_out if i % 2 == 0 else r_in
            pts.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
        p.drawPolygon(QPolygonF(pts))

    elif name == "refresh":
        p.drawArc(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64), 30 * 16, 285 * 16)
        p.drawPolyline(QPolygonF([
            QPointF(s * 0.68, s * 0.16),
            QPointF(s * 0.80, s * 0.30),
            QPointF(s * 0.64, s * 0.35),
        ]))

    elif name == "plus":
        p.drawLine(QPointF(s * 0.5, s * 0.2), QPointF(s * 0.5, s * 0.8))
        p.drawLine(QPointF(s * 0.2, s * 0.5), QPointF(s * 0.8, s * 0.5))

    elif name == "edit":
        p.drawPolygon(QPolygonF([
            QPointF(s * 0.68, s * 0.16),
            QPointF(s * 0.84, s * 0.32),
            QPointF(s * 0.36, s * 0.80),
            QPointF(s * 0.18, s * 0.82),
            QPointF(s * 0.20, s * 0.64),
        ]))

    elif name == "trash":
        p.drawLine(QPointF(s * 0.18, s * 0.28), QPointF(s * 0.82, s * 0.28))
        p.drawLine(QPointF(s * 0.38, s * 0.16), QPointF(s * 0.62, s * 0.16))
        p.drawRoundedRect(QRectF(s * 0.26, s * 0.28, s * 0.48, s * 0.56), 2.0, 2.0)
        p.drawLine(QPointF(s * 0.42, s * 0.42), QPointF(s * 0.42, s * 0.70))
        p.drawLine(QPointF(s * 0.58, s * 0.42), QPointF(s * 0.58, s * 0.70))

    elif name == "logout":
        p.drawPolyline(QPolygonF([
            QPointF(s * 0.46, s * 0.18),
            QPointF(s * 0.20, s * 0.18),
            QPointF(s * 0.20, s * 0.82),
            QPointF(s * 0.46, s * 0.82),
        ]))
        p.drawLine(QPointF(s * 0.42, s * 0.50), QPointF(s * 0.82, s * 0.50))
        p.drawPolyline(QPolygonF([
            QPointF(s * 0.68, s * 0.34),
            QPointF(s * 0.84, s * 0.50),
            QPointF(s * 0.68, s * 0.66),
        ]))

    elif name == "settings":
        p.drawEllipse(QRectF(s * 0.34, s * 0.34, s * 0.32, s * 0.32))
        p.drawEllipse(QRectF(s * 0.45, s * 0.45, s * 0.10, s * 0.10))
        for k in range(8):
            ang = math.radians(22.5 + k * 45)
            inner = QPointF(s * 0.5 + s * 0.16 * math.cos(ang), s * 0.5 + s * 0.16 * math.sin(ang))
            outer = QPointF(s * 0.5 + s * 0.30 * math.cos(ang), s * 0.5 + s * 0.30 * math.sin(ang))
            p.drawLine(inner, outer)

    elif name == "chart-bar":
        p.drawLine(QPointF(s * 0.16, s * 0.82), QPointF(s * 0.84, s * 0.82))
        p.drawRoundedRect(QRectF(s * 0.22, s * 0.48, s * 0.14, s * 0.34), 2.0, 2.0)
        p.drawRoundedRect(QRectF(s * 0.43, s * 0.22, s * 0.14, s * 0.60), 2.0, 2.0)
        p.drawRoundedRect(QRectF(s * 0.64, s * 0.36, s * 0.14, s * 0.46), 2.0, 2.0)

    p.end()
    return QIcon(pm)


def clear_layout(layout: QLayout):
    """清空布局中所有子控件与子布局。"""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())


def populate_grid(grid_layout, cards, columns=4):
    """兼容旧网格布局或 FlowLayout 的统一填充函数。"""
    clear_layout(grid_layout)
    if isinstance(grid_layout, FlowLayout):
        for card in cards:
            grid_layout.addWidget(card)
        return
    grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    for i, card in enumerate(cards):
        row, col = divmod(i, columns)
        grid_layout.addWidget(card, row, col)


class FlowLayout(QLayout):
    """响应式流式布局，随容器宽度自动换行排列。"""

    def __init__(self, parent=None, margin=0, h_spacing=20, v_spacing=22):
        super().__init__(parent)
        self._items = []
        self._h_space = h_spacing
        self._v_space = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(left, top, -right, -bottom)
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            sz = item.sizeHint()
            next_x = x + sz.width() + self._h_space
            if next_x - self._h_space > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + self._v_space
                next_x = x + sz.width() + self._h_space
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), sz))
            x = next_x
            line_height = max(line_height, sz.height())

        return y + line_height - rect.y() + bottom


class FlowContainer(QWidget):
    """配合 QScrollArea 或常规布局使用的流式容器。"""

    def __init__(self, h_spacing=20, v_spacing=22, margin=2, parent=None):
        super().__init__(parent)
        self.setObjectName("flowContainer")
        self.setStyleSheet("QWidget#flowContainer { background: transparent; }")
        self.flow = FlowLayout(self, margin=margin, h_spacing=h_spacing, v_spacing=v_spacing)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.flow.heightForWidth(width)


class MoviePoster(QWidget):
    """2:3 纯净影院级海报（支持悬浮高亮边框、TMDB 评分浮标、推荐契合度浮标）。"""

    def __init__(self, movie, radius=12, large=False, score=None, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.radius = radius
        self.large = large
        self.score = score
        self._hovered = False
        self._pixmap = None
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._load_online()

    def set_hovered(self, hovered):
        if self._hovered != hovered:
            self._hovered = hovered
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        clip = QPainterPath()
        clip.addRoundedRect(rect, self.radius, self.radius)
        p.setClipPath(clip)

        if self._pixmap is not None and not self._pixmap.isNull():
            p.drawPixmap(rect, self._pixmap, self._source_rect(w, h))
            vignette = QLinearGradient(0, 0, 0, h)
            vignette.setColorAt(0.0, QColor(0, 0, 0, 55))
            vignette.setColorAt(0.30, QColor(0, 0, 0, 0))
            vignette.setColorAt(0.74, QColor(0, 0, 0, 0))
            vignette.setColorAt(1.0, QColor(0, 0, 0, 115))
            p.fillRect(rect, vignette)
        else:
            self._paint_fallback(p, w, h, rect)

        # 左上角：推荐契合度角标
        if self.score is not None and self.score > 0 and not self.large:
            txt = f"{int(round(min(1.0, self.score) * 100))}% 匹配" if self.score <= 1.0 else f"★ {self.score:.2f}"
            f = QFont("Microsoft YaHei UI", 8)
            f.setBold(True)
            p.setFont(f)
            bw = p.fontMetrics().horizontalAdvance(txt) + 14
            b_rect = QRectF(8, 8, bw, 22)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(2, 132, 199, 230))
            p.drawRoundedRect(b_rect, 6, 6)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(b_rect, Qt.AlignCenter, txt)

        # 右上角：TMDB 评分角标
        vote = getattr(self.movie, "vote_average", 0) or 0
        if vote > 0 and not self.large:
            txt = f"★ {vote:.1f}"
            f = QFont("Microsoft YaHei UI", 8)
            f.setBold(True)
            p.setFont(f)
            bw = p.fontMetrics().horizontalAdvance(txt) + 12
            b_rect = QRectF(w - bw - 8, 8, bw, 22)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(7, 9, 14, 205))
            p.drawRoundedRect(b_rect, 6, 6)
            p.setPen(QColor("#FBBF24"))
            p.drawText(b_rect, Qt.AlignCenter, txt)

        # 边框（平时极细冷灰玻璃描边，悬停亮起冰川青蓝轮廓光）
        p.setBrush(Qt.NoBrush)
        if self._hovered:
            p.setPen(QPen(QColor("#38BDF8"), 2.5))
            p.drawRoundedRect(rect.adjusted(1.2, 1.2, -1.2, -1.2), self.radius, self.radius)
        else:
            p.setPen(QPen(QColor(148, 163, 184, 28), 1.0))
            p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), self.radius, self.radius)
        p.end()

    def _paint_fallback(self, p, w, h, rect):
        top_c, bot_c = harmonize_color(self.movie.poster_color)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, top_c)
        grad.setColorAt(1.0, bot_c)
        p.fillRect(rect, grad)

        spot = QRadialGradient(QPointF(w * 0.5, h * 0.24), w * 0.8)
        spot.setColorAt(0.0, QColor(255, 255, 255, 40))
        spot.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(rect, spot)

        p.setPen(QPen(QColor(255, 255, 255, 28), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(10, 10, w - 20, h - 20), max(4, self.radius - 4), max(4, self.radius - 4))

        f_title = QFont("Microsoft YaHei UI", 12 if not self.large else 15)
        f_title.setBold(True)
        p.setFont(f_title)
        p.setPen(QColor(255, 255, 255, 245))
        title_rect = QRectF(16, 44, w - 32, h - 92)
        p.drawText(title_rect, Qt.AlignCenter | Qt.TextWordWrap, self.movie.title)

        year = getattr(self.movie, "release_year", None)
        sub_text = f"{self.movie.director or ''} · {year}" if year else (self.movie.director or "")
        if sub_text.strip(" ·"):
            f_sub = QFont("Microsoft YaHei UI", 8 if not self.large else 9)
            p.setFont(f_sub)
            p.setPen(QColor(255, 255, 255, 185))
            sub_rect = QRectF(16, h - 38, w - 32, 20)
            elided = p.fontMetrics().elidedText(sub_text.strip(" ·"), Qt.ElideRight, int(sub_rect.width()))
            p.drawText(sub_rect, Qt.AlignCenter, elided)

    def _load_online(self):
        url = getattr(self.movie, "poster_url", "") or ""
        if not url:
            return
        try:
            from ui.cover_loader import get_loader
            get_loader().load(url, self._on_pixmap)
        except Exception:  # noqa: BLE001
            pass

    def _on_pixmap(self, pixmap):
        if pixmap is None or pixmap.isNull():
            return
        self._pixmap = pixmap
        self.update()

    def _source_rect(self, w, h):
        pw = float(self._pixmap.width())
        ph = float(self._pixmap.height())
        if pw <= 0 or ph <= 0:
            return QRectF(0, 0, pw, ph)
        target_ratio = w / h
        src_ratio = pw / ph
        if src_ratio > target_ratio:
            new_w = ph * target_ratio
            return QRectF((pw - new_w) / 2.0, 0, new_w, ph)
        new_h = pw / target_ratio
        return QRectF(0, (ph - new_h) / 2.0, pw, new_h)


class MovieCard(QFrame):
    """无边框极简流媒体海报卡片（纯净 2:3 海报 + 下方克制双行排版）。"""
    clicked = pyqtSignal(object)

    def __init__(self, movie, score=None, compact=False, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.compact = compact
        self.setObjectName("movieCard")
        if compact:
            self.setFixedSize(166, 294)
        else:
            self.setFixedSize(188, 336)
        self.setCursor(Qt.PointingHandCursor)
        self._build(score)

    def _build(self, score):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.poster = MoviePoster(self.movie, radius=12, score=score)
        self.poster.setFixedHeight(238 if self.compact else 274)

        title = QLabel(self.movie.title)
        title.setObjectName("cardTitle")
        title.setWordWrap(False)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # 用 QFontMetrics 省略超长片名，保持整行视觉整齐
        fm = title.fontMetrics()
        max_w = 160 if self.compact else 184
        title.setText(fm.elidedText(self.movie.title or "", Qt.ElideRight, max_w))

        year = getattr(self.movie, "release_year", None)
        genre = (self.movie.genre or "电影").split("/")[0]
        meta_text = f"{year} · {genre}" if year else genre
        meta = QLabel(meta_text)
        meta.setObjectName("cardMeta")

        layout.addWidget(self.poster)
        layout.addWidget(title)
        layout.addWidget(meta)
        layout.addStretch()

        for w in (title, meta):
            w.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def enterEvent(self, event):
        self.poster.set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.poster.set_hovered(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.movie)
        super().mousePressEvent(event)


class StarRating(QWidget):
    """暗色主题下的矢量五星评分控件（支持悬停预览）。"""
    rating_changed = pyqtSignal(int)

    LABELS = {
        0: "点击星星评分",
        1: "1 分 · 较差",
        2: "2 分 · 一般",
        3: "3 分 · 还不错",
        4: "4 分 · 推荐观影",
        5: "5 分 · 强烈推荐",
    }

    def __init__(self, score=0, parent=None):
        super().__init__(parent)
        self.score = score
        self.hover_score = 0
        self.star_size = 32
        self.gap = 6
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(38)
        self.setMinimumWidth(5 * self.star_size + 4 * self.gap + 150)

    def set_score(self, score):
        self.score = max(0, min(5, int(score)))
        self.update()
        self.rating_changed.emit(self.score)

    def value(self):
        return self.score

    def _star_at(self, x):
        for i in range(5):
            left = i * (self.star_size + self.gap)
            if left <= x <= left + self.star_size + self.gap:
                return i + 1
        return 0

    def mouseMoveEvent(self, event):
        hs = self._star_at(event.x())
        if hs != self.hover_score:
            self.hover_score = hs
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hover_score = 0
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            s = self._star_at(event.x())
            if s > 0:
                self.set_score(s)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        active = self.hover_score if self.hover_score > 0 else self.score
        cy = self.height() / 2.0

        for i in range(1, 6):
            cx = (i - 1) * (self.star_size + self.gap) + self.star_size / 2.0
            pts = []
            r_out = self.star_size * 0.44
            r_in = self.star_size * 0.20
            for k in range(10):
                ang = math.radians(-90 + k * 36)
                r = r_out if k % 2 == 0 else r_in
                pts.append(QPointF(cx + r * math.cos(ang), cy + r * math.sin(ang)))

            if i <= active:
                fill = QColor("#F59E0B") if self.hover_score == 0 or i <= self.score else QColor("#FBBF24")
                p.setBrush(fill)
                p.setPen(QPen(QColor("#F59E0B"), 1.0))
            else:
                p.setBrush(QColor("#23283B"))
                p.setPen(QPen(QColor("#363E5C"), 1.0))
            p.drawPolygon(QPolygonF(pts))

        text_x = 5 * (self.star_size + self.gap) + 10
        text_rect = QRectF(text_x, 0, self.width() - text_x, self.height())
        font = QFont("Microsoft YaHei UI", 10)
        font.setBold(active > 0)
        p.setFont(font)
        p.setPen(QColor("#FBBF24") if active > 0 else QColor("#64748B"))
        p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.LABELS.get(active, f"{active} 分"))
        p.end()