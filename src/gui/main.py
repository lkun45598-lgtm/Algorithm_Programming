"""main.py —— PyQt6 应用入口"""
import os
import sys

# 确保 src/gui 在 sys.path 上,允许从任意 cwd 启动
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap, QPainter, QBrush, QPen, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSpinBox, QComboBox, QLabel, QTextEdit, QGroupBox,
    QFormLayout, QMessageBox, QFileDialog, QButtonGroup, QFrame,
)

from map_view import MapView
from editor import (
    EditorState, MODE_OBSTACLE, MODE_PARKING, MODE_PLANT, MODE_POINT, MODE_ERASE,
)
from controller import build_input_text, run_solver
from animator import Animator


TRIP_COLORS = [
    QColor(255, 140, 0), QColor(0, 150, 200), QColor(180, 80, 200),
    QColor(80, 180, 80), QColor(220, 60, 90), QColor(120, 100, 200),
    QColor(40, 140, 160), QColor(200, 140, 40),
]


def _make_color_icon(color: QColor, shape: str = "square", size: int = 14) -> QIcon:
    """生成模式按钮用的小色块图标 (透明背景)."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if shape == "circle":
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(140), 1))
        p.drawEllipse(1, 1, size - 2, size - 2)
    elif shape == "cross":
        p.setPen(QPen(color, 2))
        p.drawLine(3, 3, size - 3, size - 3)
        p.drawLine(3, size - 3, size - 3, 3)
    else:  # rounded square
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(140), 1))
        p.drawRoundedRect(1, 1, size - 2, size - 2, 3, 3)
    p.end()
    return QIcon(pix)


class KpiCard(QFrame):
    """一张轻量 KPI 卡片: 顶部一条彩色横线 + 大号数值 + 小号标签."""
    def __init__(self, label: str, accent: str = "#3b7ddd", parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setStyleSheet(
            f"#kpiCard {{ background: #ffffff; border: 1px solid #e1e4eb; "
            f"border-top: 3px solid {accent}; border-radius: 6px; }}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(2)
        self.value_lbl = QLabel("—")
        self.value_lbl.setStyleSheet(
            f"color:{accent}; font-size:18pt; font-weight:600; "
            f"font-family:Consolas,'JetBrains Mono',monospace;"
        )
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_lbl = QLabel(label)
        self.label_lbl.setStyleSheet("color:#6c7689; font-size:9pt;")
        self.label_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.value_lbl)
        lay.addWidget(self.label_lbl)

    def set_value(self, text: str):
        self.value_lbl.setText(text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("城市垃圾收运路线规划")
        self.state = EditorState(rows=12, cols=12)
        self.map_view = MapView()
        self.animator = None  # type: Animator | None
        self._build_ui()
        self._refresh_map()
        self._set_run_status("idle")

    # ---------- UI 构造 ----------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # ===== 左控制面板 =====
        left = QVBoxLayout()
        left.setSpacing(10)

        modeGroup = QGroupBox("编辑模式")
        mgLayout = QVBoxLayout(modeGroup)
        mgLayout.setSpacing(6)
        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.setExclusive(True)
        # (label, mode, icon_color, icon_shape)
        mode_defs = [
            ("障碍 (toggle)",   MODE_OBSTACLE, QColor("#4a5468"), "square"),
            ("停车场 S",         MODE_PARKING,  QColor("#28a745"), "square"),
            ("处理厂 T",         MODE_PLANT,    QColor("#dc3545"), "square"),
            ("收集点 P",         MODE_POINT,    QColor("#3b7ddd"), "square"),
            ("擦除 (右键也可)",  MODE_ERASE,    QColor("#8a8f9b"), "cross"),
        ]
        first_btn = None
        for label, mode, color, shape in mode_defs:
            btn = QPushButton(label)
            btn.setIcon(_make_color_icon(color, shape=shape, size=14))
            btn.setIconSize(QSize(14, 14))
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked, m=mode, b=btn: self._set_mode(m, b))
            self.mode_btn_group.addButton(btn)
            mgLayout.addWidget(btn)
            if first_btn is None: first_btn = btn
        first_btn.setChecked(True)
        left.addWidget(modeGroup)

        paramsBox = QGroupBox("参数")
        pf = QFormLayout(paramsBox)
        pf.setVerticalSpacing(8)
        self.weight_input = QSpinBox()
        self.weight_input.setRange(1, 3)
        self.weight_input.setValue(1)
        pf.addRow("下一收集点重量:", self.weight_input)
        self.wmax_input = QSpinBox()
        self.wmax_input.setRange(1, 30)
        self.wmax_input.setValue(3)
        pf.addRow("W_max:", self.wmax_input)
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["dp", "dp_dc", "greedy", "multi_dp", "multi_greedy"])
        pf.addRow("算法:", self.algo_combo)
        left.addWidget(paramsBox)

        run_btn = QPushButton("运行求解 + 动画")
        run_btn.setObjectName("runBtn")
        run_btn.clicked.connect(self._run_and_animate)
        left.addWidget(run_btn)
        clear_btn = QPushButton("清除动画")
        clear_btn.clicked.connect(self._clear_overlays)
        left.addWidget(clear_btn)
        gen_btn = QPushButton("随机生成示例")
        gen_btn.clicked.connect(self._random_example)
        left.addWidget(gen_btn)
        load_btn = QPushButton("载入样例文件")
        load_btn.clicked.connect(self._load_sample)
        left.addWidget(load_btn)
        left.addStretch(1)

        # ===== 右结果面板 =====
        right = QVBoxLayout()
        right.setSpacing(10)

        # KPI 卡片条 (4 张)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(8)
        self.kpi_distance = KpiCard("总距离", accent="#3b7ddd")
        self.kpi_runtime  = KpiCard("耗时 (ms)", accent="#28a745")
        self.kpi_vehicles = KpiCard("车辆数",  accent="#fd7e14")
        self.kpi_trips    = KpiCard("总行程",  accent="#8a4ddb")
        for c in (self.kpi_distance, self.kpi_runtime, self.kpi_vehicles, self.kpi_trips):
            kpi_row.addWidget(c, 1)
        right.addLayout(kpi_row)

        # 实时状态: 标题 + 状态徽章 + 每车一行
        live_header = QHBoxLayout()
        live_title = QLabel("实时状态")
        live_title.setStyleSheet("font-weight:600; color:#4a5468; font-size:10.5pt;")
        live_header.addWidget(live_title)
        live_header.addStretch(1)
        self.status_pill = QLabel("● 等待")
        self.status_pill.setObjectName("statusPill")
        live_header.addWidget(self.status_pill)
        right.addLayout(live_header)

        self.live_status_box = QFrame()
        self.live_status_box.setObjectName("liveBox")
        self.live_status_layout = QVBoxLayout(self.live_status_box)
        self.live_status_layout.setContentsMargins(10, 10, 10, 10)
        self.live_status_layout.setSpacing(6)
        self.live_status_labels = []
        self._live_empty = QLabel("放置 S / T / 收集点后, 点击 ‘运行求解 + 动画’ 开始")
        self._live_empty.setStyleSheet("color:#9aa3b2; padding:6px; font-style:italic;")
        self._live_empty.setWordWrap(True)
        self.live_status_layout.addWidget(self._live_empty)
        right.addWidget(self.live_status_box)

        # 行程详情
        details_title = QLabel("行程详情")
        details_title.setStyleSheet("font-weight:600; color:#4a5468; font-size:10.5pt;")
        right.addWidget(details_title)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText(
            "运行后将显示每辆车每条 trip 的载重、距离与访问点序列。"
        )
        right.addWidget(self.result_text, 1)

        root.addLayout(left, 1)
        root.addWidget(self.map_view, 3)
        root.addLayout(right, 2)
        self.map_view.cellClicked.connect(self._on_cell_clicked)

    # ---------- 状态徽章 ----------
    def _set_run_status(self, state: str):
        """state ∈ {'idle','running','done','error'}"""
        if state == "running":
            text, bg, fg = "● 运行中", "#fff4d1", "#a87404"
        elif state == "done":
            text, bg, fg = "● 完成", "#e6f6ea", "#1f7a3a"
        elif state == "error":
            text, bg, fg = "● 错误", "#fde2e4", "#a52030"
        else:
            text, bg, fg = "● 等待", "#eef0f4", "#6c7689"
        self.status_pill.setText(text)
        self.status_pill.setStyleSheet(
            f"#statusPill {{ background:{bg}; color:{fg}; padding:2px 10px; "
            f"border-radius:10px; font-size:9pt; font-weight:600; }}"
        )

    # ---------- 模式切换 ----------
    def _set_mode(self, mode, btn=None):
        self.state.mode = mode
        if btn is not None:
            btn.setChecked(True)
        self.statusBar().showMessage(f"当前模式: {mode}")

    def _on_cell_clicked(self, r, c, btn):
        self.state.apply_click(r, c, btn, weight_input=self.weight_input.value())
        self._refresh_map()

    def _refresh_map(self):
        self.map_view.set_map(self.state.rows, self.state.cols, self.state.serialize_grid_rows())
        self.map_view.parking = self.state.parking
        self.map_view.plant = self.state.plant
        self.map_view.points = list(self.state.points)
        self.map_view.weights = list(self.state.weights)
        self.map_view.rebuild()

    def _clear_overlays(self):
        if self.animator:
            self.animator.stop()
        self.map_view.clear_overlays()
        self._set_run_status("idle")

    # ---------- 随机/载入 ----------
    def _random_example(self):
        import random
        rows, cols = 12, 12
        cells = [['.' for _ in range(cols)] for _ in range(rows)]
        for _ in range(int(rows * cols * 0.15)):
            r = random.randrange(rows)
            c = random.randrange(cols)
            cells[r][c] = '#'
        cells[0][0] = '.'
        cells[rows - 1][cols - 1] = '.'
        self.state = EditorState(rows=rows, cols=cols, cells=cells)
        self.state.parking = (0, 0)
        self.state.plant = (rows - 1, cols - 1)
        attempts = 0
        points = []
        weights = []
        while len(points) < 5 and attempts < 200:
            r = random.randrange(rows)
            c = random.randrange(cols)
            if cells[r][c] == '#' or (r, c) in [(0, 0), (rows - 1, cols - 1)] or (r, c) in points:
                attempts += 1
                continue
            points.append((r, c))
            weights.append(random.randint(1, 3))
        self.state.points = points
        self.state.weights = weights
        self.state.w_max = self.wmax_input.value()
        self._refresh_map()

    def _load_sample(self):
        fn, _ = QFileDialog.getOpenFileName(self, "载入样例", "data", "Text (*.txt)")
        if not fn:
            return
        with open(fn, encoding="utf-8") as f:
            tokens = f.read().split('\n')
        M, N = map(int, tokens[0].split())
        cells = [list(tokens[1 + i]) for i in range(M)]
        sr, sc = map(int, tokens[1 + M].split())
        tr, tc = map(int, tokens[2 + M].split())
        K = int(tokens[3 + M])
        pts = []; ws = []
        for i in range(K):
            r, c, w = map(int, tokens[4 + M + i].split())
            pts.append((r, c)); ws.append(w)
        wmax = int(tokens[4 + M + K])
        self.state = EditorState(rows=M, cols=N, cells=cells)
        self.state.parking = (sr, sc)
        self.state.plant = (tr, tc)
        self.state.points = pts
        self.state.weights = ws
        self.state.w_max = wmax
        self.wmax_input.setValue(wmax)
        self._refresh_map()

    # ---------- 运行 ----------
    def _run_and_animate(self):
        st = self.state
        if st.parking is None or st.plant is None or not st.points:
            QMessageBox.warning(self, "缺少要素", "请先放置 S、T 和至少 1 个收集点")
            return
        txt = build_input_text(st.serialize_grid_rows(), st.parking, st.plant,
                               st.points, st.weights, self.wmax_input.value(),
                               self.algo_combo.currentText())
        sol = run_solver(txt)
        if not sol.ok:
            self.result_text.setPlainText(f"[{sol.status}] {sol.reason}")
            self._set_kpi_blank()
            self._set_run_status("error")
            return

        # KPI 卡片
        total_trips = sum(len(v) for v in sol.vehicles)
        self.kpi_distance.set_value(str(sol.total_distance))
        self.kpi_runtime.set_value(f"{sol.runtime_ms:.3f}")
        self.kpi_vehicles.set_value(str(len(sol.vehicles)))
        self.kpi_trips.set_value(str(total_trips))

        # 行程详情
        lines = [f"算法: {sol.algorithm}",
                 f"总距离: {sol.total_distance}    耗时: {sol.runtime_ms:.3f} ms",
                 f"车辆数: {len(sol.vehicles)}    总行程: {total_trips}",
                 ""]
        for vi, v in enumerate(sol.vehicles):
            lines.append(f"--- 车 {vi + 1}, 行程数 {len(v)} ---")
            for ti, t in enumerate(v):
                lines.append(
                    f"  Trip {ti + 1}: 载重={t.load}, 距离={t.distance}, 点={t.point_indices}"
                )
        self.result_text.setPlainText("\n".join(lines))

        # 实时状态行 + 动画
        self._rebuild_live_status(len(sol.vehicles))
        self._set_run_status("running")
        self._clear_overlays_only_map()
        self.animator = Animator(
            self.map_view, sol, TRIP_COLORS,
            status_callback=self._on_animation_status,
        )
        self.animator.start()

    def _set_kpi_blank(self):
        for c in (self.kpi_distance, self.kpi_runtime, self.kpi_vehicles, self.kpi_trips):
            c.set_value("—")

    def _clear_overlays_only_map(self):
        # 跑动画前清掉旧 overlay 但不重置状态徽章 (会马上变 running)
        if self.animator:
            self.animator.stop()
        self.map_view.clear_overlays()

    # ---------- 实时状态行 ----------
    def _rebuild_live_status(self, n_vehicles: int):
        while self.live_status_layout.count():
            it = self.live_status_layout.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()
        self.live_status_labels = []
        for vi in range(n_vehicles):
            lbl = QLabel(f"车 {vi + 1} — 等待启动")
            lbl.setStyleSheet(
                "padding:8px 10px; border-radius:6px; "
                "background:#eef3fb; color:#2c3e50; font-family:Consolas,monospace; "
                "border-left: 3px solid #6c93d9;"
            )
            self.live_status_layout.addWidget(lbl)
            self.live_status_labels.append(lbl)

    def _on_animation_status(self, vi: int, info: dict):
        if vi >= len(self.live_status_labels):
            return
        lbl = self.live_status_labels[vi]
        if info.get('done'):
            lbl.setText(
                f"车 {vi + 1}  ✓ 完成   "
                f"Trip {info['num_trips']}/{info['num_trips']}, "
                f"载重 0, 已行驶 {info['distance']}"
            )
            lbl.setStyleSheet(
                "padding:8px 10px; border-radius:6px; "
                "background:#e6f6ea; color:#1f7a3a; font-family:Consolas,monospace; "
                "border-left: 3px solid #28a745; font-weight:600;"
            )
            # 全部车都完成时, 状态徽章变 "完成"
            if all("✓" in (l.text() if hasattr(l, 'text') else '') for l in self.live_status_labels):
                self._set_run_status("done")
            return
        lbl.setText(
            f"车 {vi + 1}  Trip {info['trip_idx']}/{info['num_trips']}, "
            f"载重 {info['load']}, 已行驶 {info['distance']}"
        )


# ---------- 全局 QSS ----------
_QSS = """
QMainWindow, QWidget {
    background: #f5f6fa;
    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
    font-size: 10pt;
    color: #2c2c2c;
}
QGroupBox {
    border: 1px solid #d8dce5;
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-weight: 600;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #4a5468;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #c8cdd6;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 20px;
    text-align: left;
    padding-left: 10px;
}
QPushButton:hover {
    background: #eaf1fb;
    border-color: #6c93d9;
}
QPushButton:pressed {
    background: #d6e4f7;
}
QPushButton:checked {
    background: #3b7ddd;
    color: white;
    border-color: #2c66c0;
    font-weight: 600;
}
QPushButton#runBtn {
    background: #28a745;
    color: white;
    border-color: #208a39;
    font-weight: 600;
    min-height: 30px;
    text-align: center;
    padding-left: 14px;
}
QPushButton#runBtn:hover { background: #2db84f; }
QPushButton#runBtn:pressed { background: #1e8035; }
QSpinBox, QComboBox {
    background: #fff;
    border: 1px solid #c8cdd6;
    border-radius: 4px;
    padding: 4px 6px;
    min-height: 24px;
}
QSpinBox:hover, QComboBox:hover {
    border-color: #6c93d9;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #d8dce5;
    background: #f5f6fa;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #6c7689;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: white;
    border: 1px solid #c8cdd6;
    selection-background-color: #eaf1fb;
    selection-color: #2c3e50;
    padding: 2px;
    outline: none;
}
QTextEdit {
    background: #1e1e2e;
    color: #e4e6eb;
    border: 1px solid #2c2f3a;
    border-radius: 6px;
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 9.5pt;
    padding: 10px;
    selection-background-color: #3b7ddd;
}
QFrame#liveBox {
    background: #ffffff;
    border: 1px solid #d8dce5;
    border-radius: 8px;
}
QLabel { color: #2c2c2c; }
QStatusBar { background: #ececf2; color: #555; }
"""


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(_QSS)
    win = MainWindow()
    win.resize(1240, 800)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
