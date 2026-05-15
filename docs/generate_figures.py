"""generate_figures.py —— 为课程设计报告生成所有 matplotlib 图表

调用 build/solver.exe 跑各 sample × algo 组合, 解析输出, 渲染:
  - problem_schematic.png        问题示意图 (6x6 示例)
  - path_<sample>_<algo>.png     6 张路径图 (small/medium/large × dp/multi_dp)
  - compare_distance.png         五种算法总距离对比柱状图
  - compare_runtime.png          五种算法运行时间对比柱状图 (对数轴)

依赖: matplotlib, numpy (pytorch conda env 自带).
"""
import os
import sys
import subprocess
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SOLVER = os.path.join(ROOT, 'build', 'solver.exe')
DATA_DIR = os.path.join(ROOT, 'data')
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figures')
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, 'src', 'gui'))
from controller import parse_solver_output  # noqa: E402

plt.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 调色板: 用于不同 trip 的折线颜色
TRIP_COLORS = [
    '#ff8c00', '#0096c8', '#b450c8', '#50b450', '#dc3c5a',
    '#7864c8', '#288ca0', '#c88c28', '#5078d2', '#a05050',
]


# --------------------------------------------------------------- solver I/O ---

def run_solver(sample_path, algo):
    """读取样例文件, 替换/插入 ALGO 行, 写临时文件, 跑 solver, 解析."""
    with open(sample_path, encoding='utf-8') as f:
        txt = f.read()
    out_lines = []
    seen_algo = False
    for ln in txt.splitlines():
        if ln.startswith('ALGO '):
            out_lines.append('ALGO ' + algo)
            seen_algo = True
        else:
            out_lines.append(ln)
    if not seen_algo:
        out_lines.append('ALGO ' + algo)
    new_txt = '\n'.join(out_lines) + '\n'

    fd, tmp_path = tempfile.mkstemp(suffix='.txt', text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(new_txt)
        proc = subprocess.run(
            [SOLVER, tmp_path],
            capture_output=True, text=True, encoding='utf-8', timeout=60,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return parse_solver_output(proc.stdout)


def parse_sample(sample_path):
    """读取样例的栅格 + S/T/P 列表 (供绘制底图)."""
    with open(sample_path, encoding='utf-8') as f:
        lines = [ln.rstrip() for ln in f.read().splitlines()]
    M, N = map(int, lines[0].split())
    cells = lines[1:1 + M]
    idx = 1 + M
    S = tuple(map(int, lines[idx].split())); idx += 1
    T = tuple(map(int, lines[idx].split())); idx += 1
    K = int(lines[idx]); idx += 1
    points, weights = [], []
    for _ in range(K):
        r, c, w = map(int, lines[idx].split()); idx += 1
        points.append((r, c)); weights.append(w)
    w_max = int(lines[idx])
    return M, N, cells, S, T, points, weights, w_max


# --------------------------------------------------------------- 底图绘制 ---

def draw_grid(ax, M, N, cells, S, T, points, weights):
    """绘制底图: 障碍 / 空格 / S / T / 编号点."""
    for r in range(M):
        for c in range(N):
            color = '#46505f' if cells[r][c] == '#' else '#ffffff'
            ax.add_patch(patches.Rectangle(
                (c, M - 1 - r), 1, 1,
                facecolor=color, edgecolor='#dde0e5', linewidth=0.6,
            ))

    # S (green)
    sx, sy = S[1] + 0.1, M - 1 - S[0] + 0.1
    ax.add_patch(patches.FancyBboxPatch(
        (sx, sy), 0.8, 0.8,
        boxstyle='round,pad=0.02,rounding_size=0.12',
        facecolor='#3ca055', edgecolor='#2e7d40', linewidth=1.2,
    ))
    ax.text(S[1] + 0.5, M - 1 - S[0] + 0.5, 'S',
            ha='center', va='center', color='white',
            fontsize=11, fontweight='bold')

    # T (red)
    tx, ty = T[1] + 0.1, M - 1 - T[0] + 0.1
    ax.add_patch(patches.FancyBboxPatch(
        (tx, ty), 0.8, 0.8,
        boxstyle='round,pad=0.02,rounding_size=0.12',
        facecolor='#dc3c50', edgecolor='#a02638', linewidth=1.2,
    ))
    ax.text(T[1] + 0.5, M - 1 - T[0] + 0.5, 'T',
            ha='center', va='center', color='white',
            fontsize=11, fontweight='bold')

    # P_i (blue)
    for i, ((r, c), w) in enumerate(zip(points, weights)):
        px, py = c + 0.1, M - 1 - r + 0.1
        ax.add_patch(patches.FancyBboxPatch(
            (px, py), 0.8, 0.8,
            boxstyle='round,pad=0.02,rounding_size=0.12',
            facecolor='#3c5ac8', edgecolor='#2c4096', linewidth=1.2,
        ))
        ax.text(c + 0.5, M - 1 - r + 0.5, f'{i}',
                ha='center', va='center', color='white',
                fontsize=10, fontweight='bold')
        # 右上角小字: 重量
        ax.text(c + 0.92, M - 1 - r + 0.92, f'{w}',
                ha='right', va='top', color='#ffe6a0',
                fontsize=7, fontweight='bold')

    ax.set_xlim(0, N); ax.set_ylim(0, M)
    ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


# --------------------------------------------------------------- 路径图 ---

def render_path_fig(sample_name, algo, out_path):
    sample_path = os.path.join(DATA_DIR, f'sample_{sample_name}.txt')
    M, N, cells, S, T, points, weights, w_max = parse_sample(sample_path)
    sol = run_solver(sample_path, algo)
    if not sol.ok:
        print(f'  FAILED {sample_name}/{algo}: {sol.status} {sol.reason}')
        return

    # 图尺寸随网格变化, 给图例留 ~2.2in 右边
    fig_w = N * 0.5 + 2.6
    fig_h = M * 0.5 + 1.2
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    draw_grid(ax, M, N, cells, S, T, points, weights)

    legend_handles, legend_labels = [], []
    color_idx = 0
    for vi, v in enumerate(sol.vehicles):
        for ti, trip in enumerate(v):
            color = TRIP_COLORS[color_idx % len(TRIP_COLORS)]
            color_idx += 1
            if not trip.path:
                continue
            # 把 trip.path 中重复经过的格子稍作偏移让线条不完全重合
            xs = [p[1] + 0.5 for p in trip.path]
            ys = [M - 1 - p[0] + 0.5 for p in trip.path]
            line, = ax.plot(
                xs, ys,
                color=color, linewidth=2.6, alpha=0.78,
                solid_capstyle='round', solid_joinstyle='round',
            )
            if len(sol.vehicles) > 1:
                label = f'车{vi + 1}-行程{ti + 1} (载{trip.load} 距{trip.distance})'
            else:
                label = f'行程{ti + 1} (载{trip.load} 距{trip.distance})'
            legend_handles.append(line)
            legend_labels.append(label)

    if legend_handles:
        ax.legend(
            legend_handles, legend_labels,
            loc='upper left', bbox_to_anchor=(1.02, 1.0),
            fontsize=8, frameon=False, handlelength=2.2,
        )

    ax.set_title(
        f'sample_{sample_name} / {algo}     '
        f'总距离 = {sol.total_distance}     '
        f'运行 {sol.runtime_ms:.3f} ms',
        fontsize=11, pad=10,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  saved {os.path.basename(out_path)}  '
          f'(total={sol.total_distance}, rt={sol.runtime_ms:.3f}ms)')


# --------------------------------------------------------------- 距离对比 ---

ALGO_LIST = ['dp', 'dp_dc', 'greedy', 'multi_dp', 'multi_greedy']
ALGO_COLORS = ['#3b7ddd', '#6c93d9', '#f0a050', '#28a745', '#7ad19a']
SAMPLE_LIST = ['small', 'medium', 'large']


def fig_distance_compare(out_path):
    data = {}
    for s in SAMPLE_LIST:
        for a in ALGO_LIST:
            sol = run_solver(os.path.join(DATA_DIR, f'sample_{s}.txt'), a)
            data[(s, a)] = sol.total_distance if sol.ok else 0
            print(f'    {s:>7s} / {a:<14s} dist={sol.total_distance}')

    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=150)
    x = np.arange(len(SAMPLE_LIST))
    width = 0.16
    n = len(ALGO_LIST)
    for i, a in enumerate(ALGO_LIST):
        vals = [data[(s, a)] for s in SAMPLE_LIST]
        offset = (i - (n - 1) / 2) * width
        bars = ax.bar(x + offset, vals, width, label=a, color=ALGO_COLORS[i])
        for b, v in zip(bars, vals):
            if v > 0:
                ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.01,
                        str(v), ha='center', va='bottom', fontsize=7.5)

    ax.set_xticks(x)
    ax.set_xticklabels([f'sample_{s}' for s in SAMPLE_LIST])
    ax.set_ylabel('总距离 (步数)')
    ax.set_title('五种算法在三个样例上的总距离对比', fontsize=12)
    ax.legend(loc='upper left', frameon=False, ncol=5, fontsize=9)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # 给 legend 留空间
    ymax = ax.get_ylim()[1]
    ax.set_ylim(0, ymax * 1.18)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  saved {os.path.basename(out_path)}')


