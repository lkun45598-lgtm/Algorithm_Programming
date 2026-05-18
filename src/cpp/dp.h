#pragma once
// dp.h —— 动态规划求解器(子集 TSP + 划分 DP)
// 两种枚举模式: 标准枚举 与 基于 pivot 的对称性消除变体.
// 内部计算结果以 DpContext 暴露, 便于双车场景复用全部 [n] 子集的单车最优代价表
// (避免对每个子问题重建距离矩阵 + 重跑 DP).

#include "types.h"
#include "solver_common.h"
#include <vector>

namespace gc {

enum class DpMode { Standard, DivideConquer };

// 一次完整 DP 计算后所有可重用的中间表.
// 索引: mask 取值 [0, 2^N - 1]; tsp 表 [mask][last_collect_idx].
struct DpContext {
    int N{0};
    DpMode mode{DpMode::Standard};

    // 内层 TSP: 从 S/T 出发, 访问 mask 中所有点, 以收集点 last 结尾的最小代价.
    std::vector<std::vector<int>> tspS;
    std::vector<std::vector<int>> tspT;

    // 单 trip 最优代价 (S→mask→T 与 T→mask→T), 以及取得最优时该 trip 的最后一个点.
    std::vector<int> firstCost;     // 2^N
    std::vector<int> laterCost;     // 2^N
    std::vector<int> firstLast;     // 2^N, INVALID 用 -1
    std::vector<int> laterLast;     // 2^N

    // 划分 DP: G[mask] = 仅用 later-trip 收完 mask 的最优总代价.
    std::vector<int> G;             // 2^N
    std::vector<int> pickG;         // 回溯: G[mask] 取得最优时的第一条 later-trip 子集

    // singleCost[mask] = 单车从 S 出发收完 mask 的最优总代价.
    // bestQ1[mask] = 取得 singleCost[mask] 时的首发 trip 子集.
    // (二者从 firstCost/G/laterCost 派生, 因此调用 dual 时无需重复 BFS / TSP.)
    std::vector<int> singleCost;    // 2^N
    std::vector<int> bestQ1;        // 2^N
};

// 单次 DP 计算, 产出完整 DpContext. mode 仅影响划分 DP 内层子集枚举方式.
DpContext compute_dp_context(const KeyPoints& kp,
                             const DistanceMatrix& dm,
                             DpMode mode);

// 从已计算的 DpContext 中, 给定要单车收完的 mask, 回溯 trips + 路径.
// 若 mask 不可行 (singleCost[mask] >= INF), 返回 ok=false.
// algorithmTag 仅写入返回 Solution.algorithm.
Solution reconstruct_single_solution(const DpContext& ctx,
                                      const KeyPoints& kp,
                                      const DistanceMatrix& dm,
                                      int mask,
                                      const char* algorithmTag);

// 顶层求解器: 兼容旧接口. mode 由参数指定.
Solution solve_dp(const Grid& g, const KeyPoints& kp,
                  const DistanceMatrix& dm, DpMode mode);

} // namespace gc
