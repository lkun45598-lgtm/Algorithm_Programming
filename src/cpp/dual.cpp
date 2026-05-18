// dual.cpp —— 双车协同求解器实现
// 共享 S/T, 枚举 2^N 个二分划分: mask1 表示车 1 应收集的点, mask2 = full ^ mask1.
// 对每个划分,分别构造子问题(子 KeyPoints + 子 DistanceMatrix),复用单车 solver.

#include "dual.h"
#include "dp.h"
#include "greedy.h"

#include <chrono>
#include <limits>

namespace gc {

namespace {

struct SubProblem {
    KeyPoints kp;
    std::vector<int> localToGlobal;   // 子问题点编号 -> 原始全局点编号
};

// 从全局 KeyPoints 中按 mask 抽取子集。子求解器内部会重新编号，
// 因此必须保留 localToGlobal 映射，输出前再把 POINTS 还原为原始编号。
SubProblem sub_problem(const KeyPoints& kp, int mask) {
    SubProblem sp;
    sp.kp.parking = kp.parking;
    sp.kp.plant   = kp.plant;
    sp.kp.wMax    = kp.wMax;
    for (int i = 0; i < kp.N(); ++i) {
        if (mask & (1 << i)) {
            sp.kp.collects.push_back(kp.collects[i]);
            sp.kp.weights .push_back(kp.weights[i]);
            sp.localToGlobal.push_back(i);
        }
    }
    return sp;
}

void remap_trip_indices(Solution& s, const std::vector<int>& localToGlobal) {
    for (Trip& tr : s.trips) {
        for (int& idx : tr.pointIndices) {
            if (0 <= idx && idx < static_cast<int>(localToGlobal.size())) {
                idx = localToGlobal[idx];
            }
        }
    }
}

} // anon

Solution solve_dual(const Grid& g, const KeyPoints& kp,
                    const DistanceMatrix& /*dm*/, DualBackend backend) {
    using clock = std::chrono::high_resolution_clock;
    auto t0 = clock::now();
    int N = kp.N();
    int full = (1 << N) - 1;

    Solution best;
    best.algorithm = (backend == DualBackend::Dp ? "multi_dp" : "multi_greedy");
    int bestTotal = std::numeric_limits<int>::max();
    Solution bestS1, bestS2;

    // 子求解器: 重新构造 sub-DistanceMatrix(子问题的收集点索引与全局不同)
    auto runSub = [&](const KeyPoints& sk) -> Solution {
        if (sk.N() == 0) {
            Solution s; s.ok = true; s.totalDistance = 0;
            return s;
        }
        DistanceMatrix sdm = build_distance_matrix(g, sk);
        if (backend == DualBackend::Dp) {
            return solve_dp(g, sk, sdm, DpMode::Standard);
        } else {
            return solve_greedy(g, sk, sdm);
        }
    };

    // 枚举 mask1, mask2 = full ^ mask1. 允许空划分(一辆车不动 == 退化为单车).
    for (int mask1 = 0; mask1 <= full; ++mask1) {
        int mask2 = full ^ mask1;
        auto sp1 = sub_problem(kp, mask1);
        auto sp2 = sub_problem(kp, mask2);

        // 子问题如果 sum(w) <= W_max 是允许的(单 trip 一次解决);
        // 单车 solver 可自然退化为一次首程。
        Solution s1 = runSub(sp1.kp);
        if (!s1.ok) continue;
        remap_trip_indices(s1, sp1.localToGlobal);
        Solution s2 = runSub(sp2.kp);
        if (!s2.ok) continue;
        remap_trip_indices(s2, sp2.localToGlobal);
        int total = s1.totalDistance + s2.totalDistance;
        if (total < bestTotal) {
            bestTotal = total; bestS1 = s1; bestS2 = s2;
        }
    }

    if (bestTotal >= std::numeric_limits<int>::max() / 2) {
        best.ok = false; best.status = "infeasible";
        best.error = "双车: 找不到可行方案";
    } else {
        best.ok = true;
        best.totalDistance = bestTotal;
        best.vehicleTrips.push_back(bestS1.trips);
        best.vehicleTrips.push_back(bestS2.trips);
    }
    best.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
    return best;
}

} // namespace gc
