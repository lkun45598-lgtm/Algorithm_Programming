# 项目自查与答辩指南

> 这份文档是 README.md 的"扩展长版", 帮你在答辩前快速找回每个细节: 各模块怎么实现的、关键代码在哪、可能被问到什么、创新点是哪些。**遇到老师提问时, 大部分答案能在这里直接翻到。**

---

## 1 项目结构总览

```
基于多策略的城市垃圾收运路线规划
├── 后端 C++ (src/cpp/)       —— 算法核心, 6 个职责模块
├── 前端 PyQt6 (src/gui/)     —— 桌面 GUI + 动画演示
├── 测试 (tests/)             —— 暴力对拍 + 密集基准 + 样例库自检
├── 报告 (report.typ → report.pdf)  —— 36 页 Typst, IEEE 风格
└── 样例库 (data/sample_library/)   —— 10 类 20 用例
```

**双层架构**: 前端不链接后端二进制, 通过 `subprocess` 调用 `solver.exe` 并解析其标准输出 (行式协议或 `--json`)。好处: 语言解耦 / 任何上层应用都能调 solver / 测试简单 (脚本调命令行)。

---

## 2 各模块实现细节 + 代码定位

### 2.1 `grid.cpp` — BFS + 路径回溯

**职责**: 网格存储 + 4-邻接 BFS + 前驱表 + 路径重建。

**关键代码**:
- `Grid::bfsDistances` (`src/cpp/grid.cpp:15`) — 标准 BFS, 只算距离
- `Grid::bfsWithPrev` (`src/cpp/grid.cpp:37`) — **一次 BFS 同时写 dist 和 prev 表** (核心优化)
- `Grid::reconstructPath` (`src/cpp/grid.cpp:62`) — 用 prev 表 $O(L)$ 反向回溯
- `Grid::shortestPath` (`src/cpp/grid.cpp:81`) — 单次便利接口 (内部组合上面两个)

**复杂度**: BFS 本身 $O(M cdot L)$, 路径回溯 $O(L)$ 其中 $L$ 是路径长度。

### 2.2 `feasibility.cpp` — 输入合法性 5 类校验

**职责**: 在算法分派前一次性检查所有约束, 失败立即返回 `infeasible`。

**关键代码**: `check_feasibility` (`src/cpp/feasibility.cpp:11`), 检查顺序:

1. 所有关键点必须落在 `.` 格 (不能越界或在障碍上)
2. 至少 1 个收集点
3. $S != T$
4. 任何两个关键点 (S, T, $P_i$) 不能坐标重复
5. 所有 $w_i in [1, 3]$
6. $W_("max") >= max_i w_i$ 且 $sum_i w_i > W_("max")$ (强制多行程)
7. 所有关键点都与 S 连通 (BFS 可达性)

报告 §3.3 `<sec:feas>` 有完整 REASON 文本表 (`tab:feas`)。

### 2.3 `solver_common.cpp` — 距离矩阵 + 路径表

**职责**: 把 $K = n + 2$ 个关键点之间的两两最短距离和路径预先算好, 后续算法直接查表。

**关键代码**: `build_distance_matrix` (`src/cpp/solver_common.cpp:10`)
- 每个源点只调用一次 `bfsWithPrev`
- 同一次 BFS 的 prev 表用来 $O(L)$ 回溯到该源点出发的**所有**目标点路径
- 总复杂度 $O(K cdot M L)$, 不是朴素的 $O(K^2 cdot M L)$

`expand_trip_path` (`src/cpp/solver_common.cpp:45`) — 按关键点序列拼接成完整网格路径。

### 2.4 `dp.cpp` — 两层 DP + singleCost 表

这是整个项目的**算法核心**, 包含 4 个子算法:

#### 2.4.1 子集 TSP (内层 DP)
`tsp_from_depot` (`src/cpp/dp.cpp:16`)
- 状态: `tsp[mask][i]` = 从指定 depot 出发, 访问 mask 全部点, 以 i 结尾的最小代价
- 转移: $"tsp"["mask" | (1<<"nxt")]["nxt"] = "tsp"["mask"]["last"] + D["last"]["nxt"]$
- 复杂度: $O(2^n cdot n^2)$, 跑两次 (S-起 和 T-起)

