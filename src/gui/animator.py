"""animator.py —— 车辆动画"""
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor


class Animator:
    def __init__(self, map_view, solution, palette, step_ms=80):
        self.map_view = map_view
        self.sol = solution
        self.palette = palette
        self.step_ms = step_ms
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        # 每辆车维护 (trip_idx, step_idx)
        self.vehicle_state = [(0, 0) for _ in solution.vehicles]
        # 为每辆车一个固定颜色 (与 trip 颜色叠加)
        self.car_colors = [QColor(255, 180, 0), QColor(0, 200, 180)]
        self.finished = False
        # 预先把所有 trip 路径作为静态叠加层画上去
        for vi, v in enumerate(solution.vehicles):
            for ti, t in enumerate(v):
                color = palette[ti % len(palette)]
                map_view.show_path_overlay(t.path, color)

    def start(self):
        self.timer.start(self.step_ms)

    def stop(self):
        self.timer.stop()

    def _tick(self):
        all_done = True
        for vi, (ti, si) in enumerate(self.vehicle_state):
            trips = self.sol.vehicles[vi]
            if ti >= len(trips):
                continue
            path = trips[ti].path
            if not path:
                self.vehicle_state[vi] = (ti + 1, 0)
                all_done = False
                continue
            r, c = path[si]
            color = self.car_colors[vi % len(self.car_colors)]
            self.map_view.set_car_position(r, c, color=color)
            # 推进
            if si + 1 < len(path):
                self.vehicle_state[vi] = (ti, si + 1)
                all_done = False
            else:
                # 当前 trip 结束 → 下一 trip
                self.vehicle_state[vi] = (ti + 1, 0)
                if ti + 1 < len(trips):
                    all_done = False
        if all_done:
            self.timer.stop()
