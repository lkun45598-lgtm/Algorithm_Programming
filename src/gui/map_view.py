"""map_view.py —— QGraphicsView 网格地图视图

特性:
- 网格外区域绘制淡点阵图案 (`_make_dot_pattern`), 替代纯灰平面
- `resizeEvent` 触发自适应: 调 `fitInView` 让整张网格按当前窗口大小
  保持长宽比缩放, 答辩投影/全屏均自适应; 场景坐标不变, 动画无需改动
"""
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QBrush, QColor, QFont, QPen, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
    QGraphicsSimpleTextItem, QGraphicsEllipseItem, QGraphicsPathItem,
    QGraphicsDropShadowEffect,
)

CELL = 36     # 每格像素数 (场景坐标; 视图层会按窗口缩放)


def _make_dot_pattern() -> QBrush:
    """24×24 平铺的淡点阵图案, 在 map 外灰色区呈现细密点。"""
    pix = QPixmap(24, 24)
    pix.fill(QColor("#eef1f5"))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor("#cdd3dd")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(10, 10, 4, 4)
    p.end()
    return QBrush(pix)


class MapView(QGraphicsView):
    """支持点击编辑的网格地图视图。
       模式: 'obstacle' / 'parking' / 'plant' / 'point' / 'erase'
    """
    cellClicked = pyqtSignal(int, int, int)  # (r, c, button: 1=L, 2=R)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )
        # 关键: 让背景图案在视口坐标里平铺 (不随场景缩放变形)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setBackgroundBrush(_make_dot_pattern())
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.rows = 10
        self.cols = 10
        self.cells = [["." for _ in range(self.cols)] for _ in range(self.rows)]
        self.parking = None
        self.plant = None
        self.points = []
        self.weights = []
        self._car_item = None           # 兼容旧单车接口: car_id=0
        self._car_items = {}            # car_id -> QGraphicsEllipseItem
        self._trip_overlays = []
        self.rebuild()

    # ---- 视口背景在视口坐标下绘制, 不随场景缩放 ----
    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.save()
        painter.resetTransform()
        vp = self.viewport().rect()
        painter.fillRect(vp, self.backgroundBrush())
        painter.restore()

    def set_map(self, rows, cols, cells):
        self.rows, self.cols = rows, cols
        self.cells = [list(row.ljust(cols, '.')[:cols]) for row in cells]
        self.rebuild()

    def rebuild(self):
        self._scene.clear()
        self._car_item = None
        self._car_items = {}
        self._trip_overlays = []
        # 网格背景
        for r in range(self.rows):
            for c in range(self.cols):
                rect = QGraphicsRectItem(c * CELL, r * CELL, CELL, CELL)
                rect.setPen(QPen(QColor(220, 224, 230)))
                if self.cells[r][c] == '#':
                    rect.setBrush(QBrush(QColor(70, 78, 95)))
                else:
                    rect.setBrush(QBrush(QColor(255, 255, 255)))
                self._scene.addItem(rect)
        # 关键点
        if self.parking is not None:
            self._paint_marker(self.parking, QColor(60, 160, 60), "S")
        if self.plant is not None:
            self._paint_marker(self.plant, QColor(220, 60, 60), "T")
        for i, (p, w) in enumerate(zip(self.points, self.weights)):
            self._paint_marker(p, QColor(60, 90, 200), f"{i}:{w}")

        # 给网格加一个浅边框 (让"卡片"感更明显)
        border = QGraphicsRectItem(0, 0, self.cols * CELL, self.rows * CELL)
        border.setPen(QPen(QColor("#b8c0cc"), 1.4))
        border.setBrush(QBrush(Qt.GlobalColor.transparent))
        border.setZValue(10)
        self._scene.addItem(border)

        self._scene.setSceneRect(QRectF(0, 0, self.cols * CELL, self.rows * CELL))
        self._fit_to_view()

    # ---- 自适应缩放 ----
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_to_view()

    def _fit_to_view(self):
        r = self._scene.sceneRect()
        if r.isEmpty():
            return
        # 留 1.5 格的视觉边距, 让网格不顶到边
        margin = CELL * 1.5
        target = QRectF(r.x() - margin, r.y() - margin,
                        r.width() + 2 * margin, r.height() + 2 * margin)
        self.fitInView(target, Qt.AspectRatioMode.KeepAspectRatio)

    def _paint_marker(self, p, color, label):
        r, c = p
        path = QPainterPath()
        path.addRoundedRect(c*CELL+4, r*CELL+4, CELL-8, CELL-8, 8, 8)
        item = QGraphicsPathItem(path)
        item.setBrush(QBrush(color))
        pen = QPen(color.darker(130))
        pen.setWidthF(1.2)
        item.setPen(pen)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 70))
        item.setGraphicsEffect(shadow)
        self._scene.addItem(item)
        txt = QGraphicsSimpleTextItem(label)
        f = QFont()
        f.setPointSize(9)
        f.setBold(True)
        txt.setFont(f)
        txt.setBrush(QBrush(QColor(255, 255, 255)))
        br = txt.boundingRect()
        txt.setPos(c*CELL + (CELL - br.width())/2, r*CELL + (CELL - br.height())/2)
        txt.setZValue(2)
        self._scene.addItem(txt)

    def mousePressEvent(self, ev):
        pos = self.mapToScene(ev.position().toPoint())
        c = int(pos.x() // CELL)
        r = int(pos.y() // CELL)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            btn = 1 if ev.button() == Qt.MouseButton.LeftButton else 2
            self.cellClicked.emit(r, c, btn)
        super().mousePressEvent(ev)

    # --- 动画接口 ---
    def show_path_overlay(self, path, color):
        """在 path (list of (r,c)) 上画线段叠加层"""
        if not path:
            return
        qp = QPainterPath()
        qp.moveTo(path[0][1]*CELL+CELL/2, path[0][0]*CELL+CELL/2)
        for (r, c) in path[1:]:
            qp.lineTo(c*CELL+CELL/2, r*CELL+CELL/2)
        item = QGraphicsPathItem(qp)
        # semi-transparent pen so overlapping trip paths are visible
        pen_color = QColor(color)
        pen_color.setAlpha(180)
        pen = QPen(pen_color)
        pen.setWidthF(3.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        item.setPen(pen)
        item.setZValue(1)
        self._scene.addItem(item)
        self._trip_overlays.append(item)

    def clear_overlays(self):
        for it in self._trip_overlays:
            self._scene.removeItem(it)
        self._trip_overlays = []
        for it in list(getattr(self, "_car_items", {}).values()):
            self._scene.removeItem(it)
        self._car_items = {}
        self._car_item = None

    def _make_car_item(self, color):
        item = QGraphicsEllipseItem(0, 0, CELL*0.55, CELL*0.55)
        outline = QPen(QColor(40, 40, 40))
        outline.setWidthF(1.6)
        item.setPen(outline)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 120))
        item.setGraphicsEffect(shadow)
        item.setZValue(10)
        item.setBrush(QBrush(color))
        self._scene.addItem(item)
        return item

    def set_car_position(self, r, c, color=None, car_id=0):
        if color is None:
            color = QColor(255, 180, 0)
        if not hasattr(self, "_car_items"):
            self._car_items = {}
        if car_id not in self._car_items:
            self._car_items[car_id] = self._make_car_item(color)
            if car_id == 0:
                self._car_item = self._car_items[car_id]
        item = self._car_items[car_id]
        item.setBrush(QBrush(color))
        item.setPos(c*CELL + CELL*0.225, r*CELL + CELL*0.225)

    def car_item(self, car_id=0):
        return getattr(self, "_car_items", {}).get(car_id)
