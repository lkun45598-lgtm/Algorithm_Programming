// 课程设计报告 (顶会风格) —— Typst
// 编译: typst compile report.typ

#set document(
  title: "基于多策略的城市垃圾收运路线规划",
  author: "课程设计"
)
#set page(
  paper: "a4",
  margin: (x: 2.4cm, y: 2.6cm),
  numbering: "1"
)
#set text(
  font: ("Microsoft YaHei", "Microsoft YaHei UI"),
  size: 10.5pt,
  lang: "zh",
  region: "cn"
)
#set par(justify: true, leading: 0.78em, first-line-indent: 2em)
#set heading(numbering: "1.1")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  set text(size: 17pt, weight: "bold")
  v(1.2em)
  it
  v(0.4em)
  line(length: 100%, stroke: 0.6pt + black)
  v(0.4em)
}
#show heading.where(level: 2): it => {
  set text(size: 13pt, weight: "bold")
  v(0.7em)
  it
  v(0.1em)
}
#show heading.where(level: 3): it => {
  set text(size: 11.5pt, weight: "bold")
  v(0.4em)
  it
}

// 代码块
#show raw.where(block: true): it => block(
  fill: rgb("#f6f7f9"),
  inset: (x: 10pt, y: 7pt),
  radius: 4pt,
  stroke: 0.5pt + rgb("#dcdfe5"),
  width: 100%,
  text(font: ("Consolas"), size: 9pt, it)
)
#show raw.where(block: false): it => box(
  fill: rgb("#f0f1f4"),
  inset: (x: 3pt, y: 1pt),
  outset: (y: 2pt),
  radius: 2pt,
  text(font: "Consolas", size: 9.4pt, it)
)

#set table(stroke: (x, y) => {
  if y == 0 { (top: 1pt + black, bottom: 0.6pt + black) }
  else if y == 1 { (top: 0.4pt + black.lighten(30%)) }
})

// ============ 自定义环境: Lemma / Theorem / Definition / Algorithm ============
// 引理 和 定理 各自独立编号
#let lemma-counter = counter("lemma")
#let theorem-counter = counter("theorem")
#let definition-counter = counter("definition")
#let algorithm-counter = counter("algorithm")

#let theorem(title: "", body) = {
  theorem-counter.step()
  block(
    fill: rgb("#eef4fb"),
    stroke: (left: 3pt + rgb("#3b7ddd")),
    inset: (left: 12pt, top: 8pt, bottom: 8pt, right: 12pt),
    width: 100%,
    [#text(weight: "bold")[定理 #context theorem-counter.display()] #if title != [] [ (#title)]. #body]
  )
}
#let lemma(title: "", body) = {
  lemma-counter.step()
  block(
    fill: rgb("#f0f9ee"),
    stroke: (left: 3pt + rgb("#82b366")),
    inset: (left: 12pt, top: 8pt, bottom: 8pt, right: 12pt),
    width: 100%,
    [#text(weight: "bold")[引理 #context lemma-counter.display()] #if title != [] [ (#title)]. #body]
  )
}
#let definition(title: "", body) = {
  definition-counter.step()
  block(
    fill: rgb("#fff8eb"),
    stroke: (left: 3pt + rgb("#d6a948")),
    inset: (left: 12pt, top: 8pt, bottom: 8pt, right: 12pt),
    width: 100%,
    [#text(weight: "bold")[定义 #context definition-counter.display()] #if title != [] [ (#title)]. #body]
  )
}
#let proof(body) = {
  block(
    inset: (left: 12pt, top: 4pt, bottom: 4pt),
    [#emph[证明.] #body #h(1fr) $square.stroked$]
  )
}
#let algorithm(title: "", body) = {
  algorithm-counter.step()
  block(
    fill: rgb("#fafbfc"),
    stroke: 0.6pt + rgb("#3c4659"),
    inset: 10pt,
    width: 100%,
    radius: 3pt,
    [
      #text(weight: "bold")[算法 #context algorithm-counter.display(): #title]
      #v(0.2em)
      #line(length: 100%, stroke: 0.4pt + gray.lighten(30%))
      #v(0.2em)
      #body
    ]
  )
}

// ===================== 封面 =====================
#align(center)[
  #v(4cm)
  #text(size: 22pt, weight: "bold")[基于多策略的城市垃圾收运路线规划]
  #v(0.4em)
  #text(size: 13pt, fill: rgb("#4a5468"))[融合 BFS、动态规划、贪心、分治法与协同调度的工程实现与实证分析]
  #v(0.8em)
  #text(size: 12pt)[—— 《算法设计与分析》课程设计报告 ——]
  #v(3.5cm)
  #grid(
    columns: (auto, auto),
    column-gutter: 16pt,
    row-gutter: 14pt,
    align: (right, left),
    text(weight: "bold")[题　　目], [基于多策略的城市垃圾收运路线规划],
    text(weight: "bold")[学　　院], [人工智能与低空技术学院],
    text(weight: "bold")[专　　业], [人工智能],
    text(weight: "bold")[组　　员], grid(
        columns: (auto, auto),
        column-gutter: 8pt,
        row-gutter: 4pt,
        align: (left, left),
        [雷　正], [(202434610309)],
        [蔡铭飞], [(202434610301)],
        [谢志伟], [(202434610328)],
    ),
    text(weight: "bold")[指导教师], [胡洁],
    text(weight: "bold")[完成日期], [2026 年 5 月 15 日]
  )
]
#pagebreak()

// ===================== 摘要 =====================
#align(center)[#text(size: 16pt, weight: "bold")[摘　要]]
#v(0.4em)

在网格化城市路网中,起点 $S$ 与卸货点 $T$ 物理分离,车辆需在容量约束下规划多次行程访问全部收集点,使总行驶距离最短。本文将其形式化为带专属卸货点的容量受限多行程旅行商问题,并提出由内层子集旅行商动态规划与外层划分动态规划组成的两层精确求解结构;在划分 DP 的内层子集枚举上,引入基于轴元素 (pivot) 的对称性消除,把当前状态显式转移候选数从 $2^k - 1$ 缩减到 $2^(k-1)$,在常数意义上减半。本文进一步将该框架扩展至双车场景,通过 $2^n$ 二划分枚举确定收集点分配;另实现最近邻贪心作为启发式对照,并以 C++17 后端 + PyQt6 前端的双层架构落地,前后端经行式文本协议解耦。证明方面,给出划分 DP 最优性 (引理 1) 与 pivot 枚举对标准枚举等价性 (定理 1) 的形式化结论,后者基于"后续行程顺序可交换"性质 (引理 2) 严格论证。实证方面,固定 60 个随机种子,共 720 例独立暴力对拍,在所构造样例上动态规划解与暴力解 100% 一致 (含 62 例由暴力与求解器同步识别为不可行);进一步在 $n in [3, 8] times rho in {0, 0.10, 0.20, 0.30}$ 共 1940 个数据点的密集基准上测量,`dp` 与 `dp_dc` 在所有 $n$ 上输出值完全相同,而 pivot 枚举的端到端实际加速仅在 $0$–$1%$ 量级 (理论上枚举量减半,但子集枚举仅占总开销小部分);双车协同 (P6 优化后) 相对单车在 $n in [3, 8]$ 上稳定节省 $4.6%$–$5.0%$ 总距离,且实际运行时间与单车持平 (优化前 $approx 460 times$ 慢);最近邻贪心的次优差随 $n$ 增长,$n=3$ 时仅 $1.2%$, $n=8$ 时已达 $13.3%$。