#### 2.4.2 单次行程代价
`compute_trip_costs` (`src/cpp/dp.cpp:42`)
- 从 tsp 表得到 "走完 mask 并回到 T" 的最优代价 `firstCost[mask]` / `laterCost[mask]`
- 容量约束在外层加: 重量超 $W_("max")$ 的 mask 置 INF

#### 2.4.3 划分 DP (外层 DP)
`compute_dp_context` 中的 G 表填充 (`src/cpp/dp.cpp:133`)
- 状态: `G[mask]` = 仅用 later-trip (T-起) 收完 mask 的最优总代价
- 转移 (标准枚举): $G["mask"] = min_(Q subset.eq "mask") "laterCost"(Q) + G["mask" without Q]$
- 转移 (pivot 枚举): 只枚举包含 $"mask"$ 最低位元素的 $Q$, 候选数减半 (§4.4 与定理 1)

#### 2.4.4 singleCost[mask] 表 ⭐ 创新点
`compute_dp_context` 末尾 (`src/cpp/dp.cpp:170`)
- 定义: `singleCost[mask]` = 单车从 S 出发收完 mask 的最优总代价
- 转移: $"singleCost"["mask"] = min_(Q_1 subset.eq "mask", Q_1 != emptyset) "firstCost"(Q_1) + G["mask" without Q_1]$
- **一次性对所有 mask 计算, $O(3^n)$**, 直接复用 firstCost/G 表, 无需重建子距离矩阵
- 双车 DP 的基石 (见 §2.6)

### 2.5 `greedy.cpp` — 最近邻贪心

**关键代码**: `solve_greedy` (`src/cpp/greedy.cpp:9`)

策略: 每步从当前位置选满足"未访问 + load+w ≤ Wmax + BFS 可达"的距离最近收集点; 无可装点时回 T 卸货开启新 trip; 最后强制返回 T。复杂度 $O(n^2)$ 主导。

由于实现层硬过滤了载重和可达性, **算法运行成功率 = 100% (在 feasibility 通过的输入上)**, 但最优性差距随结构对抗输入急剧扩大 (报告 §6.5: 31% 严格次优, 平均 +14.5%, 最坏 +120%)。

### 2.6 `dual.cpp` — 双车协同 ⭐ 创新点

**关键代码**: `solve_dual_dp` (`src/cpp/dual.cpp:56`)

**核心思想**: 双车答案归约为
$ min_(A subset.eq [n]) "singleCost"[A] + "singleCost"[[n] without A] $

**实现要点**:
1. **复用 singleCost 表**: 只调用一次 `compute_dp_context`, 不重建子距离矩阵, 不重跑子 DP
2. **对称性消除**: 强制 $0 in A$, 把无序划分的二重枚举减半
3. **退化情形**: $A = 0$ 单独处理 (一辆车不出动 = 单车场景), 保证双车解总不劣于单车解

**实测加速**: 优化前 (重建子距离矩阵 + 重跑子 DP) 大样本 ~92 ms, 优化后 ~0.2 ms, **460× 加速**, 双车 DP 与单车 DP 运行时间持平。

`solve_dual_greedy` (`src/cpp/dual.cpp:112`): 贪心后端不支持 mask 输入, 仍走"枚举划分 + 构造子 KeyPoints + 子 BFS + solve_greedy"路径, 加 `localToGlobal` 映射回全局编号。

### 2.7 `io_utils.cpp` — 双协议输出

**关键代码**:
- `parse_input` (`src/cpp/io_utils.cpp:17`) — 严格输入解析 (行长/字符/范围全检)
- `emit_solution` (`src/cpp/io_utils.cpp:68`) — 行式协议 (默认, PyQt 用)
- `emit_solution_json` (`src/cpp/io_utils.cpp:121`) — JSON 协议 (`--json` 切换, 外部工具用)

