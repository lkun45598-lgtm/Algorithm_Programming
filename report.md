# 《算法设计与分析》课程设计报告

## 题目: 基于多策略的城市垃圾收运路线规划

**学生姓名:**
**学  号:**
**指导教师:**
**完成日期:** 2026 年 5 月

---

## 一、问题分析与建模

城市环卫部门日常需要在城区路网中调度垃圾车,将分散在各个收集点的垃圾运回处理厂。出于车辆载重、燃油消耗与人员效率的考虑,如何在保证所有收集点都被准确处理的前提下,最小化车辆累计行驶距离,是一个具有现实意义的运筹学问题。本课程设计将该实际场景抽象为一个**容量受限的多行程旅行商问题**(Capacitated Vehicle Routing Problem with a single depot and a separate dump,即带卸货点的 C-VRP 变体)。

形式化地,给定一个 $M\times N$ 的字符网格 $G$,其中字符 `.` 表示可通行空地,`#` 表示障碍。网格中固定三类关键点:停车场 $S$(车辆首程的出发点)、处理厂 $T$(每次行程结束时必须到达的卸货点)、收集点集合 $\mathcal{P}=\{P_0,P_1,\ldots,P_{N-1}\}$,且 $N\le 8$。每个收集点 $P_i$ 携带重量 $w_i\in\{1,2,3\}$。车辆有最大载重 $W_{\max}$,题目约束 $\max_i w_i\le W_{\max} < \sum_i w_i$,从而至少需要两次行程才能完成全部收运。

一次合法行程(Trip)由一个起点(首次为 $S$,后续为 $T$)、一段访问序列 $\langle P_{i_1},P_{i_2},\ldots,P_{i_k}\rangle$ 以及终点 $T$ 组成,且满足载重约束 $\sum_{j=1}^{k} w_{i_j} \le W_{\max}$。整体解为有序行程序列 $\mathcal{T}=(T_1,\ldots,T_m)$,要求:(1) 所有收集点恰好在某一行程中出现一次;(2) $T_1$ 起点为 $S$,$T_2,\ldots,T_m$ 起点为 $T$;(3) 每个行程终点都为 $T$。优化目标是最小化总行驶距离

$$\min \sum_{j=1}^{m} \mathrm{dist}(T_j).$$

由于车辆在网格上以 4 邻接方式移动,任意两个关键点之间的"代价"即为绕过障碍后的 BFS 最短步数。下面所有算法都建立在预计算的关键点距离矩阵之上。

## 二、模块划分与关键数据结构

系统采用 **C++ 后端 + PyQt6 前端** 的双层架构:C++ 完成所有重量级算法运算,并通过标准输入/输出的行式文本协议与外界通信;Python 前端负责地图编辑、参数配置、算法选择、求解结果可视化与动画回放。两层完全解耦,便于独立替换与单元测试。

C++ 源码位于 `src/cpp/`,模块组织如下:

- `types.h` —— 通用数据结构 `Point` / `KeyPoints` / `Trip` / `Solution`。
- `grid.{h,cpp}` —— 网格通行判定与 BFS 最短距离/路径计算。
- `feasibility.{h,cpp}` —— 输入合法性检查 `check_feasibility()`。
- `solver_common.{h,cpp}` —— 距离矩阵 `DistanceMatrix` 与行程路径拼接。
- `dp.{h,cpp}` —— 子集 TSP 与划分 DP,支持标准枚举与分治枚举两种模式。
- `greedy.{h,cpp}` —— 最近邻贪心。
- `dual.{h,cpp}` —— 双车协同求解器。
- `io_utils.{h,cpp}` —— 输入解析与输出协议。
- `main.cpp` —— 命令行入口与算法分派。

