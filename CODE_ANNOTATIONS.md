# 关键代码逐行注释

> 这份文档把 4 个**最容易被老师追问的核心函数**逐行展开, 用 `// →` 标注每个"为什么这么写"。看完这份, 你能在白板上凭记忆默写出关键转移, 也能解释每个边界 case 的处理理由。
>
> 涉及 4 段:
> 1. `Grid::bfsWithPrev` — 单次 BFS 同时建距离 + 前驱
> 2. `compute_dp_context` 核心循环 — 划分 DP 两种枚举 + singleCost
> 3. `solve_dual_dp` — 双车归约 + 对称消除
> 4. `Animator` 核心三个方法 — 多车补间 + status_callback

---

## 1 `Grid::bfsWithPrev` (`src/cpp/grid.cpp:37-60`)

**职责**: 从一个源点 `from` 做 BFS, 同时填两张表 — `dist[r][c]` 是到 `(r,c)` 的最短距离, `prev[r][c]` 是反向追溯路径的前驱坐标。**用一次 BFS 输出两份信息**, 是距离矩阵 $O(K cdot M L)$ 而不是 $O(K^2 cdot M L)$ 的根基。

```cpp
void Grid::bfsWithPrev(const Point& from,
                       std::vector<std::vector<int>>& dist,
                       std::vector<std::vector<Point>>& prev) const {
    // → 输出是引用传入的 dist 和 prev, 调用方负责复用同一对临时容器,
    //   避免每次源点都堆 alloc 一对新表, 减少 GC 压力

    dist.assign(rows, std::vector<int>(cols, -1));     // → -1 表示"还没访问到"
    prev.assign(rows, std::vector<Point>(cols, {-1, -1}));  // → {-1,-1} 表示"没有前驱" (源点或不可达)

    if (!walkable(from)) return;
    // → 防御性: 如果源点本身就在障碍上或越界, 直接返回空表 (全 -1).
    //   调用方 (build_distance_matrix) 看到 dist[v] == -1 就视为不可达

    dist[from.r][from.c] = 0;                          // → 源点自身距离 0
    std::queue<Point> q;
    q.push(from);
    while (!q.empty()) {
        Point cur = q.front(); q.pop();                // → BFS 标准: 队头出
        int d = dist[cur.r][cur.c];                    // → 缓存当前点的距离, 后面 +1 用
        for (int k = 0; k < 4; ++k) {                  // → 4-邻接: 上下左右
            int nr = cur.r + dR[k];
            int nc = cur.c + dC[k];
            if (!walkable(nr, nc)) continue;           // → walkable 同时检查越界 + 障碍 (合并两个判断)
            if (dist[nr][nc] != -1) continue;          // → 已访问过, 跳过 (BFS 不需要松弛, 第一次访问就是最短)
            dist[nr][nc] = d + 1;                      // → 距离 +1
            prev[nr][nc] = cur;                        // → 关键: 记录前驱, 用于路径回溯
            q.push({nr, nc});                          // → 入队
        }
    }
    // → 时间复杂度 O(M·L), 空间 O(M·L) (两张表 + 队列峰值 O(M·L))
}
```

**配套的 `reconstructPath`** (`grid.cpp:62`) 用这张 prev 表 $O(L)$ 回溯:

```cpp
std::vector<Point> Grid::reconstructPath(const Point& from, const Point& to,
                                         const std::vector<std::vector<Point>>& prev) const {
    std::vector<Point> path;
    if (!walkable(from) || !walkable(to)) return path;       // → 端点不合法返回空
    if (from == to) { path.push_back(from); return path; }   // → 同点返回单点路径
    if (prev[to.r][to.c].r < 0) return path;                 // → to 不可达 (prev 为 {-1,-1})

    Point cur = to;
    while (!(cur == from)) {
        path.push_back(cur);                                 // → 从终点反着推
        cur = prev[cur.r][cur.c];
        if (cur.r < 0) return {};                            // → 防御: 链断 (理论上不该发生)
    }
    path.push_back(from);                                    // → 把源点加上
    for (size_t i = 0, j = path.size() - 1; i < j; ++i, --j)
        std::swap(path[i], path[j]);                         // → 反向, 改成 from → to 顺序
    return path;
}
```

