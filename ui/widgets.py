# -*- coding: utf-8 -*-
"""
通用界面组件
包含矢量图标生成、自绘精装电影海报、自适应流式布局、电影卡片及矢量五星评分控件。
"""
import math

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt5.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter,
                         QPainterPath, QPen, QPixmap, QPolygonF)
from PyQt5.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                             QLabel, QLayout, QVBoxLayout, QWidget)


def apply_shadow(widget, blur=20, y_offset=4, alpha=16):
    """为卡片添加轻盈柔和的阴影。"""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(shadow)


def harmonize_color(color_hex):
    """将普通类型颜色柔化并加深为更有质感的高级出版色调。"""
    c = QColor(color_hex or "#4F46E5")
    if not c.isValid():
        c = QColor("#4F46E5")
    h = c.hueF()
    s = c.saturationF()
    if h < 0:
        return QColor("#475569"), QColor("#1E293B")
    top = QColor.fromHslF(h, min(max(s, 0.35), 0.62), 0.46)
    bottom = QColor.fromHslF(h, min(max(s, 0.42), 0.68), 0.28)
    return top, bottom


def make_icon(name, color="#4B5563", size=20):
    """使用 QPainter 绘制高清矢量单色图标（支持高分屏）。"""
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
        p.drawRoundedRect(QRectF(s * 0.2, s * 0.15, s * 0.6, s * 0.7), 2.5, 2.5)
        p.drawLine(QPointF(s * 0.36, s * 0.15), QPointF(s * 0.36, s * 0.85))

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
    """响应式流式布局，随容器宽度自动换行排列卡片。"""

    def __init__(self, parent=None, margin=0, h_spacing=18, v_spacing=18):
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
    """配合 QScrollArea 使用的流式容器，确保滚动高度随宽度动态更新。"""

    def __init__(self, h_spacing=18, v_spacing=18, parent=None):
        super().__init__(parent)
        self.setObjectName("flowContainer")
        self.setStyleSheet("QWidget#flowContainer { background: transparent; }")
        self.flow = FlowLayout(self, margin=2, h_spacing=h_spacing, v_spacing=v_spacing)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.flow.heightForWidth(width)