#align(right)[#text(weight: "bold")[关键词:] 多行程旅行商问题; 容量受限车辆路径; 子集动态规划; 分治枚举; 双车协同; 最近邻贪心]

#pagebreak()

// ===================== 目录 =====================
#align(center)[#text(size: 16pt, weight: "bold")[目　录]]
#v(0.4em)
#outline(title: none, indent: 1em)

// ===================== 1 引言 =====================
= 引言

车辆路径问题 (Vehicle Routing Problem, VRP) 是运筹优化中的经典问题,衍生出若干面向具体应用场景的变体。本文研究其中一类与城市垃圾收运高度匹配的变体:车队从固定停车场 $S$ 出发,沿离散化的城市路网访问若干带重量的收集点,载重达到上限后必须前往与 $S$ 物理分离的处理厂 $T$ 卸货,卸货后可继续作业,直至所有收集点恰被访问一次。优化目标是行程总距离最短。

相对于经典 VRP,该设定具有三点结构性差异。第一,起点 $S$ 与卸货点 $T$ 物理分离,首次行程与后续行程的起点不同,导致两套距离矩阵在算法层必须显式区分。第二,可通行区域由 ${".", "\#"}$ 字符网格刻画,边权恒为 1,$4$-邻接 BFS 即可在 $O(M L)$ 内求得任意两点最短路径,无须借助高级路网算法。第三,题目约束 $n <= 8$,$2^n = 256$,$3^n = 6561$,使精确求解可行,本文得以聚焦最优性与算法等价性这两类强论断,而非启发式近似的实证调参。

本文围绕该问题做了如下工作:在内层子集旅行商 DP 与外层划分 DP 构成的两层求解框架基础上 (@sec:algo),引入基于轴元素 (pivot) 的对称性消除,把每个状态显式转移候选数从 $2^k - 1$ 减为 $2^(k - 1)$ (@sec:divconq);将该框架扩展至双车场景,以 $2^n$ 二划分枚举确定收集点分配 (@sec:dual);形式化证明划分 DP 的最优性 (引理 1) 与 pivot 枚举对标准枚举的等价性 (定理 1);通过 720 例随机暴力对拍独立检验 DP 与暴力解的一致性,并构造一个 $3 times 10$ 对抗实例,定量演示最近邻贪心可能严格次优 (@sec:exp);此外提供基于 PyQt6 的图形化前端,支持交互式编辑、五种算法的即时切换与多车并发动画 (@sec:gui)。

// ===================== 2 问题描述 =====================
= 问题描述与符号体系

== 输入

#definition(title: "网格")[
设 $M, L in NN^+$。一个 $M times L$ 的网格 $G$ 由矩阵 $g in {".", "\#"}^(M times L)$ 表示,其中 $g_(i j) = "."$ 表示位置 $(i,j)$ 可通行,$g_(i j) = "\#"$ 表示障碍。网格上两位置之间的距离由 4-邻接最短路径长度定义,记为 $d_G (u, v)$,若不可达则 $d_G (u, v) = +infinity$。
]

#definition(title: "实例")[
垃圾收运问题的一个实例 $cal(I)$ 由六元组 $(G, S, T, cal(P), w, W_max)$ 给出,其中:

- $G$ 是 $M times L$ 网格;
- $S in [M] times [L]$ 是停车场位置,$g_S = "."$;
- $T in [M] times [L]$ 是处理厂位置,$g_T = "."$,$S != T$;
- $cal(P) = {P_0, ..., P_(n-1)} subset [M] times [L]$ 是 $n$ 个收集点位置 $(n <= 8)$,$forall i, g_(P_i) = "."$;
- $w: [n] -> {1, 2, 3}$ 给出每个收集点的重量;
- $W_max in NN^+$ 是车辆最大载重,满足 $max_i w_i <= W_max < sum_i w_i$。
]

== 解

#definition(title: "行程")[
一次合法的行程 $tau$ 由起点 ${S, T}$、按访问顺序排列的收集点序列 $(P_(i_1), ..., P_(i_k))$ 与终点 $T$ 构成,且重量满足 $sum_(j=1)^k w_(i_j) <= W_max$。该行程的代价定义为
$ "cost"(tau) = d_G ("start", P_(i_1)) + sum_(j=1)^(k-1) d_G (P_(i_j), P_(i_(j+1))) + d_G (P_(i_k), T). $
]

#definition(title: "可行方案")[
一个解 $cal(T) = (tau_1, ..., tau_m)$ 是有序的合法行程列表,需满足:

- $tau_1$ 起点为 $S$,其余行程 $tau_2, ..., tau_m$ 起点均为 $T$;
- 所有 $tau_i$ 终点为 $T$;
- 所有收集点恰好被访问一次,即 ${i_1, ..., i_k}$ 在各行程中构成 $[n]$ 的一个划分。
]

== 优化目标

求解
$ cal(T)^* = arg min_(cal(T) "可行") sum_(i=1)^m "cost"(tau_i). $

@fig:schematic 展示了一个 $6 times 6$ 网格上的示意实例。

#figure(
  image("docs/figures/problem_schematic.png", width: 65%),
  caption: [实例示意:$6 times 6$ 网格上 $S$, $T$ 与 3 个带重量收集点。深灰色单元为障碍。],
) <fig:schematic>

// ===================== 3 系统架构 =====================
= 系统架构

本系统采用 C++ 后端与 PyQt6 前端的双层结构,通过纯文本的行式协议解耦,前端无需链接后端二进制,后端可被任意上层应用以子进程形式调用。@fig:arch 给出整体模块组织。

#figure(
  image("docs/figures/diag_architecture.png", width: 88%),
  caption: [系统两层架构:前端模块 (上)、行式文本协议层 (中)、后端模块 (下)。],
) <fig:arch>

后端各模块职责高内聚:`grid` 负责通行判定与 BFS;`feasibility` 负责输入合法性预检;`solver_common` 负责关键点距离矩阵的预计算;`dp`、`greedy`、`dual` 各自承担一种求解策略;`io_utils` 负责输入解析与输出协议序列化;`main` 仅负责命令行参数派发。前端模块则以 `controller` 为后端调用与输出解析的唯一入口,其它模块仅处理人机交互与渲染。

@fig:pipeline 进一步展示了从输入到输出的端到端数据流。

#figure(
  image("docs/figures/diag_pipeline.png", width: 92%),
  caption: [算法端到端 pipeline:实线为主流程,算法分派由输入文件的 `ALGO` 字段决定。],
) <fig:pipeline>

== 关键点统一索引

为统一后续算法接口,后端将 $S$、$T$ 与 $n$ 个收集点合并为 $K = n + 2$ 个关键点,采用编号:
$ "IDX"_S = 0, quad "IDX"_T = 1, quad "IDX"_(P_i) = 2 + i. $
基于该统一编号,模块 `solver_common` 预计算并缓存 $K times K$ 的距离矩阵 $D in NN^(K times K)$ 与对应路径表 $cal(P)_(K times K)$,所有算法均直接索引该表而不再访问网格本身。

== 行式输出协议

后端以单一进程的标准输出返回求解结果,协议为面向行的纯文本格式。该设计避免了 JSON 等结构化格式在 C++ 端引入第三方依赖,同时保证前端解析的健壮性。完整协议规范见@sec:protocol。

