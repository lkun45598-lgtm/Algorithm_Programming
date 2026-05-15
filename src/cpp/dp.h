#pragma once
// dp.h —— 动态规划求解器(子集 TSP + 划分 DP)
// 提供两种枚举模式: 标准枚举(经典 O(3^N) 子集枚举) 与 分治变体(固定最低位).

#include "types.h"
#include "solver_common.h"

namespace gc {

// 模式: 标准枚举 (O(3^N)) 或 分治法 (子集枚举优化, 仍 O(3^N) 但常数更小)
enum class DpMode { Standard, DivideConquer };

Solution solve_dp(const Grid& g, const KeyPoints& kp,
                  const DistanceMatrix& dm, DpMode mode);

} // namespace gc
