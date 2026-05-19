"""animator.py —— 车辆动画 (含平滑补间)

每完成一格移动后通过可选的 status_callback 暴露实时状态:
  status_callback(vi, info) , 其中 info = {
      'trip_idx':  当前 trip 序号 (1-based),
      'num_trips': 该车总 trip 数,
      'load':      当前 trip 载重,
      'distance':  该车已行驶距离 (网格步数, 等价于已走过的格数),
      'done':      该车是否全部行程完成,
  }
"""
from PyQt6.QtCore import QTimer, QVariantAnimation, QPointF, QEasingCurve
from PyQt6.QtGui import QColor

CELL = 36  # 与 map_view 同步

class Animator:
    def __init__(self, map_view, solution, palette, step_ms=180, status_callback=None):
        self.map_view = map_view
        self.sol = solution
        self.palette = palette
        self.step_ms = step_ms
        self.status_callback = status_callback
        # 每辆车维护 (trip_idx, step_idx)
        self.vehicle_state = [(0, 0) for _ in solution.vehicles]
        # 该车已行驶格数 (单调累加, 跨 trip 不归零)
        self.distance_done = [0 for _ in solution.vehicles]
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
                map_view.set_car_position(r, c, color=self.car_colors[vi % len(self.car_colors)], car_id=vi)
        # 启动前先广播一次初始状态 (Trip 1/N, distance=0)
        for vi in range(len(self.sol.vehicles)):
            self._emit_status(vi)

    def start(self):
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
            self._emit_status(vi)  # trip 切换瞬间也广播一次, 让 UI 立刻刷新 trip 号与载重
            seg = self._current_segment(vi)
            if seg is None:
                self._emit_status(vi, done=True)
                return
        (r0, c0), (r1, c1) = seg
        start = QPointF(c0 * CELL + CELL * 0.225, r0 * CELL + CELL * 0.225)
        end   = QPointF(c1 * CELL + CELL * 0.225, r1 * CELL + CELL * 0.225)
        anim = self.anims[vi]
        anim.stop()
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.start()

    def _on_pos(self, vi, value: QPointF):
        car = self.map_view.car_item(vi) if hasattr(self.map_view, "car_item") else None
        if car is not None:
            car.setPos(value)

    def _on_step_done(self, vi):
        ti, si = self.vehicle_state[vi]
        self.vehicle_state[vi] = (ti, si + 1)
        self.distance_done[vi] += 1
        self._emit_status(vi)
        # 用 0ms 延迟启动下一步, 避免递归过深
        QTimer.singleShot(0, lambda: self._begin_step(vi))

    def _emit_status(self, vi, done: bool = False):
        if self.status_callback is None:
            return
        trips = self.sol.vehicles[vi]
        n = len(trips)
        ti, _ = self.vehicle_state[vi]
        if done or ti >= n:
            self.status_callback(vi, {
                'trip_idx':  n, 'num_trips': n,
                'load':      0,
                'distance':  self.distance_done[vi],
                'done':      True,
            })
            return
        self.status_callback(vi, {
            'trip_idx':  ti + 1, 'num_trips': n,
            'load':      trips[ti].load,
            'distance':  self.distance_done[vi],
            'done':      False,
        })
