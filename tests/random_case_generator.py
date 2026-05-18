"""random_case_generator.py —— 生成随机网格实例供暴力对拍使用。

用法:
    python tests/random_case_generator.py SEED N [OBSTACLE_RATIO]

输出: 标准输入文件格式 (见 README 附录 A) 写到 stdout。
所有点位、$W_max$ 通过给定 seed 确定性生成,可复现。
"""
import random
import sys


def generate(seed: int, n: int, obstacle_ratio: float = 0.15):
    """生成一个 (10..14)×(10..14) 的随机实例,包含 n 个收集点。"""
    rng = random.Random(seed)
    M = rng.randint(8, 12)
    L = rng.randint(8, 12)

    # 1) 随机障碍 (避免占用 (0,0) 和 (M-1,L-1) 这两个我们要放 S/T 的角)
    cells = [['.'] * L for _ in range(M)]
    cell_total = M * L
    n_obstacles = int(cell_total * obstacle_ratio)
    free_cells = [(r, c) for r in range(M) for c in range(L)
                  if (r, c) != (0, 0) and (r, c) != (M - 1, L - 1)]
    rng.shuffle(free_cells)
    for r, c in free_cells[:n_obstacles]:
        cells[r][c] = '#'

    # 2) S = 左上角, T = 右下角. 验证它们都不在障碍上 (上面已经排除).
    S = (0, 0); T = (M - 1, L - 1)

    # 3) 随机选 n 个非障碍且不与 S/T 重合的点
    candidates = [(r, c) for r in range(M) for c in range(L)
                  if cells[r][c] == '.' and (r, c) != S and (r, c) != T]
    rng.shuffle(candidates)
    pts = candidates[:n]
    if len(pts) < n:
        return None  # 候选不够

    # 4) 随机重量, 必须满足 max(w) <= W_max < sum(w)
    weights = [rng.randint(1, 3) for _ in range(n)]
    sum_w = sum(weights); max_w = max(weights)
    # W_max 在 [max_w, sum_w - 1] 之间, 至少多车
    if max_w >= sum_w:
        weights[0] = max(1, sum_w - 1)
        sum_w = sum(weights); max_w = max(weights)
    W_max = rng.randint(max_w, sum_w - 1)

    return M, L, cells, S, T, pts, weights, W_max


def to_solver_input(inst, algo: str = "dp") -> str:
    M, L, cells, S, T, pts, weights, W_max = inst
    lines = [f"{M} {L}"]
    lines.extend(''.join(row) for row in cells)
    lines.append(f"{S[0]} {S[1]}")
    lines.append(f"{T[0]} {T[1]}")
    lines.append(str(len(pts)))
    for (r, c), w in zip(pts, weights):
        lines.append(f"{r} {c} {w}")
    lines.append(str(W_max))
    lines.append(f"ALGO {algo}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    ratio = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
    inst = generate(seed, n, ratio)
    if inst is None:
        sys.stderr.write(f"无法生成: seed={seed} n={n} ratio={ratio}\n")
        sys.exit(1)
    sys.stdout.write(to_solver_input(inst))