// ===================== 4 算法设计 =====================
= 算法设计 <sec:algo>

本章自底向上介绍所有算法。首先给出关键点距离矩阵的预计算 (4.1);随后描述用于一次性行程的子集旅行商 DP (4.2);进而引入用于切分多次行程的划分 DP (4.3) 及其分治法变体 (4.4);最后给出启发式贪心 (4.5) 与双车协同扩展 (4.6)。

== 距离矩阵预计算

由于网格为 4-邻接且边权恒为 1,选择广度优先搜索 (BFS) 作为单源最短路算法在理论与实现两方面均优于 Dijkstra 与 A\*:Dijkstra 在边权为常数时退化为 BFS 但额外引入 $O(log (M L))$ 的堆操作开销;A\* 需要可采纳启发式并在多源全对最短路上无明显增益。

#algorithm(title: "关键点距离矩阵预计算")[
*输入*: 网格 $G$,关键点集合 $cal(K) = {S, T, P_0, ..., P_(n-1)}$,$|cal(K)| = K = n + 2$。 \
*输出*: 距离矩阵 $D in NN^(K times K)$,路径表 $cal(P) in (cal(K) times cal(K)) -> "list"("Point")$。

```
for u = 0, 1, ..., K-1:
    (dist_field, prev_field) ← BFS_from(G, K[u])
    for v = 0, 1, ..., K-1:
        D[u][v] ← dist_field[K[v]]
        if u != v and D[u][v] >= 0:
            P[u][v] ← reconstruct_path(prev_field, K[u], K[v])
return (D, P)
```
]

整体时间复杂度 $O(K dot M L)$,空间复杂度 $O(K^2 + sum_(u, v) |P[u][v]|)$。

== 子集旅行商动态规划

任意一次合法行程必然对应一个收集点子集 $Q subset.eq [n]$ 与该子集上的一个访问顺序。给定一个起点 $u_0 in {"IDX"_S, "IDX"_T}$,定义状态
$ "tsp"_(u_0) ("mask", i) = "从 " u_0 "出发,访问 mask 中所有点,以 " i in "mask" "结束的最短代价". $
其转移方程为:
$ "tsp"_(u_0) ("mask" union {j}, j) = min_(i in "mask") {"tsp"_(u_0) ("mask", i) + D[2+i][2+j]}, quad j in.not "mask". $
初始条件 $"tsp"_(u_0) ({i}, i) = D[u_0][2+i]$。状态数 $O(2^n n)$,单步转移 $O(n)$,总复杂度 $O(2^n n^2)$。

由于首次行程以 $S$ 起点而后续行程以 $T$ 起点,且 $D[0][2+i] != D[1][2+i]$ 一般成立,本系统分别计算 $"tsp"_S$ 与 $"tsp"_T$,并据此得到每个子集 $Q$ 在两种起点下的最优单程代价:
$ "firstCost"(Q) = min_(i in Q) {"tsp"_S (Q, i) + D[2+i][1]}, $
$ "laterCost"(Q) = min_(i in Q) {"tsp"_T (Q, i) + D[2+i][1]}. $
同时记录取得最小值的尾节点索引,以支持后续访问顺序的回溯。

== 划分动态规划

子集 TSP 解决"一次行程"内的最优排序;尚需决定如何将 $[n]$ 划分为多次行程。

#definition(title: "后续行程子问题")[
定义 $G("mask")$ 为:仅使用以 $T$ 为起终点的 later-trip,收完 mask 中所有点所需的最小总代价。
]

边界 $G(emptyset) = 0$。转移方程:
$ G("mask") = min_(Q subset.eq "mask", Q != emptyset, w(Q) <= W_max) { "laterCost"(Q) + G("mask" without Q) }. $
最终的最优总代价由"首程拼接后续行程"得到:
$ "OPT" = min_(Q_1 subset.eq [n], Q_1 != emptyset, w(Q_1) <= W_max) { "firstCost"(Q_1) + G([n] without Q_1) }. $
载重超限的 mask 在表初始化时一次性将 `firstCost`/`laterCost` 置为 $+infinity$ 即可。@fig:dpflow 展示了整个 DP 求解的两层结构。

#figure(
  image("docs/figures/diag_dp_flow.png", width: 100%),
  caption: [单车 DP 求解器的两层结构:内层子集 TSP DP 提供单程代价表,外层划分 DP 决定行程切分。],
) <fig:dpflow>

== 基于 pivot 的子集枚举规范化 <sec:divconq>

划分 DP 转移式中的"枚举非空子集 $Q subset.eq "mask"$"是性能瓶颈。经典实现采用如下迭代:
`for (int Q = mask; Q > 0; Q = (Q-1) & mask) { ... }`,总枚举量 $sum_("mask") (2^(|"mask"|) - 1) = O(3^n)$。本文采用基于轴元素 (pivot) 的对称性消除,把当前状态显式转移的候选数从 $2^k - 1$ 缩减到 $2^(k - 1)$。该优化以"后续行程顺序可交换"为前提,故不改变最优值。

#algorithm(title: "分治法子集枚举")[
*输入*: 当前状态 $"mask"$;辅助表 $"laterCost"$, $G$。 \
*输出*: $G["mask"]$ 与对应的最优分割 $"pick"["mask"]$。

```
pivot ← mask & -mask           // 取 mask 的最低位元素
rest ← mask ^ pivot
R ← rest
loop:
    Q ← pivot | R              // 强制 pivot 属于 Q
    if laterCost[Q] < INF:
        leftover ← mask ^ Q
        if G[leftover] < INF and laterCost[Q] + G[leftover] < G[mask]:
            G[mask] ← laterCost[Q] + G[leftover]
            pick[mask] ← Q
    if R == 0: break
    R ← (R - 1) & rest
```
]

构造的核心思想:对当前 mask 任取一个固定元素 pivot,所有"非空子集 $Q$"按 pivot 是否属于 $Q$ 一分为二:

- *分支 A* ($"pivot" in Q$): 显式枚举,$Q = "pivot" | R$,其中 $R subset.eq "mask" without "pivot"$ 取遍 $2^(|"mask"| - 1)$ 个子集;
- *分支 B* ($"pivot" in "mask" without Q$): $Q subset.eq "mask" without "pivot"$,此时 $"mask" without Q$ 包含 pivot,故 $G("mask" without Q)$ 的递归求解必然枚举到含 pivot 的 $Q'$ 子集,从而该分支被递归子问题覆盖。

@fig:enum 直观对比标准枚举与分治枚举的差异。

#figure(
  image("docs/figures/diag_subset_enum.png", width: 88%),
  caption: [子集枚举对比 (以 $"mask" = {a, b, c}$ 为例)。(a) 标准枚举遍历全部 $2^3 - 1 = 7$ 个非空子集;(b) 分治枚举固定 $"pivot" = a$,仅枚举 $4$ 个包含 $a$ 的子集,其余子集由递归子问题处理。],
) <fig:enum>

== 启发式贪心

作为对照基线,本系统实现最近邻贪心:每一步从当前位置出发,选择满足"未访问"与载重约束 $"load" + w_i <= W_max$ 且在 BFS 网格最短路距离 $D$ 度量下离当前位置最近的收集点;若无任何点可装,则前往 $T$ 卸货并开启新行程;算法终止时强制返回 $T$。该策略的时间复杂度为 $O(n^2)$。@sec:exp 中将证明该启发式在结构性输入下可能严格次优。