**老师可能问**:
- "为什么用 `-1` 标记未访问而不是 `INT_MAX`?" → 节省内存、判断快、与"不可达"语义自然合一。
- "BFS 不需要松弛?" → 边权恒为 1 时, 第一次访问到的距离就是最短, 这是 BFS 的核心性质。

---

## 2 `compute_dp_context` 核心循环 (`src/cpp/dp.cpp:135-188`)

**职责**: 一次性算完 G 表和 singleCost 表, 暴露给 dual 模块复用。这里同时展示**两种子集枚举方式**和**singleCost 的派生**。

```cpp
// (省略前置: tsp_from_depot 已填好 ctx.tspS / ctx.tspT,
//  compute_trip_costs 已填好 ctx.firstCost / ctx.laterCost,
//  容量过滤已经把 sum_w > Wmax 的 mask 的 first/laterCost 置 INF)

// ====================== 4) 划分 DP: G[mask] ======================
ctx.G.assign(full, INF);                  // → INF = INT_MAX/4, 留余量避免加法溢出
ctx.pickG.assign(full, 0);                // → 回溯用: G[mask] 取最优时的"第一条 later-trip 子集 Q"
ctx.G[0] = 0;                             // → 边界: 空集不需要 trip, 代价 0

for (int mask = 1; mask < full; ++mask) {
    if (mode == DpMode::Standard) {
        // ─── 标准枚举: 遍历 mask 全部非空子集 Q ───────────────
        for (int Q = mask; Q > 0; Q = (Q - 1) & mask) {
            // → 这是子集枚举的经典 trick: Q 从 mask 开始, 反复做 (Q-1)&mask,
            //   会按降序遍历 mask 的所有非空子集. 例: mask=110 → Q=110,100,010.
            //   原理: (Q-1)&mask 把 Q 减 1 后只保留 mask 的位, 等于在 mask 的位空间里 Q-1.

            if (ctx.laterCost[Q] >= INF) continue;        // → 容量超限或不连通, 跳过
            int rest = mask ^ Q;                          // → mask 除去 Q 的剩余部分
            if (ctx.G[rest] >= INF) continue;             // → 剩余部分本身不可解, 跳过
            int cand = ctx.laterCost[Q] + ctx.G[rest];    // → 候选总代价
            if (cand < ctx.G[mask]) {
                ctx.G[mask] = cand;
                ctx.pickG[mask] = Q;                       // → 记录最优时取的 Q, 后面回溯路径用
            }
        }
    } else {
        // ─── pivot 规范化枚举: 只遍历含最低位元素的 Q ──────────
        int pivot = mask & -mask;                          // → mask & -mask = 最低位 1
                                                           //   (这是位运算技巧: 补码 -mask 把最低 1 之上全反转)
        int rest_of_mask = mask ^ pivot;                   // → 除去 pivot 的剩余可选位

        int R = rest_of_mask;
        while (true) {
            int Q = pivot | R;                             // → 强制 pivot ∈ Q, 在 rest 部分自由选 R
            // → 这样 Q 一定含 pivot, 跳过了 pivot ∉ Q 的一半子集
            // → 那一半由 G[mask\Q] 的递归求解时枚举到 (mask\Q 含 pivot)
            if (ctx.laterCost[Q] < INF) {
                int leftover = mask ^ Q;
                if (ctx.G[leftover] < INF) {
                    int cand = ctx.laterCost[Q] + ctx.G[leftover];
                    if (cand < ctx.G[mask]) {
                        ctx.G[mask] = cand;
                        ctx.pickG[mask] = Q;
                    }
                }
            }
            if (R == 0) break;                              // → R=0 时已经枚举到 Q=pivot, 是最后一次
            R = (R - 1) & rest_of_mask;                     // → 子集枚举 trick: 在 rest_of_mask 的位空间里遍历
        }
    }
}

// ====================== 5) singleCost[mask] ======================
// 一次性对全集 [n] 的所有 mask 求"单车从 S 出发收完 mask 的最优总代价",
// 复用 firstCost (S 起) 与 G (T 起的后续), O(3^N), 不重建子距离矩阵.
ctx.singleCost.assign(full, INF);
ctx.bestQ1.assign(full, 0);
ctx.singleCost[0] = 0;                                       // → 空集, 单车不出动, 代价 0

for (int mask = 1; mask < full; ++mask) {
    for (int Q = mask; Q > 0; Q = (Q - 1) & mask) {
        // → 同样的子集枚举 trick, Q 是首程 (S 起) 子集
        if (ctx.firstCost[Q] >= INF) continue;               // → 首程超载/不连通
        int leftover = mask ^ Q;
        if (ctx.G[leftover] >= INF) continue;                // → 后续部分不可解
        int cand = ctx.firstCost[Q] + ctx.G[leftover];       // → 首程 + 后续 G
        if (cand < ctx.singleCost[mask]) {
            ctx.singleCost[mask] = cand;
            ctx.bestQ1[mask] = Q;                            // → 记录最优时的首程子集 Q
        }
    }
}
return ctx;
// → 整个 compute_dp_context 完成后, dual.cpp 只需要查 ctx.singleCost 表 + 对称消除,
//   不用再调任何 BFS 或子 DP, 这就是 P6 优化 460× 加速的本质.
```