**为什么两套协议?**
- 行式: 0 第三方依赖, C++ 端没引 JSON 库, 解析也简单
- JSON: 跨语言友好, Web 端可直接 fetch + parse, schema 完整 (status / algorithm / total_distance / runtime_ms / vehicles[].trips[].{load, distance, point_indices, path})

### 2.8 PyQt6 GUI (`src/gui/`)

| 文件 | 职责 | 关键实现 |
|---|---|---|
| `main.py` | 主窗口 + 控件布局 + 样式 | 三栏布局, KPI 卡片, 状态徽章 pill, 实时状态面板, QSS 全局样式 |
| `controller.py` | 调 solver.exe + 解析行式输出 | `subprocess.run` + 临时文件; `parse_solver_output` 状态机 |
| `map_view.py` | QGraphicsView 网格 + 自适应 | `fitInView` 自动缩放; 点阵背景 (`drawBackground` 视口坐标); 圆角关键点 + 阴影 |
| `editor.py` | 编辑状态机 | 5 种模式 (障碍 / S / T / P / 擦除) 互斥;鼠标点击转网格坐标 |
| `animator.py` | 多车补间动画 + 实时状态回调 | `QVariantAnimation` + `InOutQuad` 缓动, 180ms/格; 每车一个 anim; `status_callback` 钩子 |

**动画 + 实时刷新流程** (核心):
1. `_run_and_animate` 把 solver 返回的 Solution 传给 `Animator`
2. Animator 给每辆车一个 `QVariantAnimation` (起点→终点, 180ms, InOutQuad)
3. `valueChanged` 信号驱动 sprite 平滑移动
4. `finished` 触发 `_on_step_done` → 累加距离 + 调 `status_callback`
5. UI 端 `_on_animation_status` 接收回调, 更新右栏每行文字
6. 全部完成时状态徽章变绿

### 2.9 测试与基准 (`tests/`)

| 脚本 | 干什么 | 样本数 | 关键结果 |
|---|---|---|---|
| `brute_force_checker.py` | $n! cdot 2^(n-1)$ 暴力枚举对照 DP | 720 | 658 PASS / 0 MISMATCH / 62 SKIP |
| `dense_benchmark.py` | $n in [3,8] times rho in {0, 0.1, 0.2, 0.3}$ 密集扫描 | 1940 | 4 张性能图; pivot 加速实测 0–1% |
| `verify_sample_library.py` | 样例库 20 用例预期状态校验 | 20 | 20/20 PASS |
| `random_case_generator.py` | 由 seed 确定性生成实例 | — | 被上面三个脚本共享 |
| `seeds.txt` | 60 个固定素数种子 ([1, 280]) | — | 可复现 |

**暴力对拍为什么可信?** 它用**独立的第二份 BFS** 算距离矩阵 (不是直接调 solver.exe 的 dm), 再 `itertools.permutations` 全排列 + 二进制位枚举切分点, 完全脱离 DP 思路。等于黄金标准。

---

## 3 创新点与亮点 (答辩讲点)

### 3.1 算法创新

1. **`singleCost[mask]` 表的一次性求解** ⭐
   - 把"对全集 $[n]$ 的所有子集 mask 计算单车最优代价"做成一个独立的 $O(3^n)$ 一次性中间表
   - 双车 DP 直接查表 + 对称消除, 不重建子距离矩阵, 不重跑子 DP
   - 实测 **460× 加速**, 双车 DP 与单车 DP 运行时间持平
   - 这是一个工业级优化, 多数同学的双车实现是朴素的"枚举划分 + 跑两次单车 DP", 复杂度高出一个量级

2. **对称性消除 (无序划分)**
   - 双车场景下 $(A, B)$ 与 $(B, A)$ 等价, 强制 $0 in A$ 每个无序划分恰被枚举一次
   - 枚举量直接减半

3. **pivot 子集枚举规范化 (任务书的"分治法"加分项)**
   - 固定 pivot = mask 最低位, 只枚举含 pivot 的子集
   - 候选数 $2^k - 1 -> 2^(k-1)$
   - 严格证明等价 (报告定理 1, 基于引理 2 "后续行程顺序可交换")