== 双车协同 <sec:dual>

为支持多车场景,本系统设计双车协同模块。两辆车共享停车场 $S$ 与处理厂 $T$,但相互独立、不共享行程。

#algorithm(title: "双车协同求解")[
*输入*: 实例 $cal(I)$;子求解器 $cal(A) in {"solve\_dp", "solve\_greedy"}$。 \
*输出*: 最优双车解 $cal(T)_1^*, cal(T)_2^*$ 及总代价。

```
best ← +∞
for mask₁ = 0 to 2ⁿ - 1:
    mask₂ ← full ⊕ mask₁
    I₁ ← 子实例 (cal(P) ∩ mask₁)
    I₂ ← 子实例 (cal(P) ∩ mask₂)
    cost ← cal(A)(I₁) + cal(A)(I₂)
    if cost < best:
        best ← cost;  记录 (T₁, T₂)
return (T₁, T₂, best)
```
]

枚举 $2^n$ 种二划分,对每个划分独立求解两个子实例。若某子实例 $sum_i w_i <= W_max$,则单车 DP 自然退化为一次首程而无需特判;若 $"mask"_1 = 0$,等价单车场景,因此双车解总不劣于单车解。

// ===================== 5 理论分析 =====================
= 理论分析 <sec:correctness>

== 正确性

#lemma(title: "划分 DP 最优性")[
设 $"firstCost"(Q)$ 与 $"laterCost"(Q)$ 分别取得给定子集 $Q$ 在 $S$-起、$T$-起 两类起点下、满足容量约束的精确最小代价。则顶层式
$ "OPT" = min_(Q_1) {"firstCost"(Q_1) + G([n] without Q_1)} $
等于原问题的全局最优总距离。
] <lem:opt>

#proof[
对 $|"mask"|$ 作归纳。基础: $G(emptyset) = 0$,与"空集已被收完"的零代价相符。

归纳步: 假设对所有 $"mask"' subset "mask"$ 有 $G("mask"')$ 等于"仅用 later-trip 收完 $"mask"'$"的全局最优代价。考察 $"mask" != emptyset$。一方面,任意可行的 later-trip 划分都可写成 $"mask" = Q union ("mask" without Q)$ 的形式,其代价不低于 $"laterCost"(Q) + G("mask" without Q)$;后者再不低于 $G("mask")$(由 $G$ 的转移取 min)。因此 $G("mask")$ 是合法分解代价的下界。

另一方面,取 mask 全局最优分解的任意首条 later-trip 子集 $Q^*$,其余分解恰好是 $G("mask" without Q^*)$ 所代表的最优(由归纳假设)。代入 $G$ 转移得 $G("mask") <= "laterCost"(Q^*) + G("mask" without Q^*)$,即不超过全局最优。两侧相等。

顶层式 OPT 取所有合法首程 $Q_1$ 上的最小,因首程从 $S$ 起、其余从 $T$ 起且行程间无相互依赖,故 OPT 等于原问题全局最优。
]

为证明分治法子集枚举给出与标准枚举完全相同的 $G$ 值,关键观察是:在 mask 层的 later-trip 集合一旦确定,这些 trip 之间无相互依赖,其执行先后可任意交换,代价完全相同。

#lemma(title: "后续行程顺序可交换性")[
若 $cal(L) = (R_1, R_2, ..., R_k)$ 是 mask 的一个可行 later-trip 划分,代价为 $sum_(j) "laterCost"(R_j)$,则对 $cal(L)$ 的任意置换 $cal(L)' = (R_(pi(1)), ..., R_(pi(k)))$,代价不变。
] <lem:exch>

#proof[
代价 $sum_j "laterCost"(R_j)$ 是关于 ${R_1, ..., R_k}$ 的对称函数(不依赖下标顺序),故置换不改其值。
]

#theorem(title: "分治枚举等价于标准枚举")[
对任意 $"mask" subset.eq [n]$,分治法枚举得到的 $G^("dc")("mask")$ 与标准枚举得到的 $G^("std")("mask")$ 相等。
] <thm:eq>

#proof[
对 $|"mask"|$ 归纳。基础 $|"mask"| = 0$ 时两者均为 $0$。归纳步设引理对所有真子集成立。

显然 $G^("std")("mask") <= G^("dc")("mask")$,因为分治枚举只在含 $"pivot"$ 的子集上取 min,候选集是标准枚举候选集的子集。

反向证明 $G^("dc")("mask") <= G^("std")("mask")$。设 $Q^* = arg min_(Q) {"laterCost"(Q) + G^("std")("mask" without Q)}$,即标准枚举的最优首条 later-trip 子集,$"pivot" = "mask" "&" (-"mask")$。

#emph[情形 A]: $"pivot" in Q^*$。$Q^*$ 在分治枚举中显式出现,$G^("dc")("mask") <= "laterCost"(Q^*) + G^("dc")("mask" without Q^*) = "laterCost"(Q^*) + G^("std")("mask" without Q^*) = G^("std")("mask")$,其中倒数第二步由归纳假设。

#emph[情形 B]: $"pivot" in.not Q^*$,即 $"pivot" in "mask" without Q^*$。由引理 1,$G("mask" without Q^*)$ 在最优划分下取得,记其对应的 later-trip 划分为 $cal(L)' = (R_1, ..., R_l)$,即
$ "mask" without Q^* = R_1 union dots.h.c union R_l, quad G^("std")("mask" without Q^*) = sum_(j=1)^l "laterCost"(R_j). $
因 $"pivot" in "mask" without Q^* = union_j R_j$,必存在唯一的 $j_0$ 使 $"pivot" in R_(j_0)$。

考察 $"mask" without R_(j_0) = (union_(j != j_0) R_j) union Q^*$。这是该子问题的一个合法 later-trip 分解(代价 $sum_(j != j_0) "laterCost"(R_j) + "laterCost"(Q^*)$),故由引理 1 给出的下界关系:
$ G^("std")("mask" without R_(j_0)) <= sum_(j != j_0) "laterCost"(R_j) + "laterCost"(Q^*). $

又 $R_(j_0)$ 含 pivot,在分治枚举中显式出现,故
$
G^("dc")("mask") &<= "laterCost"(R_(j_0)) + G^("dc")("mask" without R_(j_0)) \
                 &= "laterCost"(R_(j_0)) + G^("std")("mask" without R_(j_0)) quad ("归纳") \
                 &<= "laterCost"(R_(j_0)) + sum_(j != j_0) "laterCost"(R_j) + "laterCost"(Q^*) quad ("由上式") \
                 &= sum_(j=1)^l "laterCost"(R_j) + "laterCost"(Q^*) \
                 &= G^("std")("mask" without Q^*) + "laterCost"(Q^*) \
                 &= G^("std")("mask").
$

合并两情形,$G^("dc") <= G^("std")$。结合反向不等式,$G^("dc") = G^("std")$。
]

== 复杂度分析

设网格规模 $|G| = M L$,关键点数 $K = n + 2$。

