"""main.py —— PyQt6 应用入口"""
import os
import sys

# 确保 src/gui 在 sys.path 上,允许从任意 cwd 启动
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSpinBox, QComboBox, QLabel, QTextEdit, QGroupBox,
    QFormLayout, QMessageBox, QFileDialog,
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("城市垃圾收运路线规划")
        self.state = EditorState(rows=12, cols=12)
        self.map_view = MapView()
        self.animator = None  # type: Animator | None
        self._build_ui()
        self._refresh_map()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # 左控制面板
        left = QVBoxLayout()
        modeGroup = QGroupBox("编辑模式")
        mgLayout = QVBoxLayout(modeGroup)
        for label, mode in [("障碍 (toggle)", MODE_OBSTACLE),
                            ("停车场 S", MODE_PARKING),
                            ("处理厂 T", MODE_PLANT),
                            ("收集点 P", MODE_POINT),
                            ("擦除 (右键也可)", MODE_ERASE)]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, m=mode: self._set_mode(m))
            mgLayout.addWidget(btn)
        left.addWidget(modeGroup)

        paramsBox = QGroupBox("参数")
        pf = QFormLayout(paramsBox)
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

        # 右结果面板
        right = QVBoxLayout()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        right.addWidget(QLabel("结果"))
        right.addWidget(self.result_text)

        root.addLayout(left, 1)
        root.addWidget(self.map_view, 3)
        root.addLayout(right, 2)
        self.map_view.cellClicked.connect(self._on_cell_clicked)

    def _set_mode(self, mode):
        self.state.mode = mode
        self.statusBar().showMessage(f"模式: {mode}")

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
        # 随机 5 个点
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
        # 简单复用 C++ 端格式
        M, N = map(int, tokens[0].split())
        cells = [list(tokens[1 + i]) for i in range(M)]
        sr, sc = map(int, tokens[1 + M].split())
        tr, tc = map(int, tokens[2 + M].split())
        K = int(tokens[3 + M])
        pts = []
        ws = []
        for i in range(K):
            r, c, w = map(int, tokens[4 + M + i].split())
            pts.append((r, c))
            ws.append(w)
        wmax = int(tokens[4 + M + K])
        self.state = EditorState(rows=M, cols=N, cells=cells)
        self.state.parking = (sr, sc)
        self.state.plant = (tr, tc)
        self.state.points = pts
        self.state.weights = ws
        self.state.w_max = wmax
        self.wmax_input.setValue(wmax)
        self._refresh_map()

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
            return
        # 显示结果
        lines = [f"算法: {sol.algorithm}",
                 f"总距离: {sol.total_distance}",
                 f"耗时: {sol.runtime_ms:.3f} ms",
                 f"车辆数: {len(sol.vehicles)}",
                 ""]
        for vi, v in enumerate(sol.vehicles):
            lines.append(f"--- 车 {vi + 1}, 行程数 {len(v)} ---")
            for ti, t in enumerate(v):
                lines.append(
                    f"  Trip {ti + 1}: 载重={t.load}, 距离={t.distance}, 点={t.point_indices}"
                )
        self.result_text.setPlainText("\n".join(lines))
        # 启动动画
        self._clear_overlays()
        self.animator = Animator(self.map_view, sol, TRIP_COLORS)
        self.animator.start()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1100, 720)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