**老师可能问**:
- "`(Q-1) & mask` 这个 trick 是什么?" → 子集枚举的标准位运算, 在 mask 的位空间里 Q 减 1, 遍历 mask 的全部子集 (包含空集需要 Q=0 时退出)。
- "为什么 INF 取 INT_MAX/4 不取 INT_MAX?" → 避免加法溢出, INF + INF 还是合法 int。
- "G 表填表顺序为什么按 mask 升序?" → 因为 G[mask] 依赖 G[mask^Q] 即更小的 mask, 子问题先解。

---

## 3 `solve_dual_dp` (`src/cpp/dual.cpp:56-109`)

**职责**: 双车求解, 把答案归约为 singleCost 表的二划分, 用对称消除把枚举量减半。

```cpp
Solution solve_dual_dp(const KeyPoints& kp, const DistanceMatrix& dm) {
    using clock = std::chrono::high_resolution_clock;
    auto t0 = clock::now();                              // → 计时, 后面填 runtimeMs

    Solution result;
    result.algorithm = "multi_dp";
    int N = kp.N();
    int full = (1 << N) - 1;                             // → 全集 mask, 例: N=3 时 full=0b111=7

    // 关键: 只调用一次 compute_dp_context, 拿到所有 singleCost
    DpContext ctx = compute_dp_context(kp, dm, DpMode::Standard);
    // → 这一次 O(3^N) 计算覆盖了双车所需的全部子集; 不再重建子距离矩阵, 不再重跑子 DP

    constexpr int INF_HALF = std::numeric_limits<int>::max() / 4;
    int bestTotal = INF_HALF;
    int bestM1 = -1;

    // ─── 候选 1: 退化情形, 一辆车不出动 ──────────────────
    if (ctx.singleCost[full] < INF_HALF) {
        bestTotal = ctx.singleCost[full];                // → 第二辆车承担全集, 第一辆车 mask1=0 代价 0
        bestM1 = 0;
    }
    // → 这种情形保证: 双车解总不劣于单车解 (双车至少能选择"其中一辆不动"退化为单车)

    // ─── 候选 2: 对称性消除 — 强制 0 ∈ mask1 ──────────────
    if (N > 0) {
        for (int mask1 = 1; mask1 <= full; ++mask1) {
            if (!(mask1 & 1)) continue;
            // → 关键: 跳过不含点 0 的 mask1.
            //   原因: (mask1, mask2) 与 (mask2, mask1) 是同一个无序划分, 算两次浪费.
            //   规定"较低位元素必属于 mask1", 每个无序划分只被枚举一次, 枚举量减半.
            int mask2 = full ^ mask1;
            int c1 = ctx.singleCost[mask1];
            int c2 = ctx.singleCost[mask2];
            if (c1 >= INF_HALF || c2 >= INF_HALF) continue;  // → 任一不可解, 跳过
            int total = c1 + c2;
            if (total < bestTotal) { bestTotal = total; bestM1 = mask1; }
        }
    }

    if (bestM1 < 0 || bestTotal >= INF_HALF) {
        // → 找不到任何可行划分, 报不可行
        result.ok = false; result.status = "infeasible";
        result.error = "双车 DP: 容量与连通约束下无可行方案";
        result.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
        return result;
    }

    int bestM2 = full ^ bestM1;
    // ─── 用 reconstruct_single_solution 把每辆车的 trips 还原 ──
    // → 这一步只是从已经算好的 ctx (tspS/tspT/firstLast/laterLast/pickG/bestQ1) 回溯, 不再算新东西
    Solution s1 = reconstruct_single_solution(ctx, kp, dm, bestM1, "multi_dp");
    Solution s2 = reconstruct_single_solution(ctx, kp, dm, bestM2, "multi_dp");

    result.ok = true;
    result.totalDistance = bestTotal;
    result.vehicleTrips.push_back(s1.trips);             // → 车 1 的 trips
    result.vehicleTrips.push_back(s2.trips);             // → 车 2 的 trips
    result.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
    return result;
}
```

