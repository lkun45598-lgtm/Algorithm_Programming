"""generate_diagrams.py —— 用 matplotlib 绘制学术风格流程图。
   设计原则: 配色克制 / 圆角阴影 / Bezier 曲线箭头 / 网格对齐 / 字号层次清晰。
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.patheffects import withStroke

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 10

# ===== 设计语言 (Material/Notion 风) =====
BG = "white"
INK = "#1f2937"           # 主文字
INK_MUTED = "#6b7280"     # 次文字
LINE = "#9ca3af"          # 线条

# 节点配色族 (背景 + 边)
PALETTE = {
    "primary":  ("#dbeafe", "#3b82f6"),  # 蓝 — C++ 后端
    "secondary":("#ede9fe", "#8b5cf6"),  # 紫 — Python 前端
    "accent":   ("#dcfce7", "#22c55e"),  # 绿 — 算法
    "warn":     ("#fef3c7", "#f59e0b"),  # 黄 — 数据
    "danger":   ("#fee2e2", "#ef4444"),  # 红
    "neutral":  ("#f3f4f6", "#9ca3af"),  # 灰 — 协议
}


def node(ax, x, y, w, h, label, kind="primary", title=None,
         fontsize=9.5, weight="normal"):
    """画一个圆角矩形节点,带轻阴影。"""
    face, edge = PALETTE[kind]
    # 阴影层
    shadow = FancyBboxPatch(
        (x - w/2 + 0.04, y - h/2 - 0.04), w, h,
        boxstyle="round,pad=0.0,rounding_size=0.14",
        facecolor="#0008", edgecolor="none", alpha=0.10,
    )
    ax.add_patch(shadow)
    # 主体
    box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.0,rounding_size=0.14",
        facecolor=face, edgecolor=edge, linewidth=1.3,
    )
    ax.add_patch(box)
    if title is not None:
        ax.text(x, y + h*0.18, title, ha="center", va="center",
                fontsize=fontsize+0.5, color=INK, fontweight="bold")
        ax.text(x, y - h*0.20, label, ha="center", va="center",
                fontsize=fontsize-0.5, color=INK_MUTED)
    else:
        ax.text(x, y, label, ha="center", va="center",
                fontsize=fontsize, color=INK, fontweight=weight)


def arrow(ax, x1, y1, x2, y2, label=None, curve=0.0,
          color=None, lw=1.4, ls="-", mutation=14):
    if color is None:
        color = "#4b5563"
    ar = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=mutation,
        color=color, linewidth=lw, linestyle=ls,
        connectionstyle=f"arc3,rad={curve}",
        capstyle="round",
    )
    ax.add_patch(ar)
    if label:
        mx, my = (x1 + x2)/2, (y1 + y2)/2
        offset = 0.12 * (1 + abs(curve))
        ax.text(mx, my + offset, label, ha="center", va="center",
                fontsize=8, color=INK_MUTED,
                bbox=dict(facecolor="white", edgecolor="none", pad=2))


def group_frame(ax, x, y, w, h, title, color):
    """画一个虚线分组框 + 左上标签。"""
    frame = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.0,rounding_size=0.10",
        facecolor="none", edgecolor=color, linewidth=0.9,
        linestyle=(0, (5, 4)), alpha=0.7,
    )
    ax.add_patch(frame)
    tag = ax.text(x + 0.2, y + h - 0.05, title,
                  fontsize=9.5, color=color, fontweight="bold",
                  bbox=dict(facecolor="white", edgecolor="none", pad=2))


def caption(ax, text):
    """在图底加副标题"""
    ax.text(0.5, 0.02, text, transform=ax.transAxes,
            ha="center", va="bottom", fontsize=8.5,
            color=INK_MUTED, fontstyle="italic")


# ===================================================================
# 图 1: 系统架构图
# ===================================================================
def fig_architecture(path):
    fig, ax = plt.subplots(figsize=(11.5, 7), dpi=180)
    ax.set_xlim(0, 11.5); ax.set_ylim(0, 7); ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_facecolor(BG)

    # ===== 前端组框 =====
    group_frame(ax, 0.5, 5.0, 10.5, 1.6, "PyQt6 前端  src/gui/", PALETTE["secondary"][1])

    front_nodes = [
        (1.7, 5.7, "main.py",      "主窗口装配"),
        (3.7, 5.7, "map_view.py",  "QGraphicsView"),
        (5.7, 5.7, "editor.py",    "编辑状态"),
        (7.7, 5.7, "animator.py",  "补间动画"),
        (9.8, 5.7, "controller.py","调用 solver.exe"),
    ]
    for (x, y, title, sub) in front_nodes:
        node(ax, x, y, 1.7, 0.95, sub, kind="secondary", title=title, fontsize=9)

    # ===== 协议层 =====
    node(ax, 5.75, 4.0, 9.5, 0.7,
         "行式文本协议:STATUS / ALGORITHM / TOTAL_DISTANCE / TRIPS / PATH / END",
         kind="neutral", fontsize=9.5, weight="bold")

    # ===== 后端组框 =====
    group_frame(ax, 0.5, 0.5, 10.5, 3.0, "C++ 后端  src/cpp/", PALETTE["primary"][1])

    # 后端上排:输入/输出/基础设施
    upper = [
        (1.8, 2.5, "io_utils", "I/O 协议", "primary"),
        (4.0, 2.5, "feasibility", "合法性检查", "primary"),
        (6.2, 2.5, "grid", "BFS 最短路", "primary"),
        (8.4, 2.5, "solver_common", "距离矩阵 K×K", "primary"),
        (10.2, 2.5, "main", "命令分派", "primary"),
    ]
    for (x, y, title, sub, k) in upper:
        node(ax, x, y, 1.6, 0.95, sub, kind=k, title=title, fontsize=8.8)

    # 后端下排:算法核心
    lower = [
        (3.2, 1.15, "dp.cpp", "DP + 分治"),
        (5.7, 1.15, "greedy.cpp", "最近邻"),
        (8.2, 1.15, "dual.cpp", "双车协同"),
    ]
    for (x, y, title, sub) in lower:
        node(ax, x, y, 2.0, 0.95, sub, kind="accent", title=title, fontsize=8.8)

    # ===== 主流向箭头 =====
    arrow(ax, 9.8, 5.20, 9.0, 4.35, label="stdin/stdout", curve=-0.18,
          color=PALETTE["secondary"][1], lw=1.8, mutation=16)
    arrow(ax, 2.5, 3.65, 1.9, 3.05, curve=0.15,
          color=PALETTE["primary"][1], lw=1.8, mutation=16)

    # 后端基础设施 → 算法层
    for x in [3.2, 5.7, 8.2]:
        arrow(ax, x, 1.85, x, 1.65, color=LINE, lw=1.0, mutation=10)

    caption(ax, "图 1 — 系统两层架构:PyQt6 前端 (上) ↔ 行式协议 (中) ↔ C++ 后端 (下)")

    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=BG, pad_inches=0.15)
    plt.close(fig)
    print("saved", path)


# ===================================================================
# 图 2: 算法 pipeline
# ===================================================================
def fig_pipeline(path):
    fig, ax = plt.subplots(figsize=(13, 4.8), dpi=180)
    ax.set_xlim(0, 13); ax.set_ylim(0, 5); ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_facecolor(BG)

    # 主流: input → parse → check → distMat → ALGO → emit
    main = [
        (1.0, 2.5, "INPUT",      "file / stdin",       "warn"),
        (3.0, 2.5, "parse_input","io_utils",           "primary"),
        (5.0, 2.5, "check_feasibility","feasibility",  "primary"),
        (7.0, 2.5, "build_dist_matrix","K×K BFS",      "primary"),
    ]
    for (x, y, title, sub, k) in main:
        node(ax, x, y, 1.7, 1.0, sub, kind=k, title=title, fontsize=9)

    # 5 个算法分支
    algos = [
        (3.6, "dp",           "标准枚举",  "accent"),
        (3.0, "dp_dc",        "分治枚举",  "accent"),
        (2.4, "greedy",       "最近邻",   "accent"),
        (1.8, "multi_dp",     "双车 DP",   "accent"),
        (1.2, "multi_greedy", "双车贪心",  "accent"),
    ]
    algo_x = 9.5
    for (y, title, sub, k) in algos:
        node(ax, algo_x, y, 1.6, 0.55, sub, kind=k, title=title, fontsize=8.2)
        arrow(ax, 7.85, 2.5, algo_x - 0.8, y,
              color=LINE, lw=1.0, mutation=10, curve=0.0)

    # emit_solution
    node(ax, 11.7, 2.5, 1.5, 1.0, "stdout",
         kind="warn", title="emit_solution", fontsize=9)

    for y, _, _, _ in algos:
        arrow(ax, algo_x + 0.8, y, 11.7 - 0.75, 2.5,
              color=LINE, lw=1.0, mutation=10, curve=0.0)

    # 主线箭头
    for x in [1.0, 3.0, 5.0]:
        arrow(ax, x + 0.85, 2.5, x + 2 - 0.85, 2.5,
              color=PALETTE["primary"][1], lw=1.8, mutation=16)
    # 第 4 段
    arrow(ax, 7.85, 2.5, 8.45, 2.5,
          color=PALETTE["primary"][1], lw=1.8, mutation=16)

    # 算法分派标签
    ax.text(8.7, 4.2, "由 ALGO 字段分派", fontsize=9, color=INK_MUTED,
            bbox=dict(facecolor="#fafbfc", edgecolor=LINE, pad=4, boxstyle="round,pad=0.3"))

    caption(ax, "图 2 — 算法端到端 pipeline,算法分派由输入文件最末行 ALGO 字段决定")

    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=BG, pad_inches=0.15)
    plt.close(fig)
    print("saved", path)


# ===================================================================
# 图 3: DP 双层流程
# ===================================================================
def fig_dp_flow(path):
    fig, ax = plt.subplots(figsize=(11.5, 7.5), dpi=180)
    ax.set_xlim(0, 11.5); ax.set_ylim(0, 7.5); ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_facecolor(BG)

    # ====== 输入数据 ======
    node(ax, 1.3, 6.2, 1.9, 0.8,
         "DistanceMatrix D[K×K]\nKeyPoints",
         kind="warn", fontsize=8.5)

    # ====== 内层组框 ======
    group_frame(ax, 2.7, 4.6, 7.5, 2.0, "内层:子集 TSP DP   O(2ⁿ·n²)", PALETTE["accent"][1])

    # tspS 和 tspT
    node(ax, 3.7, 5.85, 1.7, 0.7,
         "depot = S", kind="accent", title="tsp_S[mask][i]", fontsize=8.5)
    node(ax, 6.3, 5.85, 1.7, 0.7,
         "depot = T", kind="accent", title="tsp_T[mask][i]", fontsize=8.5)
    # firstCost laterCost
    node(ax, 3.7, 4.95, 1.7, 0.7,
         "S → Q → T", kind="warn", title="firstCost[Q]", fontsize=8.5)
    node(ax, 6.3, 4.95, 1.7, 0.7,
         "T → Q → T", kind="warn", title="laterCost[Q]", fontsize=8.5)

    # 容量约束注入
    node(ax, 9.0, 5.4, 1.6, 1.2,
         "w(mask) > W_max\n→ cost := +∞", kind="danger", title="容量过滤", fontsize=8)

    # ====== 外层组框 ======
    group_frame(ax, 1.0, 2.0, 9.5, 2.0, "外层:划分 DP   O(3ⁿ)", PALETTE["primary"][1])

    # 划分 DP 主公式节点
    node(ax, 4.0, 3.2, 5.5, 0.8,
         "G[mask] = min{laterCost[Q] + G[mask⊕Q]}",
         kind="primary", fontsize=9.5, weight="bold")
    node(ax, 4.0, 2.35, 5.5, 0.6,
         "Total = min{firstCost[Q₁] + G[full⊕Q₁]}",
         kind="primary", fontsize=9.5, weight="bold")

    # 回溯
    node(ax, 9.2, 3.2, 1.8, 0.8,
         "trips 序列\n+ POINTS\n+ PATH", kind="secondary", title="回溯", fontsize=8.5)

    # ====== 箭头 ======
    arrow(ax, 2.25, 6.2, 2.85, 5.95, color=PALETTE["warn"][1])
    arrow(ax, 2.25, 6.2, 5.45, 5.95, color=PALETTE["warn"][1], curve=-0.10)

    arrow(ax, 3.7, 5.50, 3.7, 5.30)   # tspS -> firstCost
    arrow(ax, 6.3, 5.50, 6.3, 5.30)   # tspT -> laterCost

    arrow(ax, 8.2, 5.4, 7.2, 5.05, color=PALETTE["danger"][1], ls=":", curve=0.10)
    arrow(ax, 8.2, 5.4, 4.6, 5.05, color=PALETTE["danger"][1], ls=":", curve=0.18)

    arrow(ax, 6.3, 4.60, 5.5, 3.65, color=LINE, lw=1.2, curve=-0.10)  # laterCost -> G[mask]
    arrow(ax, 3.7, 4.60, 4.5, 3.65, color=LINE, lw=1.2, curve=0.10)   # firstCost -> Total

    arrow(ax, 4.0, 2.85, 4.0, 2.65,
          color=PALETTE["primary"][1], lw=1.8, mutation=16)
    arrow(ax, 6.8, 3.2, 8.3, 3.2,
          color=PALETTE["secondary"][1], lw=1.8, mutation=16)

    caption(ax, "图 3 — 单车 DP 求解器两层结构:内层 TSP DP 求单程代价,外层划分 DP 决定行程切分")

    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=BG, pad_inches=0.15)
    plt.close(fig)
    print("saved", path)


# ===================================================================
# 图 4: 子集枚举对比
# ===================================================================
def fig_subset_enum(path):
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.2), dpi=180)
    fig.patch.set_facecolor(BG)

    # ============ 左:标准枚举 ============
    ax = axes[0]
    ax.set_xlim(0, 8); ax.set_ylim(0, 7); ax.set_aspect("equal"); ax.axis("off")

    # 标题
    ax.text(4, 6.6, "(a) 标准枚举", ha="center", fontsize=12, color=INK, fontweight="bold")
    ax.text(4, 6.15, "遍历全部 $2^{|mask|}-1$ 个非空子集",
            ha="center", fontsize=9.5, color=INK_MUTED, fontstyle="italic")

    # mask 根节点
    node(ax, 4, 5.4, 2.0, 0.6, "mask = {a, b, c}",
         kind="primary", fontsize=10, weight="bold")

    # 7 个子集
    subsets = ["{a,b,c}", "{a,b}", "{a,c}", "{b,c}", "{a}", "{b}", "{c}"]
    positions = [
        (1.0, 3.8), (2.5, 3.8), (4.0, 3.8), (5.5, 3.8), (7.0, 3.8),
        (2.5, 2.5), (5.5, 2.5),
    ]
    for s, (x, y) in zip(subsets, positions):
        node(ax, x, y, 1.2, 0.55, f"Q = {s}", kind="accent", fontsize=8.5)
        arrow(ax, 4.0, 5.10, x, y + 0.3, color=LINE, lw=0.7, mutation=8)

    # 总数标注
    box = FancyBboxPatch(
        (2.5, 1.0), 3.0, 0.65,
        boxstyle="round,pad=0.0,rounding_size=0.14",
        facecolor=PALETTE["warn"][0], edgecolor=PALETTE["warn"][1], linewidth=1.4)
    ax.add_patch(box)
    ax.text(4, 1.33, "枚举次数 = 7 = $2^3 - 1$",
            ha="center", va="center", fontsize=10.5, color=INK, fontweight="bold")

    ax.text(4, 0.4, "无论 pivot 归属,每个非空子集都被显式枚举一次",
            ha="center", fontsize=8.5, color=INK_MUTED, fontstyle="italic")

    # ============ 右:分治枚举 ============
    ax = axes[1]
    ax.set_xlim(0, 8); ax.set_ylim(0, 7); ax.set_aspect("equal"); ax.axis("off")

    ax.text(4, 6.6, "(b) 分治枚举", ha="center", fontsize=12, color=INK, fontweight="bold")
    ax.text(4, 6.15, "固定 pivot 必属 $Q$,只枚举一半子集",
            ha="center", fontsize=9.5, color=INK_MUTED, fontstyle="italic")

    # mask 根节点 + pivot 标注
    node(ax, 4, 5.4, 2.0, 0.6, "mask = {a, b, c}",
         kind="primary", fontsize=10, weight="bold")
    # pivot 高亮
    ax.annotate("pivot = a", xy=(5.0, 5.4), xytext=(6.5, 5.7),
                fontsize=9.5, color=PALETTE["danger"][1], fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=PALETTE["danger"][1], lw=1.2))

    # 含 a 的 4 个子集 (本层枚举)
    inc_a = ["{a}", "{a,b}", "{a,c}", "{a,b,c}"]
    xs_a = [1.5, 3.3, 4.7, 6.5]
    for s, x in zip(inc_a, xs_a):
        node(ax, x, 4.0, 1.3, 0.55, f"Q = {s}", kind="accent", fontsize=8.5, weight="bold")
        arrow(ax, 4.0, 5.10, x, 4.30,
              color=PALETTE["danger"][1], lw=1.3, mutation=10)

    # 不在本层枚举的 (递归子问题处理)
    excl_a = ["{b}", "{c}", "{b,c}"]
    xs_e = [2.0, 4.0, 6.0]
    for s, x in zip(excl_a, xs_e):
        node(ax, x, 2.6, 1.1, 0.5, f"Q = {s}", kind="neutral", fontsize=8.2)

    ax.text(4, 1.8,
            "↑ 这些 Q 在递归子问题 $G[mask⊕Q]$ 中处理\n(因为 pivot 落入 $mask⊕Q$)",
            ha="center", fontsize=8.5, color=INK_MUTED, fontstyle="italic")

    # 总数标注
    box = FancyBboxPatch(
        (2.5, 0.6), 3.0, 0.65,
        boxstyle="round,pad=0.0,rounding_size=0.14",
        facecolor=PALETTE["accent"][0], edgecolor=PALETTE["accent"][1], linewidth=1.4)
    ax.add_patch(box)
    ax.text(4, 0.93, "枚举次数 = 4 = $2^{3-1}$",
            ha="center", va="center", fontsize=10.5, color=INK, fontweight="bold")

    fig.suptitle("图 4 — 子集枚举对比 (以 mask = {a, b, c} 为例)",
                 fontsize=11, color=INK_MUTED, y=0.04, fontstyle="italic")

    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=BG, pad_inches=0.15)
    plt.close(fig)
    print("saved", path)


# ===================================================================
def main():
    fig_architecture(os.path.join(OUT, "diag_architecture.png"))
    fig_pipeline   (os.path.join(OUT, "diag_pipeline.png"))
    fig_dp_flow    (os.path.join(OUT, "diag_dp_flow.png"))
    fig_subset_enum(os.path.join(OUT, "diag_subset_enum.png"))


if __name__ == "__main__":
    main()