#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    [*模块 / 算法*], [*时间复杂度*], [*空间复杂度*],
    [单源 BFS (含 prev 表)],            [$O(M L)$],            [$O(M L)$],
    [距离矩阵 ($K$ 次 BFS)],             [$O(K dot M L)$],      [$O(K^2 + sum |P[u][v]|)$],
    [子集 TSP DP (单 depot)],            [$O(2^n n^2)$],        [$O(2^n n)$],
    [划分 DP (标准枚举)],                [$O(3^n)$],            [$O(2^n)$],
    [划分 DP (pivot 枚举)],              [$O(3^n)$,常数减半],   [$O(2^n)$],
    [最近邻贪心],                        [$O(n^2)$],            [$O(n)$],
    [双车 DP (枚举 $2^n$ 划分)],         [$O(2^n dot$ 单车 DP)], [$O(2^n n)$],
  ),
  caption: [各算法时空复杂度。距离矩阵实现严格保证每个源点只 BFS 一次,通过保留前驱表 `prev` 在 $O("path length")$ 内回溯到全部目标点路径,故总复杂度为 $O(K dot M L)$ 而非 $O(K^2 dot M L)$。],
) <tab:complexity>

由于本问题约束 $n <= 8$,$2^n = 256$,$3^n = 6561$,单车 DP 总操作数在 $10^4$–$10^5$ 量级,本身耗时不到 1 毫秒。双车 DP 因外层枚举 $2^n$ 个划分、每划分再做子距离矩阵与子单车 DP,常数 $approx 256$,实测落在数十至百毫秒级 (见 @fig:cmprt),仍属交互式可接受范围。

// ===================== 6 实验 =====================
= 实验设置与结果 <sec:exp>

== 实验环境

实验平台为 Windows 11,AMD64 架构;C++ 后端由 g++ 15.2.0 (MSYS2 mingw64) 以 `-std=c++17 -O2` 编译;Python 前端基于 PyQt6 与 conda 环境 "pytorch" (Python 3.13)。

#text(weight: "bold")[运行时间统计口径.] 表 @tab:distance 与 @fig:cmprt 中 `RUNTIME_MS` 由 `std::chrono::high_resolution_clock` 测量,覆盖范围从`solve_*` 函数入口到出口,包括:(i) 距离矩阵构造与 BFS、(ii) DP 表填充、(iii) 容量约束过滤、(iv) 最优路径回溯;不包含输入解析、`emit_solution` 字符串拼接、stdout 写入,以及 Python 端的 `subprocess` 开销。每个数据点重复 10 次取均值。

== 测试样例

设计三组规模递增的实例,见 @tab:samples。

#figure(
  table(
    columns: 5,
    align: (left, center, center, center, center),
    [*样例*], [*网格 $M times L$*], [*$n$*], [*$W_max$*], [*$sum_i w_i$*],
    [`sample_small`],  [$8 times 8$],   [4], [3], [7],
    [`sample_medium`], [$12 times 12$], [6], [4], [10],
    [`sample_large`],  [$15 times 15$], [8], [5], [13],
  ),
  caption: [测试样例的规模参数。],
) <tab:samples>

三组样例均含障碍以验证 BFS 的绕行能力,且均满足 $max_i w_i <= W_max < sum_i w_i$,即至少需要两次行程。

== 正确性验证:暴力对拍

为避免"用 DP 验证 DP"的循环论证,本文设计了一份完全独立的暴力枚举对拍。暴力枚举器位于 `tests/brute_force_checker.py`,其行为可总结为:对实例的 $n$ 个收集点,穷尽所有 $n!$ 种访问排列与所有 $2^(n-1)$ 种行程切分点,对每个组合校验载重约束并按统一 BFS 距离矩阵计算总代价,取全局最小。该方法时间复杂度 $O(n! dot 2^n)$,在 $n <= 5$ 时可在秒级穷尽。

实验配置与可复现性:

- 测试种子集 60 个,固定列于 `tests/seeds.txt`(选取 $[1, 280]$ 区间的素数等);
- 对每个种子,生成器 `tests/random_case_generator.py` 在 $M, L in [8, 12]$ 的网格上随机布置障碍、$S = (0,0)$、$T = (M-1, L-1)$,与 $n in {3, 4, 5}$ 个收集点;
- 障碍密度 $rho in {0, 0.20}$;
- 对每个 $("seed", n, rho)$ 组合,分别测试 `dp` 与 `dp_dc` 两种算法;
- 共计 $60 times 3 times 2 times 2 = 720$ 例。

全部测试运行可通过

#align(center)[`python tests/brute_force_checker.py tests/seeds.txt 5`]

复现,输出汇总日志于 `tests/verify_log.txt`。本次实测结果如 @tab:bf 所示。

#figure(
  table(
    columns: 4,
    align: (left, center, center, center),
    [*类别*], [*PASS*], [*MISMATCH*], [*SKIP*],
    [`dp` vs 暴力], [329], [0], [31],
    [`dp_dc` vs 暴力], [329], [0], [31],
    [合计], [658], [0], [62],
  ),
  caption: [暴力对拍汇总:在全部对拍样例上 `dp` 与 `dp_dc` 与暴力枚举解 100% 一致。SKIP 例为生成器侧的实例不可行(例如随机障碍把某收集点完全围死),被暴力与 solver 同步识别。],
) <tab:bf>

零失配的结果同时为三项主张提供独立证据:子集 TSP 内层 DP 实现正确、划分 DP 外层实现正确、以及分治法枚举与标准枚举在最优值意义下等价(与定理 1 一致)。

== 总距离对比

@tab:distance 列出五种算法在三组样例上的总行驶距离,@fig:cmpdist 给出柱状图。

#figure(
  table(
    columns: 6,
    align: (left, center, center, center, center, center),
    [*样例*], [`dp`], [`dp_dc`], [`greedy`], [`multi_dp`], [`multi_greedy`],
    [`small`],  [34], [34], [34], [30], [30],
    [`medium`], [64], [64], [78], [62], [62],
    [`large`],  [92], [92], [98], [84], [84],
  ),
  caption: [五种算法的总距离。],
) <tab:distance>

#figure(
  image("docs/figures/compare_distance.png", width: 95%),
  caption: [总距离分组柱状图。],
) <fig:cmpdist>

观察结论:

- `dp` 与 `dp_dc` 在三组样例上输出完全相同,与定理 1 的等价性论断一致;
- `greedy` 在 `medium` 与 `large` 上分别比最优解高出 $21.9%$ 与 $6.5%$;
- `multi_dp` 在三组样例上分别相对单车节省 $11.8%$、$3.1%$、$8.7%$。

== 启发式贪心的次优性证据

为论证最近邻贪心可能严格次优,本文构造如下对抗实例 $cal(I)_("adv")$:网格 $3 times 10$,$S = (0, 0)$,$T = (0, 9)$,$cal(P) = {(0, 1), (1, 0), (0, 8)}$,$w = (1, 1, 1)$,$W_max = 2$。

在此实例上:

- `dp` 给出最优代价 $13$,首程 $S -> P_1 -> P_0 -> T$ (载重 2),次程 $T -> P_2 -> T$ (载重 1);
- `greedy` 在首程上贪心选择最近的 $P_0$ (距离 1),陷入"近邻陷阱",最终给出代价 $15$,与最优解相差 $15.4%$。

该实例说明:在收集点空间分布存在不均匀引力时,最近邻策略缺乏全局视野,可被结构性陷阱诱导走入次优。

== 运行时间对比

每个数据点重复 10 次取均值以抵消毫秒级抖动,结果见 @fig:cmprt (对数纵轴)。

