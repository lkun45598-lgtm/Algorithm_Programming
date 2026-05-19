# 样例库 (sample_library)

每个子目录覆盖一类输入场景, 用于回归测试、答辩演示和报告佐证。所有用例的预期状态 (`ok` / `infeasible` / `error`) 已通过 `tests/verify_sample_library.py` 校验, 见 `tests/sample_library_log.csv` (20/20 PASS)。

## 可行实例 (status = ok)

| 子目录 | 用例 | 关键考察点 |
|---|---|---|
| `basic/` | `empty_grid.txt` | 6×6 无障碍, 3 收集点, 默认 DP 路径 |
| `basic/` | `two_collects.txt` | 2 收集点, 容量约束触发 2 次行程 |
| `capacity/` | `forced_multi_trip.txt` | 4 点各重 3, $W_{\max} = 3$, 强制 4 次往返 |
| `capacity/` | `exact_fit.txt` | $W_{\max}$ 恰等于单点最大重量, 验证装载边界 |
| `obstacle/` | `walled.txt` | 内嵌矩形墙 + 顶部开口, 测试 BFS 穿洞绕路 |
| `obstacle/` | `narrow_corridor.txt` | 横向窄走廊, 多收集点跨走廊 |
| `compare/` | `greedy_suboptimal.txt` | 贪心最近邻 vs DP 总距离不一致, 体现 DP 优势 |
| `multi_vehicle/` | `balanced_split.txt` | 左右对称布局, 双车 DP 应近似 1:1 划分 |
| `multi_vehicle/` | `asymmetric_split.txt` | 5 点非对称, 验证 `singleCost[mask]` 全集分割 |

## 可行性检查不通过 (status = infeasible)

可行性检查在 `feasibility.cpp` 内统一处理, 涉及容量、重量、重复、可达性五类约束, 全部返回 `infeasible`。

| 子目录 | 用例 | 触发的约束 |
|---|---|---|
| `invalid_load/` | `overweight_single.txt` | $w_i > W_{\max}$ (3 > 1) |
| `invalid_load/` | `wmax_too_large.txt` | $\sum w_i \le W_{\max}$, 一次行程即可, 不构成多行程问题 |
| `invalid_unreachable/` | `walled_off.txt` | 收集点被障碍包围, BFS 距离 = ∞ |
| `invalid_unreachable/` | `s_blocked.txt` | $S$ 被相邻障碍封死 |
| `invalid_weight/` | `weight_zero.txt` | $w_i = 0$, 越出 $[1, 3]$ |
| `invalid_weight/` | `weight_too_large.txt` | $w_i = 4$, 越出 $[1, 3]$ |
| `invalid_duplicate/` | `s_eq_t.txt` | $S = T$, 起终点重合 |
| `invalid_duplicate/` | `dup_collect.txt` | 两个收集点坐标完全重复 |

## 解析阶段硬错误 (status = error)

只有解析期就能识别的格式问题才会返回 `error`。

| 子目录 | 用例 | 触发的检查 |
|---|---|---|
| `invalid_format/` | `k_too_large.txt` | 收集点数 9 > 上限 8 |
| `invalid_format/` | `bad_char.txt` | 地图含非法字符 `X` (仅允许 `.` 与 `#`) |
| `invalid_format/` | `row_length_mismatch.txt` | 第 0 行长度 4 ≠ 声明列数 3 |

## 使用方式

```bash
# 单个样例
build/solver.exe data/sample_library/basic/empty_grid.txt

# JSON 输出
build/solver.exe data/sample_library/basic/empty_grid.txt --json

# 跑全库自检 (20/20 PASS)
python tests/verify_sample_library.py
```