# --------------------------------------------------------------- 运行时间对比 ---

def fig_runtime_compare(out_path, repeats=10):
    data = {}
    for s in SAMPLE_LIST:
        for a in ALGO_LIST:
            ts = []
            for _ in range(repeats):
                sol = run_solver(os.path.join(DATA_DIR, f'sample_{s}.txt'), a)
                if sol.ok:
                    ts.append(sol.runtime_ms)
            data[(s, a)] = sum(ts) / len(ts) if ts else 0.0
            print(f'    {s:>7s} / {a:<14s} avg_rt={data[(s,a)]:.4f} ms ({len(ts)} runs)')

    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=150)
    x = np.arange(len(SAMPLE_LIST))
    width = 0.16
    n = len(ALGO_LIST)
    for i, a in enumerate(ALGO_LIST):
        vals = [max(data[(s, a)], 1e-4) for s in SAMPLE_LIST]  # log scale 不允许 0
        offset = (i - (n - 1) / 2) * width
        bars = ax.bar(x + offset, vals, width, label=a, color=ALGO_COLORS[i])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 1.10,
                    f'{v:.3g}', ha='center', va='bottom', fontsize=7.5)

    ax.set_xticks(x)
    ax.set_xticklabels([f'sample_{s}' for s in SAMPLE_LIST])
    ax.set_ylabel('平均运行时间 (ms, 对数轴)')
    ax.set_yscale('log')
    ax.set_title(f'五种算法在三个样例上的运行时间对比 (每点 {repeats} 次平均)',
                 fontsize=12)
    ax.legend(loc='upper left', frameon=False, ncol=5, fontsize=9,
              bbox_to_anchor=(0.0, 1.0))
    ax.grid(axis='y', linestyle='--', alpha=0.4, which='both')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  saved {os.path.basename(out_path)}')


