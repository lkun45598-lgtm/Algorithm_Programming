"""dense_benchmark.py —— 密集基准实验.

对 n ∈ {3,4,5,6,7,8} × 障碍密度 ρ ∈ {0, 0.10, 0.20, 0.30} × 多种子, 跑
五种算法 (dp / dp_dc / greedy / multi_dp / multi_greedy), 每个数据点
重复 RUNS 次取均值与标准差.

输出:
  docs/figures/bench_distance_vs_n.png    总距离 vs n
  docs/figures/bench_runtime_vs_n.png     运行时间 vs n (log y)
  docs/figures/bench_obstacle_effect.png  障碍密度对总距离的影响 (n=6)
  docs/figures/bench_dp_vs_dpdc.png       dp 与 dp_dc 运行时间细分对比
  tests/dense_benchmark_log.csv           原始数据

用法:
  python tests/dense_benchmark.py [seeds=20] [runs=5]
"""
import csv
import os
import random
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from random_case_generator import generate, to_solver_input  # noqa: E402

SOLVER = os.path.abspath(os.path.join(ROOT, "build", "solver.exe"))
OUT_FIG = os.path.join(ROOT, "docs", "figures")
os.makedirs(OUT_FIG, exist_ok=True)

ALGOS = ["dp", "dp_dc", "greedy", "multi_dp", "multi_greedy"]
N_RANGE = list(range(3, 9))
OBS_RATIOS = [0.0, 0.10, 0.20, 0.30]


def run_once(input_text):
    """调用 solver 并返回 (distance, runtime_ms),失败返回 (None, None)。"""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(input_text); p = f.name
    try:
        proc = subprocess.run([SOLVER, p], capture_output=True, text=True,
                              encoding="utf-8", timeout=30)
    finally:
        try: os.unlink(p)
        except OSError: pass
    dist = rt = None; ok = False
    for ln in proc.stdout.splitlines():
        tok = ln.split()
        if not tok: continue
        if tok[0] == "STATUS": ok = (tok[1] == "ok")
        elif tok[0] == "TOTAL_DISTANCE": dist = int(tok[1])
        elif tok[0] == "RUNTIME_MS":     rt = float(tok[1])
    if not ok: return None, None
    return dist, rt


def collect(n_seeds=20, runs=5):
    """三重循环 (n, ratio, seed) × ALGOS, 每点 RUNS 次取均值/stddev."""
    rows = []  # (n, ratio, algo, seed, dist, rt_mean, rt_stddev)
    rng = random.Random(0)
    seeds = sorted(rng.sample(range(1, 10_000), n_seeds))

    for n in N_RANGE:
        for ratio in OBS_RATIOS:
            for seed in seeds:
                inst = generate(seed, n, ratio)
                if inst is None: continue
                for algo in ALGOS:
                    txt = to_solver_input(inst, algo=algo)
                    times = []; dist = None
                    for _ in range(runs):
                        d, t = run_once(txt)
                        if d is None: break
                        dist = d; times.append(t)
                    if dist is None or not times: continue
                    mean = sum(times) / len(times)
                    std = statistics.pstdev(times) if len(times) > 1 else 0.0
                    rows.append((n, ratio, algo, seed, dist, mean, std))
                    print(f"  n={n} ρ={ratio:.2f} seed={seed:5d} {algo:13s}"
                          f" dist={dist:4d} rt={mean:8.3f}±{std:6.3f} ms")
    return rows


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "ratio", "algo", "seed", "distance", "rt_mean_ms", "rt_std_ms"])
        for r in rows: w.writerow(r)


