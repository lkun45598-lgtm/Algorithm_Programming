#pragma once
// dual.h —— 双车协同求解器(加分项)
// 思路: 共享 S/T 起终点, 枚举 2^N 种"哪些点归车 1, 哪些归车 2"的二分划分,
//       对每个划分,两车分别用单车 DP/贪心 求解其子集, 总距离 = 两车距离之和取 min.

#include "types.h"
#include "solver_common.h"

namespace gc {

enum class DualBackend { Dp, Greedy };

Solution solve_dual(const Grid& g, const KeyPoints& kp,
                    const DistanceMatrix& dm, DualBackend backend);

} // namespace gc