class MoviePoster(QWidget):
    """使用 QPainter 绘制的精装电影海报。"""

    def __init__(self, movie, radius=10, large=False, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.radius = radius
        self.large = large
        self._pixmap = None
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._load_online()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        clip = QPainterPath()
        clip.addRoundedRect(rect, self.radius, self.radius)
        p.setClipPath(clip)

        if self._pixmap is not None and not self._pixmap.isNull():
            p.drawPixmap(QRectF(0, 0, w, h), self._pixmap, self._source_rect(w, h))
            p.end()
            return

        top_c, bot_c = harmonize_color(self.movie.poster_color)
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, top_c)
        grad.setColorAt(1.0, bot_c)
        p.fillRect(rect, grad)

        seed = sum(ord(ch) for ch in (self.movie.title or "Movie"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 20))
        if seed % 3 == 0:
            p.drawEllipse(QPointF(w * 0.88, h * 0.18), w * 0.42, w * 0.42)
            p.setBrush(QColor(255, 255, 255, 12))
            p.drawEllipse(QPointF(w * 0.15, h * 0.85), w * 0.35, w * 0.35)
        elif seed % 3 == 1:
            p.drawEllipse(QPointF(w * 0.5, h * 0.96), w * 0.6, w * 0.6)
            p.setPen(QPen(QColor(255, 255, 255, 22), 1.2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(w * 0.82, h * 0.22), w * 0.28, w * 0.28)
        else:
            p.drawRoundedRect(QRectF(w * 0.52, -h * 0.08, w * 0.65, h * 0.65), 24, 24)
            p.setBrush(QColor(255, 255, 255, 12))
            p.drawEllipse(QPointF(w * 0.22, h * 0.78), w * 0.28, w * 0.28)

        spine_w = 10.0 if self.large else 8.0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(15, 23, 42, 48))
        p.drawRect(QRectF(0, 0, spine_w, h))
        p.setBrush(QColor(255, 255, 255, 42))
        p.drawRect(QRectF(spine_w, 0, 1.5, h))

        cat = self.movie.genre or "其他"
        font_cat = QFont("Microsoft YaHei UI", 8 if not self.large else 9)
        font_cat.setBold(True)
        p.setFont(font_cat)
        fm = p.fontMetrics()
        pill_w = min(fm.horizontalAdvance(cat) + 16, w - spine_w - 28)
        pill_rect = QRectF(spine_w + 14, 14, pill_w, 20 if not self.large else 22)
        p.setBrush(QColor(255, 255, 255, 36))
        p.drawRoundedRect(pill_rect, 6, 6)
        p.setPen(QColor(255, 255, 255, 235))
        p.drawText(pill_rect, Qt.AlignCenter, cat)

        title_font = QFont("Microsoft YaHei UI", 12 if not self.large else 14)
        title_font.setBold(True)
        p.setFont(title_font)
        p.setPen(QColor(255, 255, 255, 248))
        title_rect = QRectF(spine_w + 14, 46 if not self.large else 54,
                            w - spine_w - 26, h - (90 if not self.large else 104))
        p.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, self.movie.title)

        line_y = h - (36 if not self.large else 42)
        p.setPen(QPen(QColor(255, 255, 255, 110), 1.5))
        p.drawLine(QPointF(spine_w + 14, line_y), QPointF(spine_w + 42, line_y))

        director_font = QFont("Microsoft YaHei UI", 8 if not self.large else 9)
        p.setFont(director_font)
        p.setPen(QColor(255, 255, 255, 200))
        director_rect = QRectF(spine_w + 14, line_y + 6, w - spine_w - 26, 20)
        elided_director = p.fontMetrics().elidedText(self.movie.director or "未知", Qt.ElideRight, int(director_rect.width()))
        p.drawText(director_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_director)

        p.end()

    def _load_online(self):
        """异步加载在线海报；失败或离线时沿用绘制海报。"""
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
        """计算海报居中裁剪的源区域，保持纵横比。"""
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
    """现代电影卡片控件，点击后发出 clicked(Movie) 信号。"""
    clicked = pyqtSignal(object)

    def __init__(self, movie, score=None, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.setObjectName("movieCard")
        self.setFixedSize(212, 312)
        self.setCursor(Qt.PointingHandCursor)
        apply_shadow(self, blur=20, y_offset=4, alpha=14)
        self._build(score)

    def _build(self, score):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        cover = MoviePoster(self.movie, radius=10)
        cover.setFixedHeight(178)

        title = QLabel(self.movie.title)
        title.setObjectName("cardTitle")
        title.setWordWrap(True)
        title.setMaximumHeight(42)
        title.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        director = QLabel(self.movie.director or "未知")
        director.setObjectName("cardAuthor")

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 2, 0, 0)
        bottom.setSpacing(6)

        cat_pill = QLabel(self.movie.genre or "其他")
        cat_pill.setObjectName("catPill")
        bottom.addWidget(cat_pill)
        bottom.addStretch()

        if score is not None and score > 0:
            match_pill = QLabel(f"推荐 {score:.2f}")
            match_pill.setObjectName("matchPill")
            bottom.addWidget(match_pill)
            match_pill.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        layout.addWidget(cover)
        layout.addWidget(title)
        layout.addWidget(director)
        layout.addStretch()
        layout.addLayout(bottom)

        for w in (title, director, cat_pill):
            w.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.movie)
        super().mousePressEvent(event)


class StarRating(QWidget):
    """支持悬停预览的矢量五星评分控件。"""
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
                p.setPen(QPen(QColor("#D97706"), 1.0))
            else:
                p.setBrush(QColor("#E5E7EB"))
                p.setPen(QPen(QColor("#D1D5DB"), 1.0))
            p.drawPolygon(QPolygonF(pts))

        text_x = 5 * (self.star_size + self.gap) + 10
        text_rect = QRectF(text_x, 0, self.width() - text_x, self.height())
        font = QFont("Microsoft YaHei UI", 10)
        font.setBold(active > 0)
        p.setFont(font)
        p.setPen(QColor("#D97706") if active > 0 else QColor("#6B7280"))
        p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.LABELS.get(active, f"{active} 分"))
        p.end()