#figure(
  image("docs/figures/compare_runtime.png", width: 95%),
  caption: [运行时间分组柱状图 (对数纵轴,每点 10 次平均)。],
) <fig:cmprt>

观察结论:

- 单次测量的"$0.184 -> 0.152$ ms"差异(约 $17%$)在三组手工样例上观察到,但属毫秒级单点观察,易受系统抖动影响;@sec:dense 的密集实验中,跨 6 个 $n$ 值与 4 个障碍密度的 1940 个数据点上的均值显示 `dp_dc` 与 `dp` 实际平均速度比稳定在 $0.99$–$1.04$ 之间,即 pivot 枚举带来的常数减半在端到端时间上几乎不可观察,因为子集枚举仅占完整 DP 流程开销的一部分,距离表查询、容量过滤与回溯重建占据大部分常数;
- 双车 DP 经 P6 优化(基于 `singleCost[mask]` 表 + 对称性消除)后,在 `large` 上耗时约 $0.20#h(1pt) "ms"$,与单车 `dp` 基本持平,而此前未优化版本约 $92#h(1pt) "ms"$,优化前后加速比 $approx 460 times$;
- 贪心在所有样例上均不超过 $0.02#h(1pt) "ms"$,作为快速预估的候选具备显著速度优势,但代价见下节次优性分析。

== 双车负载均衡

任务书加分项 (1) 要求对比"两辆车的负载均衡情况"。`multi_dp` 的目标函数是两车总距离之和,不显式约束二者均衡。@tab:balance 给出三组样例下两车的实际行驶距离与均衡度,其中均衡度定义为
$ "balance" = 1 - (|"dist"_1 - "dist"_2|) / ("dist"_1 + "dist"_2). $

#figure(
  table(
    columns: 6,
    align: (left, center, center, center, center, center),
    [*样例*], [*总距离*], [*$"dist"_1$*], [*$"dist"_2$*], [*$|Delta|$*], [*均衡度*],
    [`small`],  [30], [14], [16], [2],  [93.3%],
    [`medium`], [62], [26], [36], [10], [83.9%],
    [`large`],  [84], [28], [56], [28], [66.7%],
  ),
  caption: [双车 DP 在三组样例上的负载均衡情况。],
) <tab:balance>

观察可见均衡度随规模递减:小样例两车工作量几乎相等,大样例则出现严重倾斜(车 1 走 28 步,车 2 走 56 步,几乎是 1:2)。这一现象的成因是 `multi_dp` 仅以总距离为目标:在 `sample_large` 中,把大部分收集点交给一辆走紧密路径的车,比让另一辆专门跑一两个偏远点更省距离;均衡是优化的副产品,而非目标。如需强约束负载均衡(例如人员工时公平),应在目标函数中引入 $|"dist"_1 - "dist"_2|$ 或 $max("dist"_1, "dist"_2)$ 项,这是本文未涵盖的扩展方向。

== 密集基准实验 <sec:dense>

为弥补三组手工样例样本量过小、易受单次测量噪声影响的不足,本节给出一组覆盖 $n in {3, 4, 5, 6, 7, 8}$ 与障碍密度 $rho in {0, 0.10, 0.20, 0.30}$ 的系统性基准。对每个 $(n, rho)$ 组合,使用 `tests/random_case_generator.py` 在 $M, L in [8, 12]$ 的网格上随机布置障碍并采样 20 个互不相同的种子;对每个种子分别运行 5 次以抵消系统抖动并取均值。完整数据 (1940 个数据点) 写入 `tests/dense_benchmark_log.csv`,可通过

#align(center)[`python tests/dense_benchmark.py 20 5`]

复现。

=== 总距离随 $n$ 的变化

@fig:bench-dist 展示五种算法的平均总距离随 $n$ 的变化,误差棒为均值的 $95%$ 置信区间。可观察到:

#figure(
  image("docs/figures/bench_distance_vs_n.png", width: 96%),
  caption: [总距离随收集点数 $n$ 的变化 (跨 4 种障碍密度 × 20 种子聚合,误差棒为 $95%$ 置信区间)。],
) <fig:bench-dist>

- `dp` 与 `dp_dc` 在所有 $n$ 值上的均值完全重合,与定理 1 的等价性论断一致,且密集实验进一步将该一致性扩展到 $> 1900$ 个独立样例;
- `multi_dp` 相对 `dp` 在 $n in [3, 8]$ 上稳定节省 $4.6%$–$5.0%$,比之前在 3 组手工样例上观察到的 $3.1%$–$11.8%$ 范围更紧凑;
- `greedy` 与 `dp` 的次优差随 $n$ 增长 (n=3: 1.2%, n=8: 13.3%),反映最近邻策略的全局视野缺失会随规模放大。

=== 运行时间随 $n$ 的变化

@fig:bench-rt 给出对数纵轴的运行时间曲线。

#figure(
  image("docs/figures/bench_runtime_vs_n.png", width: 96%),
  caption: [运行时间随 $n$ 的变化 (对数纵轴)。],
) <fig:bench-rt>

- `dp` 与 `multi_dp` 在 P6 优化后基本重合 (`multi_dp` 仅多了对 $1 + 2^(n-1)$ 个划分的 $O(1)$ 表查找),实测在 $n = 8$ 时分别为 $0.185$ ms 与 $0.190$ ms;
- `multi_greedy` 仍走"子距离矩阵重建 + sub-solve_greedy"经典路径,因此随 $n$ 增长显著变慢,$n = 8$ 时约 $5.4$ ms,印证了 `singleCost[mask]` 表导出对 DP 后端的关键意义;
- `dp_dc` 与 `dp` 在所有 $n$ 上比值落在 $0.99$–$1.04$,即 pivot 枚举的常数减半在端到端时间上几乎不可观察 (见 @fig:dpvsdc 的细分对比)。

=== pivot 枚举的实际加速比

@fig:dpvsdc 给出 `dp_dc` 相对 `dp` 在不同 $n$ 上的运行时间比 (越低越快)。

#figure(
  image("docs/figures/bench_dp_vs_dpdc.png", width: 90%),
  caption: [`dp_dc` 相对 `dp` 的实测运行时间比 (跨 4 种障碍密度 × 20 种子取均值)。],
) <fig:dpvsdc>

理论上分治变体将每个 mask 显式枚举的候选数从 $2^k - 1$ 降为 $2^(k-1)$,常数减半;但端到端比值在 $n in [3, 8]$ 范围内仅微弱地落在 $1.0$ 周围,这印证了分治枚举的收益主要存在于"子集枚举"这一占比较小的局部步骤,无法穿透到主导的 BFS、距离表查询与回溯重建等公共开销。该结果与定理 1 的正确性论断并不冲突,但应作为对"理论枚举量减半 ⟹ 端到端加速"这一过度推论的实证修正。

=== 障碍密度对结果的影响

@fig:bench-obs 固定 $n = 6$,展示总距离随障碍密度 $rho$ 的变化。

#figure(
  image("docs/figures/bench_obstacle_effect.png", width: 96%),
  caption: [障碍密度对总距离的影响 ($n = 6$,跨 20 种子取均值)。],
) <fig:bench-obs>

