"""map_view.py —— QGraphicsView 网格地图视图"""
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QBrush, QColor, QFont, QPen, QPainterPath
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
    QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsEllipseItem,
)

CELL = 36     # 每格像素数


class MapView(QGraphicsView):
    """支持点击编辑的网格地图视图。
       模式: 'obstacle' / 'parking' / 'plant' / 'point' / 'erase'
    """
    cellClicked = pyqtSignal(int, int, int)  # (r, c, button: 1=L, 2=R)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(self.renderHints())
        self.rows = 10
        self.cols = 10
        self.cells = [["." for _ in range(self.cols)] for _ in range(self.rows)]
        self.parking = None
        self.plant = None
        self.points = []
        self.weights = []
        self._car_item = None
        self._trip_overlays = []
        self.rebuild()

    def set_map(self, rows, cols, cells):
        self.rows, self.cols = rows, cols
        self.cells = [list(row.ljust(cols, '.')[:cols]) for row in cells]
        self.rebuild()

    def rebuild(self):
        self._scene.clear()
        self._car_item = None
        self._trip_overlays = []
        # 网格背景
        for r in range(self.rows):
            for c in range(self.cols):
                rect = QGraphicsRectItem(c * CELL, r * CELL, CELL, CELL)
                rect.setPen(QPen(QColor(200, 200, 200)))
                if self.cells[r][c] == '#':
                    rect.setBrush(QBrush(QColor(80, 80, 80)))
                else:
                    rect.setBrush(QBrush(QColor(250, 250, 250)))
                self._scene.addItem(rect)
        # 关键点
        if self.parking is not None:
            self._paint_marker(self.parking, QColor(60, 160, 60), "S")
        if self.plant is not None:
            self._paint_marker(self.plant, QColor(220, 60, 60), "T")
        for i, (p, w) in enumerate(zip(self.points, self.weights)):
            self._paint_marker(p, QColor(60, 90, 200), f"{i}:{w}")

        self._scene.setSceneRect(QRectF(0, 0, self.cols * CELL, self.rows * CELL))

    def _paint_marker(self, p, color, label):
        r, c = p
        item = QGraphicsRectItem(c * CELL + 3, r * CELL + 3, CELL - 6, CELL - 6)
        item.setBrush(QBrush(color))
        item.setPen(QPen(QColor(0, 0, 0)))
        self._scene.addItem(item)
        txt = QGraphicsSimpleTextItem(label)
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        txt.setFont(f)
        txt.setBrush(QBrush(QColor(255, 255, 255)))
        br = txt.boundingRect()
        txt.setPos(c * CELL + (CELL - br.width()) / 2,
                   r * CELL + (CELL - br.height()) / 2)
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
        qp.moveTo(path[0][1] * CELL + CELL / 2, path[0][0] * CELL + CELL / 2)
        for (r, c) in path[1:]:
            qp.lineTo(c * CELL + CELL / 2, r * CELL + CELL / 2)
        item = QGraphicsPathItem(qp)
        pen = QPen(color)
        pen.setWidth(3)
        item.setPen(pen)
        self._scene.addItem(item)
        self._trip_overlays.append(item)

    def clear_overlays(self):
        for it in self._trip_overlays:
            self._scene.removeItem(it)
        self._trip_overlays = []
        if self._car_item is not None:
            self._scene.removeItem(self._car_item)
            self._car_item = None

    def set_car_position(self, r, c, color=None):
        if color is None:
            color = QColor(255, 180, 0)
        if self._car_item is None:
            self._car_item = QGraphicsEllipseItem(0, 0, CELL * 0.5, CELL * 0.5)
            self._car_item.setBrush(QBrush(color))
            self._car_item.setPen(QPen(QColor(0, 0, 0), 2))
            self._car_item.setZValue(10)
            self._scene.addItem(self._car_item)
        self._car_item.setBrush(QBrush(color))
        self._car_item.setPos(c * CELL + CELL * 0.25, r * CELL + CELL * 0.25)