关键数据结构如下:`KeyPoints` 用 `Point parking` 表示 $S$,`Point plant` 表示 $T$,`std::vector<Point> collects`/`weights` 表示收集点与权重,`int wMax` 为载重。`DistanceMatrix` 为 $K\times K$ 的二维表,$K=N+2$,采用统一全局编号 `0=S, 1=T, 2..N+1=P_0..P_{N-1}`,既存 `dist[u][v]`(最短步数,负值代表不可达),也存 `path[u][v]`(完整网格路径,供动画使用)。`Trip` 记录一次行程的访问序列、载重、距离与完整路径。`Solution` 是通用结果容器:单车解写入 `trips`,双车解写入 `vehicleTrips`,并附带算法名、总距离、运行毫秒数与状态信息。

PyQt6 前端模块 `src/gui/` 包含:`controller.py` 调用 C++ 并解析输出;`map_view.py` 与 `editor.py` 提供地图绘制与点位编辑;`animator.py` 实现路径动画与回放;`main.py` 装配主窗口。

## 三、算法详细设计

### 3.1 BFS 计算关键点最短距离

由于网格 4 邻接且边权均为 1,单源最短路用 BFS 求解最佳,时间复杂度为 $O(MN)$。`Grid::bfsDistances(from)` 返回一张距离场;`Grid::shortestPath(from,to)` 同时维护前驱表 `prev[r][c]`,在搜索到目标后反向回溯还原完整路径,翻转后即得到 `from→to` 的具体格子序列。`build_distance_matrix()` 调用 BFS $K$ 次,得到完整的距离矩阵与路径矩阵,后续所有算法直接索引该表,无需重复搜索网格。

### 3.2 合法性检查 `check_feasibility()`

`check_feasibility()` 顺序执行三类校验:

(1) **关键点合法性**:$S$、$T$ 与所有 $P_i$ 必须落在可通行格,任一在障碍或越界则报错;同时要求至少有一个收集点。

(2) **重量约束**:计算 $\max w_i$ 与 $\sum w_i$,要求 $W_{\max}\ge\max w_i$(否则该重量点永远装不下),并要求 $\sum w_i > W_{\max}$(否则一次即可,与"多行程"题目设定不符)。

(3) **互相可达性**:从 $S$ 出发跑一次 BFS,检验 $T$ 与所有 $P_i$ 是否都落在 $S$ 的可达区域内。由于网格无向,只需一次 BFS 即可保证两两可达。

任一项失败立即返回 `infeasible` 状态并附原因,前端会展示具体说明供用户修改输入。

### 3.3 子集 TSP 动态规划

任意一次合法行程都对应一个收集点子集 $Q\subseteq\{0,\ldots,N-1\}$ 与一个访问序列。给定 depot(`IDX_S` 或 `IDX_T`),令

$$\mathrm{tsp}[\mathrm{mask}][i] = \text{从 depot 出发,访问 mask 中所有点,以 }P_i\text{ 结束的最短代价}.$$

初始化:对每个 $i$,若可达则 $\mathrm{tsp}[\{i\}][i] = d(\mathrm{depot}, P_i)$。转移按状态升序:对每个 mask 与其中的 last,枚举尚未访问的 nxt,更新 $\mathrm{tsp}[\mathrm{mask}\,|\,(1\!<\!<\!\mathrm{nxt})][\mathrm{nxt}]$。状态数 $O(2^N\cdot N)$,转移 $O(N)$,总复杂度 $O(2^N\cdot N^2)$。

由于首次行程以 $S$ 起点而其余以 $T$ 起点,二者距离表不同,程序分别得到 `tspS` 与 `tspT`。再各自计算 `firstCost[mask]` 与 `laterCost[mask]`:走完 mask 后必须回 $T$ 卸货,故

$$\mathrm{firstCost}[\mathrm{mask}] = \min_{i\in\mathrm{mask}} \big\{\mathrm{tspS}[\mathrm{mask}][i] + d(P_i, T)\big\},$$

`laterCost` 同理。同时记下取得最小值的 `lastIdx`,作为后续路径回溯的种子。

### 3.4 划分动态规划

把所有 later-trip 视为一次切分:定义

