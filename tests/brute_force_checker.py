"""brute_force_checker.py —— DP 解的黄金标准独立验证。

策略: 不依赖 solver_common 的 DP, 而是从头自己实现 BFS + 全枚举:
  1. BFS 计算关键点间的最短距离 (与 solver 完全独立的另一份实现)
  2. 枚举所有排列 (n! 种) + 所有切分点 (2^{n-1} 种), 校验每个 trip
     的载重不超 W_max, 计算总距离, 取全局最小
  3. 与 solver 输出对比

仅适用于 n <= 5. 每例 n=5 大约枚举 120 * 16 = 1920 个组合.

用法:
    python tests/brute_force_checker.py SEEDS_FILE [N_MAX]

SEEDS_FILE 每行一个整数 seed (见 tests/seeds.txt).
"""
import itertools
import os
import subprocess
import sys
import tempfile
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from random_case_generator import generate, to_solver_input  # noqa: E402

SOLVER = os.path.join(ROOT, "build", "solver.exe")


def bfs_dist(cells, M, L, src):
    """从 src=(r,c) 出发 4 邻接 BFS 距离场."""
    dist = [[-1] * L for _ in range(M)]
    dist[src[0]][src[1]] = 0
    q = deque([src])
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < M and 0 <= nc < L):
                continue
            if cells[nr][nc] == '#':
                continue
            if dist[nr][nc] != -1:
                continue
            dist[nr][nc] = dist[r][c] + 1
            q.append((nr, nc))
    return dist


def build_dist_matrix(M, L, cells, S, T, pts):
    """K x K 距离矩阵 (K = n + 2). 索引: 0=S, 1=T, 2+i=pts[i]"""
    n = len(pts)
    K = n + 2
    keys = [S, T] + list(pts)
    D = [[-1] * K for _ in range(K)]
    for u in range(K):
        d = bfs_dist(cells, M, L, keys[u])
        for v in range(K):
            D[u][v] = d[keys[v][0]][keys[v][1]]
    return D, keys


def brute_force_best(D, weights, W_max):
    """枚举 n! 排列 + 2^{n-1} 切分点, 返回最优总代价 (无可行解返回 None).

    排列 perm = (p_0, p_1, ..., p_{n-1}) 表示按此顺序访问.
    切分点 mask of (n-1) 位: 第 j 位为 1 表示在 perm[j] 与 perm[j+1] 之间
    切开 (前一行程结束并回 T 卸货, 后续行程从 T 开始).
    """
    n = len(weights)
    if n == 0:
        return 0
    best = None
    IDX_S, IDX_T = 0, 1
    IDX_P = lambda i: 2 + i  # noqa: E731

    for perm in itertools.permutations(range(n)):
        for split in range(1 << (n - 1)):
            # 切出 trip 序列
            trips = [[perm[0]]]
            for j in range(1, n):
                if (split >> (j - 1)) & 1:
                    trips.append([perm[j]])
                else:
                    trips[-1].append(perm[j])
            # 验载重
            ok = all(sum(weights[i] for i in t) <= W_max for t in trips)
            if not ok:
                continue
            # 计算总距离
            cost = 0
            valid = True
            for ti, t in enumerate(trips):
                depot = IDX_S if ti == 0 else IDX_T
                # depot -> P_t[0] -> ... -> P_t[-1] -> T
                d_first = D[depot][IDX_P(t[0])]
                if d_first < 0: valid = False; break
                cost += d_first
                for k in range(1, len(t)):
                    e = D[IDX_P(t[k - 1])][IDX_P(t[k])]
                    if e < 0: valid = False; break
                    cost += e
                if not valid: break
                back = D[IDX_P(t[-1])][IDX_T]
                if back < 0: valid = False; break
                cost += back
            if not valid:
                continue
            if best is None or cost < best:
                best = cost
    return best


def solver_distance(input_text):
    """调用 solver.exe, 解析 TOTAL_DISTANCE."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(input_text); p = f.name
    try:
        proc = subprocess.run([SOLVER, p], capture_output=True, text=True,
                              encoding="utf-8", timeout=30)
    finally:
        try: os.unlink(p)
        except OSError: pass
    for ln in proc.stdout.splitlines():
        if ln.startswith("STATUS"):
            if ln.split()[1] != "ok":
                return None  # infeasible 或 error
        if ln.startswith("TOTAL_DISTANCE"):
            return int(ln.split()[1])
    return None


def check_one(seed, n, ratio, algo):
    inst = generate(seed, n, ratio)
    if inst is None:
        return ("SKIP", seed, n, ratio, None, None, "无法生成实例")
    M, L, cells, S, T, pts, weights, W_max = inst
    D, _keys = build_dist_matrix(M, L, cells, S, T, pts)

    # 校验可行性 (max w <= W_max < sum w 已由 generator 保证, 但点位可能不可达)
    if any(D[u][v] < 0 for u in range(len(D)) for v in range(len(D))):
        return ("SKIP", seed, n, ratio, None, None, "存在不可达对")

    brute = brute_force_best(D, weights, W_max)
    if brute is None:
        return ("SKIP", seed, n, ratio, None, None, "暴力枚举无可行解")

    txt = to_solver_input(inst, algo=algo)
    solver = solver_distance(txt)
    if solver is None:
        return ("FAIL_INFEASIBLE", seed, n, ratio, brute, None, f"solver 返回不可行 ({algo})")
    if solver == brute:
        return ("PASS", seed, n, ratio, brute, solver, f"{algo}={solver} 与暴力一致")
    return ("MISMATCH", seed, n, ratio, brute, solver,
            f"{algo}={solver} 与暴力={brute} 不一致!")


def main():
    seeds_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "seeds.txt")
    n_max = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    with open(seeds_file, encoding="utf-8") as f:
        seeds = []
        for line in f:
            line = line.split('#', 1)[0].strip()
            if line:
                seeds.append(int(line))

    print(f"# 暴力对拍 — 共 {len(seeds)} 个种子, n ∈ [3, {n_max}]")
    print(f"# solver: {SOLVER}\n")

    stats = {"PASS": 0, "MISMATCH": 0, "SKIP": 0, "FAIL_INFEASIBLE": 0}
    log = []
    for seed in seeds:
        for n in range(3, n_max + 1):
            for ratio in (0.0, 0.20):
                for algo in ("dp", "dp_dc"):
                    r = check_one(seed, n, ratio, algo)
                    stats[r[0]] = stats.get(r[0], 0) + 1
                    if r[0] == "MISMATCH":
                        msg = f"[MISMATCH] seed={seed} n={n} ratio={ratio} {r[6]}"
                        print(msg); log.append(msg)
                    elif r[0] == "PASS":
                        log.append(f"[PASS] seed={seed} n={n} ratio={ratio} {r[6]}")

    print("\n# 汇总")
    for k, v in stats.items():
        print(f"  {k:18s}: {v}")
    if stats["MISMATCH"] == 0:
        print("\n  所有测试通过 (暴力与 DP 输出完全一致).")
    else:
        print(f"\n  存在 {stats['MISMATCH']} 例不一致, 见上方 [MISMATCH] 行.")
    return 0 if stats["MISMATCH"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