**对比**: 朴素双车 (P6 优化前) 长这样:
```cpp
// 朴素版伪代码 (不再使用):
for (int mask1 = 0; mask1 <= full; ++mask1) {
    int mask2 = full ^ mask1;
    KeyPoints sub_kp1 = construct_sub_kp(kp, mask1);     // ← 重建关键点
    DistanceMatrix sub_dm1 = build_distance_matrix(grid, sub_kp1);  // ← 重建距离矩阵 (K 次 BFS!)
    Solution s1 = solve_dp(grid, sub_kp1, sub_dm1, DpMode::Standard);  // ← 重跑完整单车 DP
    // (同样对 mask2)
    ...
}
```
每个 mask1 都要 K 次 BFS + 完整 DP, $2^n$ 个 mask 总开销 $O(2^n cdot K cdot M L + 2^n cdot 3^n)$, 实测大样本 92 ms。

**优化后**: 只跑一次 BFS 阵 + 一次 `compute_dp_context`, 然后 $O(2^(n-1))$ 查表加法, 实测 0.2 ms。**461× 加速**。

**老师可能问**:
- "对称消除为什么是 `mask1 & 1`?" → 强制点 0 (最低位) 必属于 mask1。任意元素都行, 选 0 最简单。
- "退化情形 `mask1=0` 为什么必要?" → 不强制对称时 mask1=0 是合法划分, 强制后 (mask1&1==0) 会被跳过, 单独保留以覆盖。
- "为什么 INF_HALF = INT_MAX/4 不是 /2?" → 多次加法都要不溢出, /4 保险。

---

## 4 `Animator` 核心方法 (`src/gui/animator.py`)

**职责**: 多车补间动画 + 实时状态回调。每辆车独立 `QVariantAnimation`, 完成一格触发下一格, 同时通知 UI 刷新载重和已行驶距离。

### 4.1 `__init__` 构造