### 3.2 工程亮点

4. **独立暴力对拍黄金标准**
   - 第二份 BFS + $n! times 2^(n-1)$ 全枚举, 不复用 solver 内部代码
   - 720 例 0 MISMATCH, 是 DP 实现正确性的**直接证据**, 比单元测试可信得多

5. **1940 数据点密集基准**
   - 跨规模 ($n in [3,8]$) × 跨障碍密度 ($rho in {0, 0.1, 0.2, 0.3}$) × 多种子
   - 4 张分析图: 距离-n / 时间-n / 障碍效应 / dp_dc vs dp 比值
   - **得到反直觉结论**: pivot 枚举理论 2× 但实际 0–1%, 因为子集枚举只占总开销小部分

6. **行式 + JSON 双协议**
   - PyQt 默认走行式 (0 第三方依赖)
   - 外部 Web 端可用 `--json` 直接 fetch
   - 接口分层清晰

7. **分类样例库 (10 类 20 用例)**
   - 覆盖 5 类不可行情形 + 5 类可行场景
   - `verify_sample_library.py` 自动校验预期状态, 可入 CI

### 3.3 报告与可视化亮点

8. **IEEE 风格 Typst 排版**
   - 自定义定理/引理/定义/算法环境, 独立计数器
   - 真证明 (引理 1 + 引理 2 + 定理 1), 不是白话描述
   - 36 页, 数据驱动, 不水分

9. **GUI 工业级体验**
   - KPI 卡片 / 状态徽章 / 实时状态面板 / 多色路径 / 自适应缩放 / 点阵背景
   - 实时显示载重 + 已行驶距离 (任务书加分项 2 硬指标)

---

## 4 答辩 Q&A 准备 (按类别)

### 4.1 算法类问题

**Q1: 你的 BFS 复杂度是多少? 为什么不用 Dijkstra?**

A: BFS 在 $4$-邻接网格上是 $O(M cdot L)$。Dijkstra 在边权恒为 1 时退化为 BFS 但多 $O(log(M L))$ 的堆操作开销。A* 需要可采纳启发式且在多源全对最短路上无明显增益。

**Q2: 子集 TSP DP 的状态空间多大?**

A: $2^n times n$, 即 $"mask" in [0, 2^n)$ 配 last $in [0, n)$。$n = 8$ 时 $256 times 8 = 2048$ 个状态, 转移 $O(n)$, 总 $O(2^n cdot n^2) approx 16384$ 次操作。

**Q3: 划分 DP 的转移方程?**

A: $G["mask"] = min_(Q subset.eq "mask", Q != emptyset) "laterCost"(Q) + G["mask" without Q]$, 其中 $G(emptyset) = 0$。顶层 $"OPT" = min_(Q_1) "firstCost"(Q_1) + G([n] without Q_1)$, $Q_1$ 是首次行程子集 (S-起)。

**Q4: 为什么 dp_dc (pivot 枚举) 在实测中没快多少?**

A: 理论上枚举量减半, 但子集枚举只占完整 DP 流程的一小部分 — 距离表查询、容量过滤、最优路径回溯加起来占了大头。1940 数据点上实测比值 0.99–1.04, 几乎不可观察。**这是诚实的实验结果**, 没有为了好看而夸大。

**Q5: 双车 DP 复杂度?**

A: 朴素实现是 $O(2^n cdot "单车DP")$。我们的优化用 `singleCost[mask]` 表把它压到 $O(3^n)$ (singleCost 自身的求解), 双车求解阶段只是 $O(2^(n-1))$ 的查表 + 对称消除。$n = 8$ 时整个双车 DP 实测约 0.2 ms。

**Q6: 为什么强制 $0 in "mask"_1$?**

A: 无序划分对称性。$("mask"_1, "mask"_2)$ 与 $("mask"_2, "mask"_1)$ 是同一个无序划分但被算两次。强制点 0 属于 $"mask"_1$ 后, 每个划分只被枚举一次, 枚举量减半。

