"""程序化截取主窗口,生成两张 png 给报告用。"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src", "gui"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from main import MainWindow

QSS = """
QMainWindow, QWidget { background: #f5f6fa; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 10pt; color: #2c2c2c; }
QGroupBox { border: 1px solid #d0d4dc; border-radius: 8px; margin-top: 12px; padding: 12px 8px 8px 8px; font-weight: 600; background: #ffffff; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #4a5468; }
QPushButton { background: #ffffff; border: 1px solid #c8cdd6; border-radius: 6px; padding: 6px 12px; min-height: 18px; }
QPushButton:hover { background: #eaf1fb; border-color: #6c93d9; }
QPushButton:pressed { background: #d6e4f7; }
QPushButton:checked { background: #3b7ddd; color: white; border-color: #2c66c0; font-weight: 600; }
QPushButton#runBtn { background: #28a745; color: white; border-color: #208a39; font-weight: 600; min-height: 28px; }
QPushButton#runBtn:hover { background: #2db84f; }
QPushButton#runBtn:pressed { background: #1e8035; }
QSpinBox, QComboBox { background: #fff; border: 1px solid #c8cdd6; border-radius: 4px; padding: 3px 6px; min-height: 22px; }
QComboBox::drop-down { border: none; }
QTextEdit { background: #1e1e2e; color: #e4e6eb; border: 1px solid #2c2f3a; border-radius: 6px; font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace; font-size: 9.5pt; padding: 8px; }
QLabel { color: #2c2c2c; }
QStatusBar { background: #ececf2; color: #555; }
"""

def grab(win, path):
    pm = win.grab()
    pm.save(path, "PNG")
    print("saved", path, "size", pm.size().width(), "x", pm.size().height())

def schedule_shots(win):
    sample = os.path.join(ROOT, "data", "sample_medium.txt")
    with open(sample, encoding="utf-8") as f:
        tokens = f.read().splitlines()
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

    from editor import EditorState
    win.state = EditorState(rows=M, cols=N, cells=cells)
    win.state.parking = (sr, sc); win.state.plant = (tr, tc)
    win.state.points = pts; win.state.weights = ws; win.state.w_max = wmax
    win.wmax_input.setValue(wmax)
    win._refresh_map()

    QTimer.singleShot(200, lambda: grab(win, os.path.join(HERE, "figures", "gui_main.png")))
    QTimer.singleShot(600, lambda: win._run_and_animate())
    QTimer.singleShot(1500, lambda: grab(win, os.path.join(HERE, "figures", "gui_running.png")))
    QTimer.singleShot(2000, QApplication.quit)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = MainWindow()
    win.resize(1180, 760)
    win.show()
    QTimer.singleShot(100, lambda: schedule_shots(win))
    sys.exit(app.exec())