def make_figures(rows):
    import numpy as np
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False

    # 聚合: (n, algo) -> list of (distance, rt_mean)
    agg = {}
    for n, ratio, algo, seed, dist, rtm, rts in rows:
        agg.setdefault((n, algo, ratio), []).append((dist, rtm))

    # ====== 图 1: 总距离 vs n (聚合所有 ratio 后取均值, 加 95% CI) ======
    fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=160)
    colors = {"dp":"#3b7ddd","dp_dc":"#6c93d9","greedy":"#f0a050",
              "multi_dp":"#28a745","multi_greedy":"#3cb878"}
    for algo in ALGOS:
        xs, ys, errs = [], [], []
        for n in N_RANGE:
            pool = []
            for r in OBS_RATIOS:
                pool.extend(d for d,_ in agg.get((n, algo, r), []))
            if not pool: continue
            xs.append(n); m = sum(pool)/len(pool); ys.append(m)
            errs.append(1.96 * statistics.pstdev(pool) / (len(pool) ** 0.5) if len(pool) > 1 else 0)
        ax.errorbar(xs, ys, yerr=errs, fmt="-o", label=algo,
                    color=colors[algo], linewidth=1.8, markersize=4.5,
                    capsize=3, alpha=0.92)
    ax.set_xlabel("收集点数 $n$")
    ax.set_ylabel("平均总距离 (95% CI)")
    ax.set_title("总距离随收集点数的变化 (跨 4 种障碍密度 × 多种子聚合)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(frameon=False, ncol=5, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(OUT_FIG, "bench_distance_vs_n.png"))
    plt.close(fig)

    # ====== 图 2: 运行时间 vs n (log y) ======
    fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=160)
    for algo in ALGOS:
        xs, ys = [], []
        for n in N_RANGE:
            pool = []
            for r in OBS_RATIOS:
                pool.extend(t for _,t in agg.get((n, algo, r), []))
            if not pool: continue
            xs.append(n); ys.append(sum(pool)/len(pool))
        ax.plot(xs, ys, "-o", label=algo, color=colors[algo], linewidth=1.8, markersize=4.5)
    ax.set_yscale("log")
    ax.set_xlabel("收集点数 $n$")
    ax.set_ylabel("平均运行时间 (ms, log)")
    ax.set_title("运行时间随收集点数的变化")
    ax.grid(axis="y", linestyle="--", alpha=0.4, which="both")
    ax.legend(frameon=False, ncol=5, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(OUT_FIG, "bench_runtime_vs_n.png"))
    plt.close(fig)

    # ====== 图 3: 障碍密度对总距离的影响 (n=6) ======
    fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=160)
    for algo in ALGOS:
        xs, ys, errs = [], [], []
        for r in OBS_RATIOS:
            pool = [d for d,_ in agg.get((6, algo, r), [])]
            if not pool: continue
            xs.append(r); ys.append(sum(pool)/len(pool))
            errs.append(1.96 * statistics.pstdev(pool) / (len(pool) ** 0.5) if len(pool) > 1 else 0)
        ax.errorbar(xs, ys, yerr=errs, fmt="-o", label=algo,
                    color=colors[algo], linewidth=1.8, markersize=5, capsize=3)
    ax.set_xlabel("障碍密度 $rho$")
    ax.set_ylabel("平均总距离 (95% CI)")
    ax.set_title("障碍密度对总距离的影响 (n = 6)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(frameon=False, ncol=5, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(OUT_FIG, "bench_obstacle_effect.png"))
    plt.close(fig)

    # ====== 图 4: dp 与 dp_dc 运行时间比 (pivot 枚举的实际收益) ======
    fig, ax = plt.subplots(figsize=(8.5, 4.4), dpi=160)
    ns, ratios = [], []
    for n in N_RANGE:
        rt_std = []; rt_dc = []
        for r in OBS_RATIOS:
            for d,t in agg.get((n,"dp",r), []): rt_std.append(t)
            for d,t in agg.get((n,"dp_dc",r), []): rt_dc.append(t)
        if not rt_std or not rt_dc: continue
        ns.append(n)
        ratios.append((sum(rt_dc)/len(rt_dc)) / (sum(rt_std)/len(rt_std)))
    ax.bar(ns, ratios, color="#3b7ddd", alpha=0.75, edgecolor="#2c66c0")
    ax.axhline(1.0, color="red", linestyle="--", linewidth=1.0, alpha=0.6,
               label="基线 (dp_dc / dp = 1.0)")
    ax.set_xlabel("收集点数 $n$"); ax.set_ylabel("dp_dc 运行时间 / dp 运行时间")
    ax.set_title("pivot 枚举相对标准枚举的实测加速比 (越低越快)")
    for x, y in zip(ns, ratios):
        ax.text(x, y + 0.02, f"{y:.2f}", ha="center", fontsize=8.5)
    ax.set_ylim(0, max(1.1, max(ratios) * 1.15) if ratios else 1.2)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(OUT_FIG, "bench_dp_vs_dpdc.png"))
    plt.close(fig)

    print("\n所有图已生成到", OUT_FIG)


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    runs    = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    print(f"# 密集基准 n_seeds={n_seeds}, runs={runs}\n")
    rows = collect(n_seeds, runs)
    write_csv(rows, os.path.join(HERE, "dense_benchmark_log.csv"))
    make_figures(rows)
    print(f"\n# 共 {len(rows)} 个数据点, 详见 tests/dense_benchmark_log.csv")


if __name__ == "__main__":
    main()