$$G[\mathrm{mask}] = \text{用若干以 }T\text{ 起终点的 later-trip 收完 mask 内所有点的最小总代价}.$$

边界 $G[0]=0$,转移为枚举 mask 内第一条 later-trip 的子集 $Q\subseteq\mathrm{mask}$:

$$G[\mathrm{mask}] = \min_{\substack{Q\subseteq\mathrm{mask},\,Q\ne\varnothing\\ \mathrm{weight}(Q)\le W_{\max}}} \big\{\mathrm{laterCost}[Q] + G[\mathrm{mask}\oplus Q]\big\}.$$

顶层把首程拼上:

$$\mathrm{Total} = \min_{\substack{Q_1\subseteq\mathrm{full},\,Q_1\ne\varnothing\\ \mathrm{weight}(Q_1)\le W_{\max}}} \big\{\mathrm{firstCost}[Q_1] + G[\mathrm{full}\oplus Q_1]\big\}.$$

重量约束在求解前一次性把不合法 mask 的 `firstCost`/`laterCost` 置为 `INF` 即可。回溯阶段用 `pick[mask]` 记录最优的 $Q$,沿链 $\mathrm{rem}\leftarrow\mathrm{rem}\oplus Q$ 直到 0,即可还原全部 later-trip,再用 `recover_order` 配合 `tsp` 表回出每个 trip 内的访问顺序。

### 3.5 分治法优化子集枚举(加分项 3)

经典枚举 $\sum_{\mathrm{mask}}\sum_{Q\subseteq\mathrm{mask}} 1 = 3^N$,实现是 `for (int Q = mask; Q > 0; Q = (Q-1)&mask)`,这已经是 $O(3^N)$ 的最优表达方式。本课程设计在此之上进一步引入**分治枚举**:对每个 mask 取其最低位 `pivot = mask & -mask`,**强制 pivot 属于第一条 later-trip 子集 $Q$**,然后枚举 $\mathrm{mask}\setminus\mathrm{pivot}$ 的所有子集 $R$,令 $Q=\mathrm{pivot}\,|\,R$。代码片段(摘自 `dp.cpp`):

```cpp
int pivot = mask & -mask;
int rest_of_mask = mask ^ pivot;
int R = rest_of_mask;
while (true) {
    int Q = pivot | R;
    if (laterCost[Q].cost < INF) {
        int leftover = mask ^ Q;
        if (G[leftover] < INF) {
            int cand = laterCost[Q].cost + G[leftover];
            if (cand < G[mask]) { G[mask] = cand; pick[mask] = Q; }
        }
    }
    if (R == 0) break;
    R = (R - 1) & rest_of_mask;
}
```

之所以称为分治,是因为这一构造把"枚举 $Q\subseteq\mathrm{mask}$"按"pivot 在 $Q$ 还是在 $\mathrm{mask}\setminus Q$"二分:若 pivot $\in Q$,即上述显式枚举;若 pivot $\in \mathrm{mask}\setminus Q$,该划分会在更小的 $G[\mathrm{mask}\setminus Q]$ 递归子问题中被覆盖,**无需在 mask 层重复枚举**。两种枚举得到的全局最优值必然相等,但分治版本只走前一半,把每个 $(Q,\mathrm{mask})$ 序偶的枚举次数从 2 降到 1,实测在大样例上常数约节省 1/6。

### 3.6 贪心法(最近邻启发式)

贪心从当前位置出发,遍历未访问且满足载重约束($\mathrm{load}+w_i\le W_{\max}$)的收集点,选距离最近者前进。若无任何点能装,则去 $T$ 卸货,开启新行程并把起点切换为 $T$;最后一段也强制回到 $T$。该过程 $O(N^2)$。它不一定能得到最优解,但在简单样例上常常碰巧最优,可作为 DP 的对照基线。

### 3.7 双车协同(加分项 1)