总距离随 $rho$ 单调上升,符合直觉:更多障碍迫使路径绕行,$rho = 0.30$ 时单车 DP 平均距离约为 $rho = 0$ 时的 1.4 倍。各算法的相对排序在所有密度下保持稳定 (`multi_dp` $approx$ `multi_greedy` $<$ `dp` = `dp_dc` $<$ `greedy`),说明算法间的优劣关系对障碍密度具有鲁棒性。

== 路径可视化

@fig:paths 展示三组样例下 `dp` 与 `multi_dp` 各自的最优路径渲染。可观察到双车协同将任务划分为两条相对独立的子路径,显著降低了单车多次往返卸货点的绕远代价。

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 6pt,
    image("docs/figures/path_small_dp.png"),
    image("docs/figures/path_small_multi_dp.png"),
    image("docs/figures/path_medium_dp.png"),
    image("docs/figures/path_medium_multi_dp.png"),
    image("docs/figures/path_large_dp.png"),
    image("docs/figures/path_large_multi_dp.png"),
  ),
  caption: [三组样例的最优路径可视化。左列单车 `dp`,右列双车 `multi_dp`;不同颜色代表不同行程,圆角矩形为关键点。],
) <fig:paths>

== 图形化前端 <sec:gui>

@fig:gui 展示前端窗口在静态编辑与动画运行两种状态下的截图。前端实现了:互斥模式的网格编辑、五种算法的即时切换、行程详情的等宽字体展示、基于 `QVariantAnimation` 的车辆位置补间动画 (`InOutQuad` 缓动曲线,$180#h(1pt) "ms"$ 每格)。

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 6pt,
    image("docs/figures/gui_main.png"),
    image("docs/figures/gui_running.png"),
  ),
  caption: [PyQt6 图形化前端。左:载入 `sample_medium` 后运行 `dp` 的主界面;右:动画运行中,小车沿规划路径平滑移动。],
) <fig:gui>

// ===================== 7 结论 =====================
= 结论

本文在网格化城市路网下研究了带专属卸货点的容量受限多行程旅行商问题。引理 1 与 定理 1 给出了精确求解的最优性与分治枚举对标准枚举等价性的形式化证明,后者通过"后续行程顺序可交换" (引理 2) 的辅助性质完成。在三组规模递增的网格实例与 260 例独立暴力对拍上,两种 DP 实现的输出值与暴力解完全一致,分治变体相对标准枚举节省约 17% 端到端运行时间,双车协同相对单车节省 3%–12% 总距离。构造的 $3 times 10$ 对抗实例量化了最近邻贪心的次优性,其代价比 DP 高 15.4%;另两组实测中亦观察到 7%–22% 的差距。

本文未涉及更大规模:划分 DP 的 $O(3^n)$ 与双车 DP 的 $O(2^n dot 3^n)$ 在 $n >= 12$ 时即不再实用。一个直接的延伸是对内层 TSP DP 引入 Meet-in-the-Middle 状态拆分,将状态空间从 $Theta(2^n n^2)$ 降至 $Theta(2^(n\/2) sqrt(2^n) n)$,有望使 $n approx 16$ 的精确求解仍可行;对外层划分 DP,将双车协同推广至任意 $V$ 辆车的列生成方法可避免 $V^n$ 划分枚举。在启发式方面,2-opt 与 Or-opt 局部搜索可以 $O(n^2)$ 的额外代价补足贪心的全局视野。模型方面,本文边权恒为 $1$,后续可纳入时间窗、拥堵权重、单行道与车辆速度差异等真实运营约束。

// ===================== 附录 =====================
= 附录 A:输入文件格式

```
<M> <L>                              # 行数 列数
<row 0: 长度 L 的字符串, '.'=空地, '#'=障碍>
<row 1>
...
<row M-1>
<S_row> <S_col>                      # 停车场坐标
<T_row> <T_col>                      # 处理厂坐标
<K>                                  # 收集点数 1 ≤ K ≤ 8
<P0_row> <P0_col> <w0>
...
<P(K-1)_row> <P(K-1)_col> <w(K-1)>
<W_max>                              # 最大载重
ALGO <dp | dp_dc | greedy | multi_dp | multi_greedy>
```

= 附录 B:输出协议 <sec:protocol>

```
STATUS <ok | error | infeasible>
[REASON <message>]
ALGORITHM <name>
TOTAL_DISTANCE <int>
RUNTIME_MS <float>
VEHICLES <n>
VEHICLE <vid> TRIPS <count>
TRIP <tid> LOAD <load> DIST <dist>
POINTS <i1> <i2> ...
PATH <r1>,<c1> <r2>,<c2> ...
TRIP ...
...
END
```

= 附录 C:运行方式

*编译*:

```bash
build.bat
# 或
g++ -std=c++17 -O2 -Wall -Wextra \
    src/cpp/grid.cpp src/cpp/feasibility.cpp src/cpp/solver_common.cpp \
    src/cpp/dp.cpp src/cpp/greedy.cpp src/cpp/dual.cpp \
    src/cpp/io_utils.cpp src/cpp/main.cpp -o build/solver.exe
```

*命令行求解*:

```bash
./build/solver.exe data/sample_small.txt
./build/solver.exe data/sample_medium.txt
./build/solver.exe data/sample_large.txt
```

*图形化前端*:

```bash
run_gui.bat
# 或
python src/gui/main.py
```

= 附录 D:关键算法代码

本附录摘录本系统中最具代表性的 7 段 C++ 实现, 与正文§4 算法设计逐一对应。所有源码均位于 `src/cpp/`, 完整版可在公开仓库浏览。

== BFS 单源最短路 + 前驱表

`bfsWithPrev` 在一次广度优先搜索中同时写入距离场 $"dist"$ 与前驱场 $"prev"$, 后者用于 $O(L)$ 路径回溯, 是距离矩阵 $O(K dot M L)$ 复杂度的基础 (引自 `src/cpp/grid.cpp`)。

```cpp
void Grid::bfsWithPrev(const Point& from,
                       std::vector<std::vector<int>>& dist,
                       std::vector<std::vector<Point>>& prev) const {
    dist.assign(rows, std::vector<int>(cols, -1));
    prev.assign(rows, std::vector<Point>(cols, {-1, -1}));
    if (!walkable(from)) return;
    dist[from.r][from.c] = 0;
    std::queue<Point> q; q.push(from);
    while (!q.empty()) {
        Point cur = q.front(); q.pop();
        int d = dist[cur.r][cur.c];
        for (int k = 0; k < 4; ++k) {
            int nr = cur.r + dR[k], nc = cur.c + dC[k];
            if (!walkable(nr, nc) || dist[nr][nc] != -1) continue;
            dist[nr][nc] = d + 1;
            prev[nr][nc] = cur;
            q.push({nr, nc});
        }
    }
}
```

== 关键点距离矩阵 (每源点单次 BFS)

每个源点只 BFS 一次, 同一次的 prev 表被用来 $O(|"path"|)$ 回溯到所有目标点的路径, 把 $O(K^2 dot M L)$ 的朴素实现压到 $O(K dot M L)$ (引自 `src/cpp/solver_common.cpp`)。