```python
def __init__(self, map_view, solution, palette, step_ms=180, status_callback=None):
    self.map_view = map_view
    self.sol = solution
    self.palette = palette                       # → 8 色调色板, 不同 trip 用不同颜色
    self.step_ms = step_ms                       # → 单步动画时长 180 ms (经验值: 太快肉眼跟不上, 太慢累)
    self.status_callback = status_callback       # → 可选钩子, 由主窗口传入, 用于刷新 UI

    self.vehicle_state = [(0, 0) for _ in solution.vehicles]
    # → 每辆车的 (当前 trip 索引, 当前 trip 内的步索引), 初始都从 (0, 0) 开始

    self.distance_done = [0 for _ in solution.vehicles]
    # → 每辆车的累计已行驶格数, 单调递增, 跨 trip 不归零

    self.car_colors = [QColor(255, 180, 0), QColor(0, 200, 180)]
    # → 双车颜色: 橙黄 (车 1) + 青绿 (车 2), 高对比

    # 每辆车一个 QVariantAnimation 用于平滑过渡
    self.anims = [QVariantAnimation() for _ in solution.vehicles]
    for i, anim in enumerate(self.anims):
        anim.setDuration(step_ms)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        # → InOutQuad 缓动: 起步加速 + 末尾减速, 视觉上比线性更自然
        anim.valueChanged.connect(lambda v, idx=i: self._on_pos(idx, v))
        # → 帧驱动: Qt 每帧调用 valueChanged, 更新 sprite 位置
        anim.finished.connect(lambda idx=i: self._on_step_done(idx))
        # → 完成一格的回调, 链式触发下一格

    # 预先把所有 trip 路径作为静态叠加层画上去
    for vi, v in enumerate(solution.vehicles):
        for ti, t in enumerate(v):
            color = palette[ti % len(palette)]
            map_view.show_path_overlay(t.path, color)
    # → 一次性画完, 不在动画过程中增量画 (避免重绘抖动)

    # 初始化每辆车到其第一个 trip 的起点
    for vi, v in enumerate(solution.vehicles):
        if v and v[0].path:
            r, c = v[0].path[0]
            map_view.set_car_position(r, c,
                color=self.car_colors[vi % len(self.car_colors)],
                car_id=vi)

    # 启动前先广播一次初始状态 (Trip 1/N, distance=0)
    for vi in range(len(self.sol.vehicles)):
        self._emit_status(vi)
    # → 避免 UI 上"等待启动"显示太久, 立刻显示 trip 1 信息
```

### 4.2 `_begin_step` (启动一步动画)

```python
def _begin_step(self, vi):
    seg = self._current_segment(vi)              # → 拿当前 trip 内的"下一对相邻格"
    if seg is None:
        # 当前 trip 走完了, 切到下一 trip
        ti, _ = self.vehicle_state[vi]
        self.vehicle_state[vi] = (ti + 1, 0)
        self._emit_status(vi)                    # → trip 切换瞬间也广播一次, 让 UI 立刻刷新 trip 号
        seg = self._current_segment(vi)
        if seg is None:
            # 所有 trip 都走完了
            self._emit_status(vi, done=True)
            return

    (r0, c0), (r1, c1) = seg
    # → 把网格坐标转换为场景像素坐标 (CELL=36 px 一格, 0.225 是车辆 sprite 居中偏移)
    start = QPointF(c0 * CELL + CELL * 0.225, r0 * CELL + CELL * 0.225)
    end   = QPointF(c1 * CELL + CELL * 0.225, r1 * CELL + CELL * 0.225)
    anim = self.anims[vi]
    anim.stop()                                  # → 防御: 万一前一段没停干净
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.start()
    # → start() 后 Qt 主循环会每帧调用 valueChanged → _on_pos → 更新 sprite 位置
    # → 180 ms 后 finished 触发 → _on_step_done → 推进 vehicle_state 并启动下一步
```

### 4.3 `_on_step_done` + `_emit_status` (完成一步 + 通知 UI)

```python
def _on_step_done(self, vi):
    ti, si = self.vehicle_state[vi]
    self.vehicle_state[vi] = (ti, si + 1)        # → 步索引 +1
    self.distance_done[vi] += 1                  # → 累计距离 +1
    self._emit_status(vi)                        # → 广播新状态给 UI
    # → 用 0ms 延迟启动下一步, 避免递归过深 (Qt 信号回调嵌套有栈深度风险)
    QTimer.singleShot(0, lambda: self._begin_step(vi))

def _emit_status(self, vi, done: bool = False):
    if self.status_callback is None:
        return                                   # → 没注册回调就静默, 不报错
    trips = self.sol.vehicles[vi]
    n = len(trips)
    ti, _ = self.vehicle_state[vi]
    if done or ti >= n:
        # 已完成所有 trip
        self.status_callback(vi, {
            'trip_idx':  n, 'num_trips': n,
            'load':      0,                       # → 完成时载重归零 (已经在 T 卸完)
            'distance':  self.distance_done[vi],
            'done':      True,
        })
        return
    # 正在某个 trip 中
    self.status_callback(vi, {
        'trip_idx':  ti + 1, 'num_trips': n,    # → 1-based, UI 友好
        'load':      trips[ti].load,             # → 当前 trip 的固定载重 (整段 trip 不变)
        'distance':  self.distance_done[vi],     # → 单调递增的累计步数
        'done':      False,
    })
```