两辆车共享 $S/T$。`solve_dual` 枚举所有 $2^N$ 个二分划分 `mask1 / mask2 = full ^ mask1`,每个划分构造两个子 `KeyPoints` 与对应的子 `DistanceMatrix`,分别用单车 DP(或单车贪心)求解,取两车总距离最小者。需要注意子问题中 $\sum w$ 可能 $\le W_{\max}$,此时单车 DP 自然退化为单次 first-trip,代码无需特判;`mask1 = 0` 允许其中一辆车不出动,自然兼容单车场景。

## 四、复杂度分析

设收集点数为 $N$,网格大小 $K = M\times N_{\text{cols}}$:

| 模块 | 时间复杂度 | 空间复杂度 |
|------|-----------|-----------|
| 单源 BFS | $O(K)$ | $O(K)$ |
| 距离矩阵 (BFS × K) | $O(N\cdot K)$ | $O(N^2)$ + 路径表 |
| 子集 TSP DP(一次 depot) | $O(2^N\cdot N^2)$ | $O(2^N\cdot N)$ |
| 划分 DP(标准枚举) | $O(3^N)$ | $O(2^N)$ |
| 划分 DP(分治枚举) | $O(3^N)$(常数减半) | $O(2^N)$ |
| 最近邻贪心 | $O(N^2)$ | $O(N)$ |
| 双车 DP | $O(2^N\cdot$ 单车 DP$)$ | $O(2^N\cdot N)$ |

由于 $N\le 8$,$2^N=256$,$3^N=6561$,所有算法均在毫秒级结束。

## 五、测试与结果对比

### 5.1 测试样例

测试集位于 `data/`:`sample_small`($N=4$,$8\times 8$ 网格)、`sample_medium`($N=6$,$12\times 12$ 网格)、`sample_large`($N=8$,$15\times 15$ 网格)。三组样例都含障碍,且 $W_{\max}$ 均迫使至少两次行程,符合题目设定。每组样例分别用 5 种算法求解。

### 5.2 总距离对比

| 样例 | $N$ | 网格 | DP | DP+分治 | 贪心 | 双车 DP | 双车贪心 |
|------|-----|------|-----|---------|------|---------|----------|
| sample_small  | 4 | 8×8   | 34 | 34 | 34 | 30 | 30 |
| sample_medium | 6 | 12×12 | 64 | 64 | 78 | 62 | 62 |
| sample_large  | 8 | 15×15 | 92 | 92 | 98 | 84 | 84 |

### 5.3 运行时间对比(毫秒)

| 样例 | DP | DP+分治 | 贪心 | 双车 DP | 双车贪心 |
|------|-----|---------|------|---------|----------|
| small  | 0.018 | 0.016 | 0.008 | 0.900  | 0.871  |
| medium | 0.034 | 0.034 | 0.005 | 7.408  | 7.015  |
| large  | 0.184 | 0.152 | 0.014 | 92.276 | 61.296 |

### 5.4 分析

(1) **正确性交叉验证**:DP 标准枚举与 DP+分治枚举在三个样例上得到的最优总距离完全一致(34/64/92),侧面验证分治版本的正确性;由于二者均枚举所有可行划分,理论上必然得到全局最优。

(2) **DP vs 贪心**:在 small 上贪心碰巧也得到 34;但 medium 上贪心 78 vs DP 64,多出约 22%;large 上贪心 98 vs DP 92,多出约 7%。可见最近邻策略缺乏全局视野,在某些"绕远的近邻"上会被坑。但贪心在 large 上仅耗时 0.014 ms,比 DP 快约 13 倍,是快速预估或更大规模场景下的可选基线。

(3) **单车 vs 双车**:双车 DP 在三个样例上分别得到 30 / 62 / 84,相对单车 DP 节省 11.8% / 3.1% / 8.7%,验证了协同的收益,但幅度取决于点位分布——`sample_medium` 中收集点聚簇较紧,二分后两车仍互相干扰,节省最少。

(4) **双车开销**:双车的运行时间约为单车的 50× ~ 500×,原因是外层枚举 $2^N$ 种划分,每个划分都要重建子距离矩阵并跑一次完整单车 DP。large 上 92 ms,仍在可接受范围内。

