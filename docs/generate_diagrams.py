"""generate_diagrams.py —— 用 matplotlib 画报告里的系统/算法流程图。
   输出位置: docs/figures/
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# 颜色规范
C_BG = "#fafbfc"
C_BORDER = "#3c4659"
C_NODE_PRIMARY = "#dae8fc"        # 浅蓝
C_NODE_PRIMARY_BD = "#3b7ddd"
C_NODE_DATA = "#fff2cc"           # 浅黄
C_NODE_DATA_BD = "#d6a948"
C_NODE_ALGO = "#d5e8d4"           # 浅绿
C_NODE_ALGO_BD = "#82b366"
C_NODE_IO = "#e1d5e7"             # 浅紫
C_NODE_IO_BD = "#9673a6"
C_ARROW = "#3c4659"


def styled_box(ax, x, y, w, h, text, face, edge, fontsize=10, fontweight="normal"):
    box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        facecolor=face, edgecolor=edge, linewidth=1.4
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight=fontweight, color="#1f2530")


def arrow(ax, x1, y1, x2, y2, label="", style="-|>", color=C_ARROW, lw=1.4, mutation=14, curve=0.0):
    ar = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=mutation,
        color=color, linewidth=lw,
        connectionstyle=f"arc3,rad={curve}",
    )
    ax.add_patch(ar)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.12, label, ha="center", va="center",
                fontsize=8, color="#4a5468",
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5))


# ===================================================================
# 图 1: 系统架构图 (前端 / 通信协议 / 后端三层)
# ===================================================================
def fig_system_architecture(out_path):
    fig, ax = plt.subplots(figsize=(12, 7.2), dpi=160)
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_facecolor("white")

    # === 上层:PyQt6 前端 ===
    ax.text(6, 7.6, "PyQt6 前端 (src/gui/)", ha="center", fontsize=11.5,
            fontweight="bold", color="#2c4096")
    front_y = 6.6
    for i, (x, name) in enumerate([
        (1.8, "main.py\n主窗口装配"),
        (4.0, "map_view.py\n网格视图 (QGraphicsView)"),
        (6.4, "editor.py\n编辑状态管理"),
        (8.8, "animator.py\nQVariantAnimation 补间"),
        (11.0, "controller.py\nsolver 调用与解析"),
    ]):
        styled_box(ax, x, front_y, 2.0, 0.9, name, C_NODE_IO, C_NODE_IO_BD, fontsize=8.5)

    # 前端框
    front_frame = FancyBboxPatch((0.6, 6.0), 10.8, 1.4,
                                  boxstyle="round,pad=0.04,rounding_size=0.12",
                                  facecolor="none", edgecolor=C_NODE_IO_BD,
                                  linewidth=1.0, linestyle="--", alpha=0.55)
    ax.add_patch(front_frame)

    # === 中层:协议层 ===
    proto_y = 4.6
    styled_box(ax, 6, proto_y, 9.4, 0.7, "行式文本协议: 输入文件 + STDOUT (STATUS/ALGORITHM/TRIPS/PATH/...)",
               "#f4f5f7", "#7c8597", fontsize=9.5, fontweight="bold")

    # === 下层:C++ 后端 ===
    ax.text(6, 3.6, "C++ 算法核心 (src/cpp/)", ha="center", fontsize=11.5,
            fontweight="bold", color="#2c8a3a")
    back_y_top = 2.7
    back_y_bot = 1.4

    for x, name in [
        (1.5, "io_utils\n解析/输出"),
        (3.7, "feasibility\ncheck_feasibility()"),
        (6.0, "grid\nBFS / 最短路径"),
        (8.3, "solver_common\nDistanceMatrix"),
        (10.7, "main\n入口与分派"),
    ]:
        styled_box(ax, x, back_y_top, 2.0, 0.85, name, C_NODE_PRIMARY, C_NODE_PRIMARY_BD, fontsize=8.5)

    for x, name in [
        (2.5, "dp.cpp\n标准 / 分治"),
        (5.2, "greedy.cpp\n最近邻启发式"),
        (7.9, "dual.cpp\n双车协同"),
    ]:
        styled_box(ax, x, back_y_bot, 2.2, 0.85, name, C_NODE_ALGO, C_NODE_ALGO_BD, fontsize=8.5)

    # 后端框
    back_frame = FancyBboxPatch((0.4, 0.85), 11.2, 2.6,
                                 boxstyle="round,pad=0.04,rounding_size=0.12",
                                 facecolor="none", edgecolor=C_NODE_PRIMARY_BD,
                                 linewidth=1.0, linestyle="--", alpha=0.55)
    ax.add_patch(back_frame)

    # 流向箭头: 前端→协议→后端
    arrow(ax, 11.0, 6.1, 8.0, 4.95, style="-|>", color=C_NODE_IO_BD, lw=1.6)
    arrow(ax, 4.0, 4.25, 1.5, 3.15, style="-|>", color=C_NODE_PRIMARY_BD, lw=1.6)
    arrow(ax, 1.5, 2.25, 1.5, 1.8, style="-|>", color="#7c8597", lw=1.2)

    ax.text(9.7, 5.4, "stdin/stdout", ha="center", fontsize=8, color="#4a5468",
            bbox=dict(facecolor="white", edgecolor="none"))
    ax.text(2.6, 3.7, "parse + dispatch", ha="center", fontsize=8, color="#4a5468",
            bbox=dict(facecolor="white", edgecolor="none"))

    # 标题
    ax.text(6, 0.3, "图: 系统两层架构与通信协议",
            ha="center", fontsize=9.5, fontstyle="italic", color="#4a5468")

    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", out_path)


# ===================================================================
# 图 2: 算法 pipeline (端到端处理流程)
# ===================================================================
def fig_algorithm_pipeline(out_path):
    fig, ax = plt.subplots(figsize=(13, 4.2), dpi=160)
    ax.set_xlim(0, 13); ax.set_ylim(0, 4); ax.set_aspect("equal"); ax.axis("off")

    # 输入 → 解析 → 校验 → 距离矩阵 → 算法分派 → 输出
    nodes = [
        (1.0, 2.0, "输入\nfile/stdin", C_NODE_IO, C_NODE_IO_BD),
        (2.9, 2.0, "io_utils\nparse_input", C_NODE_PRIMARY, C_NODE_PRIMARY_BD),
        (4.8, 2.0, "check_\nfeasibility", C_NODE_PRIMARY, C_NODE_PRIMARY_BD),
        (6.7, 2.0, "build_distance_\nmatrix (BFS×K)", C_NODE_PRIMARY, C_NODE_PRIMARY_BD),
    ]
    for x, y, name, face, edge in nodes:
        styled_box(ax, x, y, 1.6, 0.95, name, face, edge, fontsize=8.5)

    # 算法分派(竖向 5 个分支)
    algo_x = 9.0
    for i, (name, _color, edge) in enumerate([
        ("solve_dp\n(标准)", C_NODE_ALGO, C_NODE_ALGO_BD),
        ("solve_dp\n(分治)", C_NODE_ALGO, C_NODE_ALGO_BD),
        ("solve_greedy", C_NODE_ALGO, C_NODE_ALGO_BD),
        ("solve_dual\n(DP backend)", C_NODE_ALGO, C_NODE_ALGO_BD),
        ("solve_dual\n(Greedy backend)", C_NODE_ALGO, C_NODE_ALGO_BD),
    ]):
        y = 3.5 - i * 0.7
        styled_box(ax, algo_x, y, 1.65, 0.55, name, _color, edge, fontsize=7.5)
        arrow(ax, 7.6, 2.0, algo_x - 0.85, y, style="-|>", color="#7c8597", lw=1.1, mutation=10)

    # 汇聚到 emit_solution
    emit_x = 11.4
    styled_box(ax, emit_x, 2.0, 1.6, 0.95, "emit_solution\n→ stdout", C_NODE_PRIMARY, C_NODE_PRIMARY_BD, fontsize=8.5)
    for i in range(5):
        y = 3.5 - i * 0.7
        arrow(ax, algo_x + 0.85, y, emit_x - 0.85, 2.0, style="-|>", color="#7c8597", lw=1.1, mutation=10)

    # 主线箭头
    for x in [1.0, 2.9, 4.8, 6.7]:
        arrow(ax, x + 0.85, 2.0, x + 1.9 - 0.85, 2.0, style="-|>", color=C_ARROW, lw=1.5, mutation=14)

    # 标题
    ax.text(6.5, 0.4, "图: 算法端到端 pipeline,算法分派由输入文件最后一行 ALGO 字段触发",
            ha="center", fontsize=9, fontstyle="italic", color="#4a5468")

    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", out_path)


# ===================================================================
# 图 3: DP 双层流程 (子集 TSP 内层 + 划分 DP 外层 + 回溯)
# ===================================================================
def fig_dp_pipeline(out_path):
    fig, ax = plt.subplots(figsize=(12, 7), dpi=160)
    ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.set_aspect("equal"); ax.axis("off")

    # 输入
    styled_box(ax, 1.0, 5.7, 1.6, 0.7, "DistanceMatrix\n+ KeyPoints", C_NODE_DATA, C_NODE_DATA_BD, fontsize=8.5)

    # 内层 TSP DP
    styled_box(ax, 3.5, 5.7, 1.8, 0.7, "tsp_from_depot\n(IDX_S)", C_NODE_ALGO, C_NODE_ALGO_BD, fontsize=8.5)
    styled_box(ax, 6.0, 5.7, 1.8, 0.7, "tsp_from_depot\n(IDX_T)", C_NODE_ALGO, C_NODE_ALGO_BD, fontsize=8.5)
    styled_box(ax, 3.5, 4.6, 1.8, 0.7, "firstCost[Q]\n(S→Q→T)", C_NODE_DATA, C_NODE_DATA_BD, fontsize=8.5)
    styled_box(ax, 6.0, 4.6, 1.8, 0.7, "laterCost[Q]\n(T→Q→T)", C_NODE_DATA, C_NODE_DATA_BD, fontsize=8.5)
    styled_box(ax, 9.2, 5.15, 1.8, 1.3, "对所有不合\n法 mask 置 INF\n(载重 > Wmax)", C_NODE_PRIMARY, C_NODE_PRIMARY_BD, fontsize=8)

    # 外层 划分 DP
    styled_box(ax, 4.6, 3.0, 4.2, 0.95, "划分 DP: G[mask] = min_{Q⊆mask} laterCost[Q] + G[mask⊕Q]", C_NODE_ALGO, C_NODE_ALGO_BD, fontsize=9, fontweight="bold")
    styled_box(ax, 4.6, 1.8, 4.2, 0.7, "顶层: Total = min_{Q₁} firstCost[Q₁] + G[full⊕Q₁]", C_NODE_PRIMARY, C_NODE_PRIMARY_BD, fontsize=9)

    # 回溯
    styled_box(ax, 9.5, 1.8, 2.2, 0.7, "回溯 pick[mask]\n+ recover_order", C_NODE_IO, C_NODE_IO_BD, fontsize=8.5)
    styled_box(ax, 9.5, 0.7, 2.2, 0.7, "Solution.trips", C_NODE_DATA, C_NODE_DATA_BD, fontsize=8.5)

    # 箭头
    arrow(ax, 1.85, 5.7, 2.6, 5.7); arrow(ax, 4.4, 5.7, 5.1, 5.7)
    arrow(ax, 3.5, 5.3, 3.5, 4.95)
    arrow(ax, 6.0, 5.3, 6.0, 4.95)
    arrow(ax, 6.9, 5.7, 8.3, 5.5, curve=0.05)
    arrow(ax, 4.4, 4.6, 4.4, 3.48)
    arrow(ax, 6.9, 4.6, 5.8, 3.48)
    arrow(ax, 9.2, 4.5, 6.7, 3.48, color="#7c8597", lw=1.0)
    arrow(ax, 4.6, 2.52, 4.6, 2.15)
    arrow(ax, 6.7, 1.8, 8.4, 1.8)
    arrow(ax, 9.5, 1.45, 9.5, 1.05)

    # 区域标签
    ax.text(5.0, 6.45, "内层: 子集 TSP DP   O(2ⁿ·n²)", ha="center", fontsize=9.5,
            color="#2c8a3a", fontweight="bold")
    ax.text(4.6, 3.65, "外层: 划分 DP   O(3ⁿ)", ha="center", fontsize=9.5,
            color="#2c8a3a", fontweight="bold")
    ax.text(9.5, 2.45, "结果回溯", ha="center", fontsize=9.5,
            color="#9673a6", fontweight="bold")

    ax.text(6, 0.15, "图: 单车 DP 求解器的两层结构,虚线表示约束注入,主流程沿实线",
            ha="center", fontsize=9, fontstyle="italic", color="#4a5468")

    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", out_path)


# ===================================================================
# 图 4: 子集枚举对比 (标准 vs 分治)
# ===================================================================
def fig_subset_enum_comparison(out_path):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), dpi=160)

    # 左:标准枚举 — mask={a,b,c} 的所有非空子集 7 个
    ax = axes[0]
    ax.set_xlim(0, 8); ax.set_ylim(0, 7); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("(a) 标准枚举: 遍历 mask 的全部 $2^{|mask|}-1$ 个非空子集",
                 fontsize=10.5, color="#1f2530", pad=10)

    # 树根
    styled_box(ax, 4, 6.2, 1.8, 0.65, "mask={a,b,c}", C_NODE_PRIMARY, C_NODE_PRIMARY_BD, fontsize=9, fontweight="bold")
    # 7 个子集 Q,排成两行
    subsets_std = ["{a,b,c}", "{a,b}", "{a,c}", "{b,c}", "{a}", "{b}", "{c}"]
    xs = [1.0, 2.2, 3.4, 4.6, 5.8, 7.0, 4.0]
    ys = [4.6, 4.6, 4.6, 4.6, 4.6, 4.6, 3.0]
    for s, x, y in zip(subsets_std, xs, ys):
        styled_box(ax, x, y, 1.05, 0.55, "Q="+s, C_NODE_ALGO, C_NODE_ALGO_BD, fontsize=8.2)
        arrow(ax, 4, 5.85, x, y + 0.3, color="#7c8597", lw=0.9, mutation=8)

    ax.text(4, 1.8, "枚举次数 = 7 (= $2^3 - 1$)", ha="center", fontsize=11,
            color="#1f2530", fontweight="bold",
            bbox=dict(facecolor="#fff5f0", edgecolor="#d6a948", boxstyle="round,pad=0.3"))
    ax.text(4, 0.8, "每个非空子集都被显式枚举一次,无论 pivot 归属",
            ha="center", fontsize=9, fontstyle="italic", color="#4a5468")

    # 右:分治枚举 — 固定 pivot=a 必属 Q,仅枚举 4 个 Q
    ax = axes[1]
    ax.set_xlim(0, 8); ax.set_ylim(0, 7); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("(b) 分治枚举: 固定 pivot=a 必属 $Q$,只枚举 $2^{|mask|-1}$ 个 $Q$",
                 fontsize=10.5, color="#1f2530", pad=10)

    styled_box(ax, 4, 6.2, 1.8, 0.65, "mask={a,b,c}", C_NODE_PRIMARY, C_NODE_PRIMARY_BD, fontsize=9, fontweight="bold")
    # pivot 标注
    ax.text(6.0, 6.2, "pivot = a", fontsize=9.5, color="#dc3c5a",
            fontweight="bold", va="center")

    # 仅 4 个含 a 的子集
    subsets_dc = ["{a}", "{a,b}", "{a,c}", "{a,b,c}"]
    xs = [1.5, 3.3, 5.0, 6.8]
    for s, x in zip(subsets_dc, xs):
        styled_box(ax, x, 4.6, 1.2, 0.55, "Q="+s, C_NODE_ALGO, C_NODE_ALGO_BD, fontsize=8.2, fontweight="bold")
        arrow(ax, 4, 5.85, x, 4.9, color="#dc3c5a", lw=1.2, mutation=10)

    # 不枚举的子集(虚化显示)
    ax.text(4, 3.5, "不在本层枚举的 Q (= 含 b/c 但不含 a 的子集):",
            ha="center", fontsize=8.5, color="#888")
    omitted = ["{b}", "{c}", "{b,c}"]
    for s, x in zip(omitted, [2.5, 4.0, 5.5]):
        styled_box(ax, x, 2.9, 1.0, 0.45, "Q="+s, "#f0f0f0", "#bbb", fontsize=8.0)

    # 解释箭头
    ax.text(4, 2.0, "这些 Q 通过递归子问题 $G[mask⊕Q]$ 处理\n(其中 pivot=a 必属于该子问题)",
            ha="center", fontsize=8.5, color="#4a5468", fontstyle="italic")

    ax.text(4, 0.8, "枚举次数 = 4 (= $2^{3-1}$),减半",
            ha="center", fontsize=11, color="#1f2530", fontweight="bold",
            bbox=dict(facecolor="#f0fdf4", edgecolor="#82b366", boxstyle="round,pad=0.3"))

    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", out_path)


# ===================================================================
def main():
    fig_system_architecture(os.path.join(OUT, "diag_architecture.png"))
    fig_algorithm_pipeline(os.path.join(OUT, "diag_pipeline.png"))
    fig_dp_pipeline(os.path.join(OUT, "diag_dp_flow.png"))
    fig_subset_enum_comparison(os.path.join(OUT, "diag_subset_enum.png"))


if __name__ == "__main__":
    main()
