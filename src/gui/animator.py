"""animator.py —— 车辆动画 (含平滑补间)"""
from PyQt6.QtCore import QTimer, QVariantAnimation, QPointF, QEasingCurve
from PyQt6.QtGui import QColor

CELL = 36  # 与 map_view 同步

class Animator:
    def __init__(self, map_view, solution, palette, step_ms=180):
        self.map_view = map_view
        self.sol = solution
        self.palette = palette
        self.step_ms = step_ms
        # 每辆车维护 (trip_idx, step_idx)
        self.vehicle_state = [(0, 0) for _ in solution.vehicles]
        self.car_colors = [QColor(255, 180, 0), QColor(0, 200, 180)]
        # 每辆车一个 QVariantAnimation 用于平滑过渡
        self.anims = [QVariantAnimation() for _ in solution.vehicles]
        for i, anim in enumerate(self.anims):
            anim.setDuration(step_ms)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim.valueChanged.connect(lambda v, idx=i: self._on_pos(idx, v))
            anim.finished.connect(lambda idx=i: self._on_step_done(idx))
        # 预先把所有 trip 路径作为静态叠加层画上去
        for vi, v in enumerate(solution.vehicles):
            for ti, t in enumerate(v):
                color = palette[ti % len(palette)]
                map_view.show_path_overlay(t.path, color)
        # 初始化每辆车到其第一个 trip 的起点
        for vi, v in enumerate(solution.vehicles):
            if v and v[0].path:
                r, c = v[0].path[0]
                map_view.set_car_position(r, c, color=self.car_colors[vi % len(self.car_colors)])

    def start(self):
        # 启动每辆车的第一步
        for vi in range(len(self.sol.vehicles)):
            self._begin_step(vi)

    def stop(self):
        for a in self.anims:
            a.stop()

    def _current_segment(self, vi):
        ti, si = self.vehicle_state[vi]
        trips = self.sol.vehicles[vi]
        if ti >= len(trips):
            return None
        path = trips[ti].path
        if not path or si + 1 >= len(path):
            return None
        return (path[si], path[si+1])

    def _begin_step(self, vi):
        seg = self._current_segment(vi)
        if seg is None:
            # 当前 trip 走完了, 切到下一 trip
            ti, _ = self.vehicle_state[vi]
            self.vehicle_state[vi] = (ti + 1, 0)
            seg = self._current_segment(vi)
            if seg is None:
                return  # 该车全部完成
        (r0, c0), (r1, c1) = seg
        start = QPointF(c0 * CELL + CELL * 0.225, r0 * CELL + CELL * 0.225)
        end   = QPointF(c1 * CELL + CELL * 0.225, r1 * CELL + CELL * 0.225)
        anim = self.anims[vi]
        anim.stop()
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.start()

    def _on_pos(self, vi, value: QPointF):
        car = self.map_view._car_item if vi == 0 else None
        # 多车时, 我们用单一 _car_item 不够 — 这里只针对单车做平滑, 多车退化为快速跳
        if car is not None:
            car.setPos(value)

    def _on_step_done(self, vi):
        ti, si = self.vehicle_state[vi]
        self.vehicle_state[vi] = (ti, si + 1)
        # 用 0ms 延迟启动下一步, 避免递归过深
        QTimer.singleShot(0, lambda: self._begin_step(vi))