# --------------------------------------------------------------- 问题示意图 ---

def fig_problem_schematic(out_path):
    M, N = 6, 6
    cells = [
        '......',
        '.##...',
        '.##...',
        '......',
        '...##.',
        '......',
    ]
    S = (0, 0); T = (5, 5)
    points = [(1, 4), (3, 2), (5, 1)]
    weights = [1, 2, 2]

    fig, ax = plt.subplots(figsize=(5.4, 5.4), dpi=150)
    draw_grid(ax, M, N, cells, S, T, points, weights)

    # 辅助标注: 在右侧加一段图例样式的说明
    ax.set_title('问题示意图: 6 × 6 网格, S = 停车场, T = 处理厂, P0~P2 = 收集点',
                 fontsize=10, pad=12)

    # 注解箭头: 示意一条可行路线 (仅示意, 不调用 solver)
    # S -> P2 -> P1 -> P0 -> T 的简化引导线
    illustrative = [(0, 0), (3, 0), (5, 1), (3, 2), (1, 4), (5, 5)]
    xs = [c + 0.5 for r, c in illustrative]
    ys = [M - 1 - r + 0.5 for r, c in illustrative]
    ax.plot(xs, ys, color='#ff8c00', linewidth=2.2, alpha=0.55,
            linestyle='--', solid_capstyle='round', label='示意路径')
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0),
              fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  saved {os.path.basename(out_path)}')


# --------------------------------------------------------------- main ---

def main():
    if not os.path.exists(SOLVER):
        raise SystemExit(f'solver not found: {SOLVER} — please build first')

    print('[1/4] problem_schematic.png')
    fig_problem_schematic(os.path.join(OUT_DIR, 'problem_schematic.png'))

    print('[2/4] path_<sample>_<algo>.png  (6 figures)')
    for s in SAMPLE_LIST:
        for a in ['dp', 'multi_dp']:
            render_path_fig(s, a, os.path.join(OUT_DIR, f'path_{s}_{a}.png'))

    print('[3/4] compare_distance.png')
    fig_distance_compare(os.path.join(OUT_DIR, 'compare_distance.png'))

    print('[4/4] compare_runtime.png')
    fig_runtime_compare(os.path.join(OUT_DIR, 'compare_runtime.png'))

    print('\nAll figures written to:', OUT_DIR)


if __name__ == '__main__':
    main()
