// dp.cpp —— 动态规划求解器实现 (两层 DP + singleCost 表导出)
#include "dp.h"

#include <algorithm>
#include <chrono>
#include <limits>
#include <vector>

namespace gc {

namespace {

constexpr int INF = std::numeric_limits<int>::max() / 4;

// 子集 TSP: tsp[mask][i] = depot 出发, 访问 mask 全部点, 以 i 结尾的最小代价.
void tsp_from_depot(const DistanceMatrix& dm, int N, int depotIdx,
                    std::vector<std::vector<int>>& tsp) {
    int full = 1 << N;
    tsp.assign(full, std::vector<int>(N, INF));
    for (int i = 0; i < N; ++i) {
        int d = dm.dist[depotIdx][IDX_P(i)];
        if (d >= 0) tsp[1 << i][i] = d;
    }
    for (int mask = 1; mask < full; ++mask) {
        for (int last = 0; last < N; ++last) {
            if (!(mask & (1 << last))) continue;
            if (tsp[mask][last] >= INF) continue;
            int curCost = tsp[mask][last];
            for (int nxt = 0; nxt < N; ++nxt) {
                if (mask & (1 << nxt)) continue;
                int e = dm.dist[IDX_P(last)][IDX_P(nxt)];
                if (e < 0) continue;
                int newMask = mask | (1 << nxt);
                int cand = curCost + e;
                if (cand < tsp[newMask][nxt]) tsp[newMask][nxt] = cand;
            }
        }
    }
}

// 由 tsp 表得到 "走完 mask 并回到 T 的最小代价" 与对应 lastIdx.
void compute_trip_costs(const std::vector<std::vector<int>>& tsp,
                        const DistanceMatrix& dm, int N,
                        std::vector<int>& outCost, std::vector<int>& outLast) {
    int full = 1 << N;
    outCost.assign(full, INF);
    outLast.assign(full, -1);
    for (int mask = 1; mask < full; ++mask) {
        for (int last = 0; last < N; ++last) {
            if (!(mask & (1 << last))) continue;
            if (tsp[mask][last] >= INF) continue;
            int back = dm.dist[IDX_P(last)][IDX_T];
            if (back < 0) continue;
            int total = tsp[mask][last] + back;
            if (total < outCost[mask]) {
                outCost[mask] = total;
                outLast[mask] = last;
            }
        }
    }
}

std::vector<int> compute_weights(const KeyPoints& kp) {
    int N = kp.N();
    std::vector<int> sw(1 << N, 0);
    for (int mask = 1; mask < (1 << N); ++mask) {
        int lb = mask & -mask;
        int i  = __builtin_ctz(lb);
        sw[mask] = sw[mask ^ lb] + kp.weights[i];
    }
    return sw;
}

// 从 tsp 表回溯 mask 内访问顺序 (以 last 结尾).
std::vector<int> recover_order(const std::vector<std::vector<int>>& tsp,
                               const DistanceMatrix& dm, int N,
                               int mask, int last) {
    std::vector<int> order;
    int curMask = mask, curLast = last;
    order.push_back(curLast);
    while (__builtin_popcount(curMask) > 1) {
        int prevMask = curMask ^ (1 << curLast);
        int targetCost = tsp[curMask][curLast];
        int found = -1;
        for (int p = 0; p < N; ++p) {
            if (!(prevMask & (1 << p))) continue;
            int e = dm.dist[IDX_P(p)][IDX_P(curLast)];
            if (e < 0) continue;
            if (tsp[prevMask][p] != INF && tsp[prevMask][p] + e == targetCost) {
                found = p; break;
            }
        }
        if (found < 0) break;
        curLast = found;
        curMask = prevMask;
        order.push_back(curLast);
    }
    std::reverse(order.begin(), order.end());
    return order;
}

} // anon

// ===================== compute_dp_context =====================

DpContext compute_dp_context(const KeyPoints& kp,
                             const DistanceMatrix& dm,
                             DpMode mode) {
    DpContext ctx;
    ctx.N = kp.N();
    ctx.mode = mode;
    int N = ctx.N;
    int full = 1 << N;

    // 1) 子集 TSP (S 与 T 起点)
    tsp_from_depot(dm, N, IDX_S, ctx.tspS);
    tsp_from_depot(dm, N, IDX_T, ctx.tspT);

    // 2) firstCost / laterCost
    compute_trip_costs(ctx.tspS, dm, N, ctx.firstCost, ctx.firstLast);
    compute_trip_costs(ctx.tspT, dm, N, ctx.laterCost, ctx.laterLast);

    // 3) 容量约束: 重量超限的 mask 直接置 INF
    auto sw = compute_weights(kp);
    for (int mask = 1; mask < full; ++mask) {
        if (sw[mask] > kp.wMax) {
            ctx.firstCost[mask] = INF;
            ctx.laterCost[mask] = INF;
        }
    }

    // 4) 划分 DP: G[mask]
    ctx.G.assign(full, INF);
    ctx.pickG.assign(full, 0);
    ctx.G[0] = 0;
    for (int mask = 1; mask < full; ++mask) {
        if (mode == DpMode::Standard) {
            for (int Q = mask; Q > 0; Q = (Q - 1) & mask) {
                if (ctx.laterCost[Q] >= INF) continue;
                int rest = mask ^ Q;
                if (ctx.G[rest] >= INF) continue;
                int cand = ctx.laterCost[Q] + ctx.G[rest];
                if (cand < ctx.G[mask]) {
                    ctx.G[mask] = cand;
                    ctx.pickG[mask] = Q;
                }
            }
        } else {
            int pivot = mask & -mask;
            int rest_of_mask = mask ^ pivot;
            int R = rest_of_mask;
            while (true) {
                int Q = pivot | R;
                if (ctx.laterCost[Q] < INF) {
                    int leftover = mask ^ Q;
                    if (ctx.G[leftover] < INF) {
                        int cand = ctx.laterCost[Q] + ctx.G[leftover];
                        if (cand < ctx.G[mask]) {
                            ctx.G[mask] = cand;
                            ctx.pickG[mask] = Q;
                        }
                    }
                }
                if (R == 0) break;
                R = (R - 1) & rest_of_mask;
            }
        }
    }

    // 5) singleCost[mask]: 对所有 mask 求"单车从 S 出发收完 mask"的最优代价.
    //    singleCost[mask] = min_{Q1 ⊆ mask, Q1≠∅} firstCost[Q1] + G[mask⊕Q1]
    //    一次性 O(3^N) 算出所有 mask, 直接复用 firstCost/G 表, 不重建子距离矩阵.
    ctx.singleCost.assign(full, INF);
    ctx.bestQ1.assign(full, 0);
    ctx.singleCost[0] = 0;   // 空集: 不出动, 代价 0
    for (int mask = 1; mask < full; ++mask) {
        for (int Q = mask; Q > 0; Q = (Q - 1) & mask) {
            if (ctx.firstCost[Q] >= INF) continue;
            int leftover = mask ^ Q;
            if (ctx.G[leftover] >= INF) continue;
            int cand = ctx.firstCost[Q] + ctx.G[leftover];
            if (cand < ctx.singleCost[mask]) {
                ctx.singleCost[mask] = cand;
                ctx.bestQ1[mask] = Q;
            }
        }
    }
    return ctx;
}

// ===================== reconstruct_single_solution =====================

Solution reconstruct_single_solution(const DpContext& ctx,
                                      const KeyPoints& kp,
                                      const DistanceMatrix& dm,
                                      int mask,
                                      const char* algorithmTag) {
    Solution sol;
    sol.algorithm = algorithmTag ? algorithmTag : "";
    int N = ctx.N;

    if (mask == 0) {
        sol.ok = true;
        sol.totalDistance = 0;
        return sol;
    }
    if (mask < 0 || mask >= (1 << N) || ctx.singleCost[mask] >= INF) {
        sol.ok = false;
        sol.status = "infeasible";
        sol.error = "DP 在该 mask 下无可行解";
        return sol;
    }

    auto build_trip = [&](int tripMask, int depotIdx, bool isFirst) {
        Trip trip;
        int last = isFirst ? ctx.firstLast[tripMask] : ctx.laterLast[tripMask];
        const auto& tspRef = isFirst ? ctx.tspS : ctx.tspT;
        auto order = recover_order(tspRef, dm, N, tripMask, last);
        trip.pointIndices = order;
        trip.load = 0;
        for (int idx : order) trip.load += kp.weights[idx];
        std::vector<int> keySeq;
        keySeq.push_back(depotIdx);
        for (int idx : order) keySeq.push_back(IDX_P(idx));
        keySeq.push_back(IDX_T);
        trip.fullPath = expand_trip_path(dm, keySeq);
        trip.distance = static_cast<int>(trip.fullPath.size()) - 1;
        return trip;
    };

    int Q1 = ctx.bestQ1[mask];
    sol.trips.push_back(build_trip(Q1, IDX_S, true));
    int rem = mask ^ Q1;
    while (rem != 0) {
        int Q = ctx.pickG[rem];
        sol.trips.push_back(build_trip(Q, IDX_T, false));
        rem ^= Q;
    }
    sol.totalDistance = ctx.singleCost[mask];
    sol.ok = true;
    return sol;
}

// ===================== solve_dp 顶层 =====================

Solution solve_dp(const Grid& /*g*/, const KeyPoints& kp,
                  const DistanceMatrix& dm, DpMode mode) {
    using clock = std::chrono::high_resolution_clock;
    auto t0 = clock::now();

    DpContext ctx = compute_dp_context(kp, dm, mode);
    int full = (1 << ctx.N) - 1;
    const char* tag = (mode == DpMode::Standard ? "dp" : "dp_dc");
    Solution sol = reconstruct_single_solution(ctx, kp, dm, full, tag);
    sol.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
    return sol;
}

} // namespace gc
