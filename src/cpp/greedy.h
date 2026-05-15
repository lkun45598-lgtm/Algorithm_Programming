#pragma once
// greedy.h —— 最近邻贪心求解器
// 策略: 从当前位置出发,选择"未访问且能装下"的最近收集点;
//       若装不下任何点则先去 T 卸货并开启新行程.

#include "types.h"
#include "solver_common.h"

namespace gc {

Solution solve_greedy(const Grid& g, const KeyPoints& kp,
                      const DistanceMatrix& dm);

} // namespace gc