**Q7: 贪心算法什么时候会次优?**

A: 当收集点空间分布存在"不均匀引力"时。报告 §6.5 给出对抗实例 $3 times 10$ 网格: 贪心首程选最近的 $P_0$ 陷入近邻陷阱, 最终代价 15 vs DP 最优 13 (+15.4%)。在 372 例随机样本上, 31% 严格次优, 平均 +14.5%, 最坏一例 +120%。

### 4.2 实现类问题

**Q8: 行式协议长什么样? 为什么不用 JSON?**

A: 行式格式见报告附录 B, 形如 `STATUS ok` / `TOTAL_DISTANCE 34` / `TRIP 1 LOAD 3 DIST 14` / `PATH 0,0 0,1 ...`。**不用 JSON 是为了避免 C++ 端引第三方库**, stdlib 直接 << 输出就行。我们额外支持 `--json` 切换, 给外部工具用 — 两套协议并存。

**Q9: PyQt 怎么和 C++ 通信?**

A: `subprocess.run` 调用 `solver.exe`, 把输入文件路径作为命令行参数, 解析其 stdout。`controller.py:parse_solver_output` 是状态机解析器, 逐行读取 STATUS / ALGORITHM / VEHICLE / TRIP / PATH 等字段, 构造 Python 端的 `Solution` 对象。

**Q10: 动画怎么实现平滑移动?**

A: 每辆车一个 `QVariantAnimation`, 起点和终点是相邻两格的场景坐标, 单步 180 ms, `InOutQuad` 缓动曲线 (加速-减速)。`valueChanged` 信号每帧 (~60 FPS) 触发 sprite 位置更新。`finished` 触发下一格, 链式推进。

**Q11: 如何在动画过程中实时刷新载重和已行驶距离?**

A: `Animator` 暴露 `status_callback(vi, info)` 钩子, 在四个时机触发: 初始态 / 每完成一格 / trip 切换 / 全部完成。`info` 字段 `{trip_idx, num_trips, load, distance, done}`。UI 端 `_on_animation_status` 解析后更新对应车辆的标签文字, 完成时整行背景变绿。

### 4.3 实验与正确性

**Q12: 你怎么证明 DP 实现是对的?**

A: 三层证据。第一, 引理 1 + 定理 1 的形式化数学证明 (报告 §5)。第二, 720 例独立暴力对拍 — 用**第二份 BFS + 全排列 + 二进制位枚举切分点**, 跟 solver 的 DP 完全不共享代码, 0 mismatch。第三, 1940 数据点密集基准上 `dp` 与 `dp_dc` 输出值在所有 $n$ 上严格相同。

**Q13: 暴力对拍的复杂度是多少? 为什么不直接用暴力解?**

A: $O(n! cdot 2^(n-1))$ — 全部访问顺序 × 全部切分点。$n = 5$ 时 120 × 16 = 1920, 秒级可解; $n = 8$ 时 40320 × 128 = 5160960, 已经接近分钟级; $n = 10$ 完全不可行。所以暴力**只能用来对拍小规模**, 实际求解必须用 DP。

**Q14: 你测了多大规模?**

A: 报告里跑到 $n = 8$ (任务书约束的上限)。$2^8 = 256$ 个 mask 状态, 跑完一次 DP $approx 0.2$ ms。理论上 $n = 12$ 也能秒级完成 ($2^12 = 4096$), 但任务书没要求, 没测。

**Q15: 如果 $n = 20$ 你怎么办?**

A: 精确 DP 不再可行 ($3^20 approx 3.5 times 10^9$)。可选: ① Meet-in-the-Middle 把状态空间拆成两半合并; ② 启发式 (Lin-Kernighan, 2-opt, Or-opt 局部搜索); ③ 列生成方法分阶段求解。报告 §7 也提到这是未来方向。

### 4.4 工程类问题

**Q16: 项目代码量多大?**