(5) **分治枚举效益**:large 上 DP+分治从 0.184 ms 降到 0.152 ms,节省约 17%,与"每个三元组只被枚举一次"的理论预期相符。

## 六、加分项实现说明

(1) **双车协同(加分项 1)**:见 `src/cpp/dual.cpp`。不仅支持双车 DP,也支持双车贪心作为速度对照。GUI 中以两种不同颜色路径区分两车的行程,动画并行播放。

(2) **图形化界面与交互演示(加分项 2)**:PyQt6 实现,见 `src/gui/`。功能包括:鼠标点选放置/移除障碍及关键点,SpinBox 调整重量与 $W_{\max}$,左侧算法面板选择 5 种算法之一,运行后中部画布按 trip 顺序播放车辆移动轨迹,右侧结果面板列出总距离、运行时间与每次 trip 的访问序列、载重、距离。支持文件(`data/` 目录)与交互式两种输入,前后端通过文本协议解耦,后端可独立通过 `solver.exe data/sample_small.txt` 调用。

(3) **分治法优化子集枚举(加分项 3)**:见 `dp.cpp` 中 `DpMode::DivideConquer` 分支。命令行算法名 `dp_dc` 即可启用,可与标准 `dp` 模式互相比对正确性与速度。

## 七、总结与不足

本设计完整实现了题目要求的全部功能(输入/合法性/BFS/DP/贪心/输出/对比)以及全部三项加分内容,并在三个不同规模的样例上完成端到端测试。代码层次清晰、接口规范,C++ 后端可通过纯文本协议被任意前端复用。

**主要局限性**:由于划分 DP 的 $O(3^N)$ 与双车 DP 的 $O(2^N\cdot 3^N)$ 性质,$N$ 增长到 12 以上时单车将逼近秒级、双车将到分钟级;题目中 $N\le 8$ 的限制恰好保证算法工程可行。

**改进方向**:(i) 引入 meet-in-the-middle,把 TSP 状态拆成左右各 $N/2$ 位,常数显著降低;(ii) 接入 LKH/2-opt 等启发式,作为大规模场景的近似算法;(iii) 把双车扩展到任意 $V$ 辆车,改用 set-cover 风格的列生成方法;(iv) 加入更多障碍/动态拥堵模型,贴近真实城市路况。

---

## 附录 A: 输入文件格式

```
<M> <N>
<row 0: 长度 N 的字符串, '.'=空地, '#'=障碍>
<row 1>
...
<row M-1>
<S_row> <S_col>
<T_row> <T_col>
<K>                            # 收集点数 (1 ≤ K ≤ 8)
<P0_row> <P0_col> <w0>
<P1_row> <P1_col> <w1>
...
<P{K-1}_row> <P{K-1}_col> <w_{K-1}>
<W_max>
ALGO <dp | dp_dc | greedy | multi_dp | multi_greedy>
```

例如 `data/sample_small.txt`:

```
8 8
........
.######.
........
.######.
........
.######.
........
........
0 0
7 7
4
1 0 1
3 0 2
5 0 1
6 7 3
3
ALGO dp
```

## 附录 B: 输出协议

```
STATUS <ok | error | infeasible>
[REASON ...]                    # 仅在 status != ok 时出现
ALGORITHM <name>
TOTAL_DISTANCE <int>
RUNTIME_MS <float>
VEHICLES <n>                    # 1 = 单车, 2 = 双车
VEHICLE <vid> TRIPS <count>     # count 可为 0 (空闲车辆)
TRIP <tid> LOAD <load> DIST <dist>
POINTS <i1> <i2> ...            # 0-indexed 收集点编号
PATH <r1>,<c1> <r2>,<c2> ...    # 完整网格路径
TRIP ...
...
END
```

错误或不可行时,输出 `STATUS error/infeasible` 与 `REASON ...`;前端弹窗提示。对应解析见 `src/gui/controller.py::parse_solver_output`。
