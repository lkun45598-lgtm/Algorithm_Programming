// dual.cpp —— 双车协同求解器实现
//
// DP 后端: 调用 dp 模块的 compute_dp_context 一次, 直接得到 [n] 所有
// 子集 mask 的单车最优代价表 singleCost[mask]; 双车答案归约为
//     min_{A ⊆ [n]} singleCost[A] + singleCost[[n] \ A]
// 通过强制点 0 ∈ A (或 A = 0 退化为单车) 消除车号对称, 枚举量从 2^N
// 减为 1 + 2^(N-1). 整个过程不再重建子距离矩阵, 不再重跑子 DP.
//
// Greedy 后端: 因贪心不接受 mask 输入, 仍走原始 "枚举划分 + 构造子
// KeyPoints + 子 BFS + solve_greedy" 路径, 并把子求解器返回的局部点
// 编号映射回全局编号(避免 GUI / 报告对不上号).

#include "dual.h"
#include "dp.h"
#include "greedy.h"

#include <chrono>
#include <limits>

namespace gc {

namespace {

// ---- Greedy 后端专用辅助 (不影响 DP 后端) ----
struct SubProblem {
    KeyPoints kp;
    std::vector<int> localToGlobal;
};

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

// ===================== DP 后端: 高效路径 =====================
Solution solve_dual_dp(const KeyPoints& kp, const DistanceMatrix& dm) {
    using clock = std::chrono::high_resolution_clock;
    auto t0 = clock::now();

    Solution result;
    result.algorithm = "multi_dp";
    int N = kp.N();
    int full = (1 << N) - 1;

    // 单次 DP 计算 → singleCost[mask] for all mask ⊆ [n].
    DpContext ctx = compute_dp_context(kp, dm, DpMode::Standard);

    constexpr int INF_HALF = std::numeric_limits<int>::max() / 4;
    int bestTotal = INF_HALF;
    int bestM1 = -1;

    // 候选 1: mask1 = 0, 即车 1 不出动 (退化为单车情况).
    if (ctx.singleCost[full] < INF_HALF) {
        bestTotal = ctx.singleCost[full];
        bestM1 = 0;
    }

    // 候选 2: 0 ∈ mask1 (对称性消除 — (mask1, mask2) 与 (mask2, mask1) 等价,
    //         我们规定较低位元素属于 mask1, 这样每个无序划分恰被枚举一次).
    if (N > 0) {
        for (int mask1 = 1; mask1 <= full; ++mask1) {
            if (!(mask1 & 1)) continue;            // 必须包含点 0
            int mask2 = full ^ mask1;
            int c1 = ctx.singleCost[mask1];
            int c2 = ctx.singleCost[mask2];
            if (c1 >= INF_HALF || c2 >= INF_HALF) continue;
            int total = c1 + c2;
            if (total < bestTotal) { bestTotal = total; bestM1 = mask1; }
        }
    }

    if (bestM1 < 0 || bestTotal >= INF_HALF) {
        result.ok = false; result.status = "infeasible";
        result.error = "双车 DP: 容量与连通约束下无可行方案";
        result.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
        return result;
    }

    int bestM2 = full ^ bestM1;
    Solution s1 = reconstruct_single_solution(ctx, kp, dm, bestM1, "multi_dp");
    Solution s2 = reconstruct_single_solution(ctx, kp, dm, bestM2, "multi_dp");

    result.ok = true;
    result.totalDistance = bestTotal;
    result.vehicleTrips.push_back(s1.trips);
    result.vehicleTrips.push_back(s2.trips);
    result.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
    return result;
}

// ===================== Greedy 后端: 经典枚举路径 =====================
Solution solve_dual_greedy(const Grid& g, const KeyPoints& kp) {
    using clock = std::chrono::high_resolution_clock;
    auto t0 = clock::now();

    Solution result;
    result.algorithm = "multi_greedy";
    int N = kp.N();
    int full = (1 << N) - 1;

    constexpr int INF_HALF = std::numeric_limits<int>::max() / 4;
    int bestTotal = INF_HALF;
    Solution bestS1, bestS2;

    // 同样使用对称性消除 + mask1=0 退化情形.
    auto try_partition = [&](int mask1) -> bool {
        int mask2 = full ^ mask1;
        SubProblem sp1 = sub_problem(kp, mask1);
        SubProblem sp2 = sub_problem(kp, mask2);

        Solution s1, s2;
        if (sp1.kp.N() == 0) { s1.ok = true; s1.totalDistance = 0; }
        else {
            DistanceMatrix sdm1 = build_distance_matrix(g, sp1.kp);
            s1 = solve_greedy(g, sp1.kp, sdm1);
            if (!s1.ok) return false;
            remap_trip_indices(s1, sp1.localToGlobal);
        }
        if (sp2.kp.N() == 0) { s2.ok = true; s2.totalDistance = 0; }
        else {
            DistanceMatrix sdm2 = build_distance_matrix(g, sp2.kp);
            s2 = solve_greedy(g, sp2.kp, sdm2);
            if (!s2.ok) return false;
            remap_trip_indices(s2, sp2.localToGlobal);
        }

        int total = s1.totalDistance + s2.totalDistance;
        if (total < bestTotal) { bestTotal = total; bestS1 = s1; bestS2 = s2; }
        return true;
    };

    try_partition(0);
    if (N > 0) {
        for (int mask1 = 1; mask1 <= full; ++mask1) {
            if (!(mask1 & 1)) continue;
            try_partition(mask1);
        }
    }

    if (bestTotal >= INF_HALF) {
        result.ok = false; result.status = "infeasible";
        result.error = "双车 Greedy: 找不到可行方案";
        result.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
        return result;
    }

    result.ok = true;
    result.totalDistance = bestTotal;
    result.vehicleTrips.push_back(bestS1.trips);
    result.vehicleTrips.push_back(bestS2.trips);
    result.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
    return result;
}

} // anon

// ===================== solve_dual 顶层 =====================
Solution solve_dual(const Grid& g, const KeyPoints& kp,
                    const DistanceMatrix& dm, DualBackend backend) {
    if (backend == DualBackend::Dp)     return solve_dual_dp(kp, dm);
    if (backend == DualBackend::Greedy) return solve_dual_greedy(g, kp);
    Solution err;
    err.ok = false; err.status = "error";
    err.error = "未知双车后端";
    return err;
}

} // namespace gc