A: C++ 后端 ~1100 行 (8 个 .cpp/.h), Python 前端 ~750 行 (5 个 .py), 测试脚本 ~600 行 (5 个 .py), 报告 ~900 行 Typst → 36 页 PDF。

**Q17: 你怎么处理非法输入?**

A: `feasibility.cpp::check_feasibility` 在算法分派前一次性检查 5 大类约束 (关键点位置 / S=T / 坐标重复 / 重量越界 / 容量矛盾 / BFS 可达性), 失败立即返回 `STATUS infeasible / REASON <text>`, GUI 弹错误对话框允许用户重新编辑。报告 §3.3 有完整 REASON 文本表。

**Q18: 项目有哪些测试?**

A: 三类共 3032 个测试点。① 720 例暴力对拍 (DP 正确性), ② 1940 数据点密集基准 (性能扫描), ③ 20 例样例库自检 (REASON 文本契约 + 可行性判定). 报告 §6 全部公开了数据和脚本路径。

**Q19: 为什么报告里说 pivot 加速是 0–1%, 不是"分治法应该快很多"?**

A: 这是**实证结论**, 不是假设。在小规模 ($n <= 8$) 上, 子集枚举不是性能瓶颈 — 距离表查询、容量过滤、回溯重建占了大部分常数。理论上枚举量是 $2^n - 1$ → $2^(n-1)$, 但端到端实际加速被这些常数稀释了。报告诚实地报告了这一点, 没有为加分项夸大。在更大 $n$ 上 pivot 加速会更明显, 但任务书约束了 $n <= 8$。

### 4.5 创新与亮点 (主动引导)

**Q20: 你这个项目相对其他同学的最大不同是什么?**

A: 三点。① **算法层有真优化**: singleCost 表把双车 DP 从朴素 $O(2^n cdot "单车DP")$ 压到 $O(3^n)$, 实测 460× 加速; 多数同学是暴力枚举划分跑两次单车 DP。② **报告有真证明**: 12 个定义/引理/定理块, 严格证明 pivot 枚举的等价性, 而不是白话描述。③ **实验有真数据**: 720 + 372 + 1940 = 3032 个测试点, 4 张密集基准图, 诚实报告 pivot 加速只有 0-1%, 而不是"理论 2× 实际就 2×"。

---

## 5 如果时间有限怎么准备

**最重要的 3 件事 (按答辩频次排序)**:

1. **算法核心**: 能在白板上画出"两层 DP" (内层 TSP + 外层划分) 和 `singleCost[mask]` 表是怎么算的; 能解释 pivot 枚举为什么等价
2. **测试方法**: 能解释暴力对拍是怎么做的 (独立第二份 BFS + 全排列 + 切分点), 为什么 720 例 0 mismatch 是有力证据
3. **诚实的实验结论**: 准备好回答"为什么分治没快多少", 答案是子集枚举只占总开销小部分 (有 1940 数据点支持)

剩下的细节再翻这份文档。

---

## 6 速查: 哪个文件干什么

| 想知道 | 看哪里 |
|---|---|
| BFS 实现 | `src/cpp/grid.cpp` |
| 不可行判定 | `src/cpp/feasibility.cpp` |
| 距离矩阵 | `src/cpp/solver_common.cpp` |
| 单车 DP / pivot 枚举 / singleCost | `src/cpp/dp.cpp` |
| 双车 DP / 对称消除 | `src/cpp/dual.cpp` |
| 贪心 | `src/cpp/greedy.cpp` |
| 输入解析 + 行式输出 + JSON 输出 | `src/cpp/io_utils.cpp` |
| 主窗口 + KPI + 实时状态 | `src/gui/main.py` |
| 多车补间动画 + status_callback | `src/gui/animator.py` |
| 调 solver 解析输出 | `src/gui/controller.py` |
| 暴力对拍 | `tests/brute_force_checker.py` |
| 密集基准 1940 点 | `tests/dense_benchmark.py` |
| 样例库自检 | `tests/verify_sample_library.py` |
| 报告源 | `report.typ` |
| 编译好的报告 | `report.pdf` |

祝顺利。