**UI 端如何接 callback** (`main.py` 的 `_on_animation_status`):

```python
def _on_animation_status(self, vi: int, info: dict):
    if vi >= len(self.live_status_labels):
        return                                   # → 防御: 万一回调比 UI 重建快
    lbl = self.live_status_labels[vi]
    if info.get('done'):
        lbl.setText(f"车 {vi + 1}  ✓ 完成   "
                    f"Trip {info['num_trips']}/{info['num_trips']}, "
                    f"载重 0, 已行驶 {info['distance']}")
        lbl.setStyleSheet("...浅绿底...")        # → 完成态变绿
        # 全部车都完成时, 状态徽章变 "完成"
        if all("✓" in l.text() for l in self.live_status_labels):
            self._set_run_status("done")
        return
    lbl.setText(f"车 {vi + 1}  Trip {info['trip_idx']}/{info['num_trips']}, "
                f"载重 {info['load']}, 已行驶 {info['distance']}")
```

**老师可能问**:
- "为什么用 QVariantAnimation 不用 QTimer 手动步进?" → QVariantAnimation 自带缓动曲线 + 帧同步, 比手动 QTimer 平滑得多 (60 FPS); 而且 finished 信号链式触发更清晰。
- "InOutQuad 是什么?" → 缓动曲线, 起步加速 + 末尾减速, 视觉上比线性匀速更自然。
- "为什么 `QTimer.singleShot(0, ...)` 而不是直接调?" → 避免回调栈递归过深 (`finished → _on_step_done → _begin_step → start → ... → finished`), 用 0ms 延迟把控制权交回 Qt 事件循环, 平展栈深度。
- "多车回调会不会冲突?" → 不会, Qt 主线程串行执行所有事件, info 字段 `vi` 标识哪辆车。

---

## 速查: 哪段代码做什么

| 想知道 | 代码 | 行 |
|---|---|---|
| BFS + 前驱表 | `grid.cpp::bfsWithPrev` | 37-60 |
| 路径回溯 | `grid.cpp::reconstructPath` | 62-79 |
| 距离矩阵预计算 | `solver_common.cpp::build_distance_matrix` | 10-43 |
| 子集 TSP DP | `dp.cpp::tsp_from_depot` | 16-39 |
| 单 trip 代价派生 | `dp.cpp::compute_trip_costs` | 42-61 |
| 划分 DP 两种枚举 | `dp.cpp::compute_dp_context` | 135-167 |
| singleCost 表派生 | `dp.cpp::compute_dp_context` | 170-188 |
| 路径回溯还原 trips | `dp.cpp::reconstruct_single_solution` | 193-242 |
| 双车归约 + 对称消除 | `dual.cpp::solve_dual_dp` | 56-109 |
| 最近邻贪心 | `greedy.cpp::solve_greedy` | 9-88 |
| 输入解析 | `io_utils.cpp::parse_input` | 17-66 |
| 行式输出 | `io_utils.cpp::emit_solution` | 68-103 |
| JSON 输出 | `io_utils.cpp::emit_solution_json` | 145-203 |
| 可行性检查 | `feasibility.cpp::check_feasibility` | 11-84 |
| 多车补间 + status_callback | `animator.py::Animator` | 全文件 |
| 主窗口 + KPI + 实时状态 | `main.py::MainWindow` | 全文件 |
