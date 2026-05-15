#pragma once
// feasibility.h —— 输入合法性检查
// 验证: (1) 所有关键点都落在可通行格内
//       (2) 所有关键点之间互相可达
//       (3) W_max >= max(w_i), 且 sum(w_i) > W_max (否则一次行程即可完成)

#include "types.h"
#include "grid.h"
#include <string>

namespace gc {

struct FeasibilityResult {
    bool ok{true};
    std::string reason;
};

// 检查: 关键点全部可达, W_max ≥ max(w_i), sum(w_i) > W_max
FeasibilityResult check_feasibility(const Grid& g, const KeyPoints& kp);

} // namespace gc