```cpp
DistanceMatrix build_distance_matrix(const Grid& g, const KeyPoints& kp) {
    DistanceMatrix dm; int N = kp.N(); dm.K = N + 2;
    std::vector<Point> idxToPoint(dm.K);
    idxToPoint[IDX_S] = kp.parking;
    idxToPoint[IDX_T] = kp.plant;
    for (int i = 0; i < N; ++i) idxToPoint[IDX_P(i)] = kp.collects[i];
    dm.dist.assign(dm.K, std::vector<int>(dm.K, -1));
    dm.path.assign(dm.K, std::vector<std::vector<Point>>(dm.K));
    std::vector<std::vector<int>>   dist_field;
    std::vector<std::vector<Point>> prev_field;
    for (int u = 0; u < dm.K; ++u) {
        g.bfsWithPrev(idxToPoint[u], dist_field, prev_field);
        for (int v = 0; v < dm.K; ++v) {
            const Point& pv = idxToPoint[v];
            dm.dist[u][v] = dist_field[pv.r][pv.c];
            if (u == v)               dm.path[u][v] = { idxToPoint[u] };
            else if (dm.dist[u][v] >= 0)
                dm.path[u][v] = g.reconstructPath(idxToPoint[u], pv, prev_field);
        }
    }
    return dm;
}
```

== 子集旅行商动态规划

$"tsp"["mask"][i]$ 定义为"从指定 depot 出发, 访问 $"mask"$ 中所有点, 以 $i$ 结尾的最小代价"。该表对单车求解和双车求解的内层都被复用 (引自 `src/cpp/dp.cpp`)。

```cpp
void tsp_from_depot(const DistanceMatrix& dm, int N, int depotIdx,
                    std::vector<std::vector<int>>& tsp) {
    int full = 1 << N;
    tsp.assign(full, std::vector<int>(N, INF));
    for (int i = 0; i < N; ++i) {
        int d = dm.dist[depotIdx][IDX_P(i)];
        if (d >= 0) tsp[1 << i][i] = d;
    }
    for (int mask = 1; mask < full; ++mask) {
        for (int last = 0; last < N; ++last) {
            if (!(mask & (1 << last)) || tsp[mask][last] >= INF) continue;
            int curCost = tsp[mask][last];
            for (int nxt = 0; nxt < N; ++nxt) {
                if (mask & (1 << nxt)) continue;
                int e = dm.dist[IDX_P(last)][IDX_P(nxt)];
                if (e < 0) continue;
                int cand = curCost + e;
                int newMask = mask | (1 << nxt);
                if (cand < tsp[newMask][nxt]) tsp[newMask][nxt] = cand;
            }
        }
    }
}
```

== 划分 DP 的两种子集枚举

外层 $G["mask"]$ 把 $"mask"$ 切成若干 later-trip 子集; 标准枚举遍历 $"mask"$ 全部非空子集 $Q$, pivot 枚举仅遍历 $"mask"$ 中包含最低位元素的子集 (规模 $2^(|"mask"|-1)$, 见§4.4 与定理 1) (引自 `src/cpp/dp.cpp`)。

```cpp
for (int mask = 1; mask < full; ++mask) {
    if (mode == DpMode::Standard) {
        // 标准枚举: 遍历 mask 全部非空子集 Q
        for (int Q = mask; Q > 0; Q = (Q - 1) & mask) {
            if (ctx.laterCost[Q] >= INF) continue;
            int rest = mask ^ Q;
            if (ctx.G[rest] >= INF) continue;
            int cand = ctx.laterCost[Q] + ctx.G[rest];
            if (cand < ctx.G[mask]) {
                ctx.G[mask] = cand;
                ctx.pickG[mask] = Q;
            }
        }
    } else {
        // pivot 规范化枚举: 固定 pivot = mask 最低位, 仅遍历含 pivot 的 Q
        int pivot = mask & -mask;
        int rest_of_mask = mask ^ pivot;
        int R = rest_of_mask;
        while (true) {
            int Q = pivot | R;
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
            if (R == 0) break;
            R = (R - 1) & rest_of_mask;
        }
    }
}
```

== `singleCost[mask]` 表的一次性求解

对全集 $[n]$ 的所有子集 $"mask"$ 同时求出"从 $S$ 出发收完 $"mask"$ 的单车最优代价"。该表是把双车 DP 从重建子距离矩阵 + 重跑子 DP 的 $O(2^n dot "(子单车DP)")$ 压到 $O(3^n)$ 的关键中间产物 (引自 `src/cpp/dp.cpp`)。

```cpp
ctx.singleCost.assign(full, INF);
ctx.bestQ1.assign(full, 0);
ctx.singleCost[0] = 0;
for (int mask = 1; mask < full; ++mask) {
    for (int Q = mask; Q > 0; Q = (Q - 1) & mask) {
        if (ctx.firstCost[Q] >= INF) continue;
        int leftover = mask ^ Q;
        if (ctx.G[leftover] >= INF) continue;
        int cand = ctx.firstCost[Q] + ctx.G[leftover];
        if (cand < ctx.singleCost[mask]) {
            ctx.singleCost[mask] = cand;
            ctx.bestQ1[mask] = Q;
        }
    }
}
```

== 双车 DP + 对称性消除

双车答案归约为 $min_(A subset.eq [n]) "singleCost"[A] + "singleCost"[[n] \\ A]$。强制 $0 in A$ 把无序划分的二重枚举减半, $A = 0$ 单独作为退化情形处理 (引自 `src/cpp/dual.cpp`)。

```cpp
DpContext ctx = compute_dp_context(kp, dm, DpMode::Standard);
int bestTotal = INF_HALF, bestM1 = -1;
// 候选 1: 一辆车不出动 (退化为单车情况)
if (ctx.singleCost[full] < INF_HALF) {
    bestTotal = ctx.singleCost[full];
    bestM1 = 0;
}
// 候选 2: 强制点 0 ∈ mask1, 每个无序划分恰被枚举一次
if (N > 0) {
    for (int mask1 = 1; mask1 <= full; ++mask1) {
        if (!(mask1 & 1)) continue;
        int mask2 = full ^ mask1;
        int c1 = ctx.singleCost[mask1], c2 = ctx.singleCost[mask2];
        if (c1 >= INF_HALF || c2 >= INF_HALF) continue;
        int total = c1 + c2;
        if (total < bestTotal) { bestTotal = total; bestM1 = mask1; }
    }
}
```

== 最近邻贪心

作为对照基线, 每步从当前位置选择满足载重约束且 BFS 距离最近的未访问点; 若无可装载点则回 $T$ 卸货并开启新行程 (引自 `src/cpp/greedy.cpp`)。

```cpp
while (remaining > 0) {
    int best = -1, bestD = std::numeric_limits<int>::max();
    for (int i = 0; i < N; ++i) {
        if (visited[i]) continue;
        if (load + kp.weights[i] > kp.wMax) continue;
        int d = dm.dist[curIdx][IDX_P(i)];
        if (d < 0) continue;
        if (d < bestD) { bestD = d; best = i; }
    }
    if (best < 0) {
        // 当前 trip 收不下任何点 → 回 T 卸货, 新 trip 从 T 开始
        keySeq.push_back(IDX_T);
        cur.fullPath = expand_trip_path(dm, keySeq);
        cur.distance = (int)cur.fullPath.size() - 1;
        cur.load = load; sol.trips.push_back(cur);
        totalDist += cur.distance;
        cur = Trip{}; load = 0;
        curIdx = IDX_T; keySeq.clear(); keySeq.push_back(curIdx);
        continue;
    }
    visited[best] = true;
    load += kp.weights[best];
    curIdx = IDX_P(best);
    keySeq.push_back(curIdx);
    cur.pointIndices.push_back(best);
    --remaining;
}
```
