// feasibility.cpp —— 输入合法性检查实现
#include "feasibility.h"

#include <algorithm>
#include <numeric>
#include <sstream>
#include <set>

namespace gc {

FeasibilityResult check_feasibility(const Grid& g, const KeyPoints& kp) {
    FeasibilityResult res;

    // (1) 关键点必须落在可通行格
    auto checkCell = [&](const Point& p, const std::string& name) -> bool {
        if (!g.walkable(p)) {
            std::ostringstream os;
            os << name << " 落在障碍或越界 (" << p.r << "," << p.c << ")";
            res.ok = false; res.reason = os.str();
            return false;
        }
        return true;
    };
    if (!checkCell(kp.parking, "停车场 S")) return res;
    if (!checkCell(kp.plant,   "处理厂 T")) return res;
    for (int i = 0; i < kp.N(); ++i) {
        if (!checkCell(kp.collects[i], "收集点 P" + std::to_string(i))) return res;
    }
    if (kp.N() == 0) {
        res.ok = false; res.reason = "至少需要一个收集点";
        return res;
    }
    if (kp.parking == kp.plant) {
        res.ok = false; res.reason = "停车场 S 与处理厂 T 不能重合";
        return res;
    }
    std::set<Point> seen;
    seen.insert(kp.parking);
    seen.insert(kp.plant);
    for (int i = 0; i < kp.N(); ++i) {
        if (!seen.insert(kp.collects[i]).second) {
            res.ok = false;
            res.reason = "关键点坐标重复: P" + std::to_string(i);
            return res;
        }
    }

    // (2) 重量约束
    for (int i = 0; i < kp.N(); ++i) {
        if (kp.weights[i] < 1 || kp.weights[i] > 3) {
            res.ok = false;
            res.reason = "收集点 P" + std::to_string(i) + " 的重量不在 1..3 范围内";
            return res;
        }
    }
    int maxW = *std::max_element(kp.weights.begin(), kp.weights.end());
    int sumW = std::accumulate(kp.weights.begin(), kp.weights.end(), 0);
    if (kp.wMax < maxW) {
        res.ok = false;
        res.reason = "W_max 小于单个最大收集点重量 ("
                     + std::to_string(kp.wMax) + " < " + std::to_string(maxW) + ")";
        return res;
    }
    if (sumW <= kp.wMax) {
        res.ok = false;
        res.reason = "总重量 ≤ W_max, 一次行程即可完成, 不构成多行程问题";
        return res;
    }

    // (3) 互相可达性 (用 S 出发的 BFS 距离表检测)
    auto distS = g.bfsDistances(kp.parking);
    auto checkReach = [&](const Point& p, const std::string& name) -> bool {
        if (distS[p.r][p.c] == -1) {
            res.ok = false; res.reason = "关键点 " + name + " 与停车场 S 不可达";
            return false;
        }
        return true;
    };
    if (!checkReach(kp.plant, "处理厂 T")) return res;
    for (int i = 0; i < kp.N(); ++i) {
        if (!checkReach(kp.collects[i], "P" + std::to_string(i))) return res;
    }
    return res;
}

} // namespace gc
