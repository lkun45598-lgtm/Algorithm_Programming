// dp.cpp —— 动态规划求解器实现
// 算法分两层:
//   1. 子集 TSP: tsp[mask][last] = 从 depot 出发,访问 mask 中所有点,以 last 结尾的最小代价
//   2. 划分 DP: G[mask] = 把 mask 切成若干 later-trip 的最小总代价; 首发 trip 单独枚举.
// 标准模式枚举 mask 的所有非空子集(经典 O(3^N) 技巧); 分治变体固定最低位,递归枚举其余位.

#include "dp.h"

#include <algorithm>
#include <chrono>
#include <limits>
#include <vector>

namespace gc {

namespace {

constexpr int INF = std::numeric_limits<int>::max() / 4;

// tsp[mask][i] = 从 depot 出发,访问 mask 中所有收集点,以收集点 i 结束的最小代价
// depotIdx: 关键点全局索引 (IDX_S 或 IDX_T)
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

struct TripCost {
    int cost{INF};
    int lastIdx{-1};   // 该 trip 的最后一个收集点(回溯用)
};

// trip_cost[mask] = 从 depot 出发, 走完 mask 中所有点, 回到 T 的最小距离
void compute_trip_costs(const std::vector<std::vector<int>>& tsp,
                        const DistanceMatrix& dm, int N,
                        std::vector<TripCost>& out) {
    int full = 1 << N;
    out.assign(full, TripCost{});
    for (int mask = 1; mask < full; ++mask) {
        for (int last = 0; last < N; ++last) {
            if (!(mask & (1 << last))) continue;
            if (tsp[mask][last] >= INF) continue;
            int back = dm.dist[IDX_P(last)][IDX_T];
            if (back < 0) continue;
            int total = tsp[mask][last] + back;
            if (total < out[mask].cost) {
                out[mask].cost = total;
                out[mask].lastIdx = last;
            }
        }
    }
}

// 给定 mask 和该 trip 的最后一个点, 回溯访问顺序
std::vector<int> recover_order(const std::vector<std::vector<int>>& tsp,
                               const DistanceMatrix& dm, int N,
                               int mask, int last, int /*depotIdx*/) {
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
        if (found < 0) break;   // 理论上不会发生
        curLast = found;
        curMask = prevMask;
        order.push_back(curLast);
    }
    std::reverse(order.begin(), order.end());
    return order;
}

// 计算每个 mask 的总重量
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

} // anon

// --------- 主求解器 ---------
Solution solve_dp(const Grid& /*g*/, const KeyPoints& kp,
                  const DistanceMatrix& dm, DpMode mode) {
    using clock = std::chrono::high_resolution_clock;
    auto t0 = clock::now();

    Solution sol;
    sol.algorithm = (mode == DpMode::Standard ? "dp" : "dp_dc");
    int N = kp.N();
    int full = (1 << N) - 1;

    // 1) 子集 TSP (S 出发 / T 出发)
    std::vector<std::vector<int>> tspS, tspT;
    tsp_from_depot(dm, N, IDX_S, tspS);
    tsp_from_depot(dm, N, IDX_T, tspT);

    // 2) trip_cost[mask]: 走完 mask 并回到 T 的最小代价
    std::vector<TripCost> firstCost, laterCost;
    compute_trip_costs(tspS, dm, N, firstCost);
    compute_trip_costs(tspT, dm, N, laterCost);

    // 3) 重量约束: 不满足载重的 mask 直接置 INF
    auto sw = compute_weights(kp);
    for (int mask = 1; mask <= full; ++mask) {
        if (sw[mask] > kp.wMax) {
            firstCost[mask].cost = INF;
            laterCost[mask].cost = INF;
        }
    }

    // 4) 划分 DP: G[mask] = 把 mask 拆成若干 later-trip 的最优代价
    std::vector<int> G(full + 1, INF);
    std::vector<int> pick(full + 1, 0);  // 回溯: 第一个 later-trip 的子集
    G[0] = 0;
    for (int mask = 1; mask <= full; ++mask) {
        if (mode == DpMode::Standard) {
            // 标准枚举: 枚举 mask 所有非空子集 Q
            for (int Q = mask; Q > 0; Q = (Q - 1) & mask) {
                if (laterCost[Q].cost >= INF) continue;
                int rest = mask ^ Q;
                if (G[rest] >= INF) continue;
                int cand = laterCost[Q].cost + G[rest];
                if (cand < G[mask]) { G[mask] = cand; pick[mask] = Q; }
            }
        } else {
            // 分治变体: 固定 mask 的最低位必属于第一行程 Q
            int pivot = mask & -mask;
            int rest_of_mask = mask ^ pivot;
            int R = rest_of_mask;
            while (true) {
                int Q = pivot | R;
                if (laterCost[Q].cost < INF) {
                    int leftover = mask ^ Q;
                    if (G[leftover] < INF) {
                        int cand = laterCost[Q].cost + G[leftover];
                        if (cand < G[mask]) { G[mask] = cand; pick[mask] = Q; }
                    }
                }
                if (R == 0) break;
                R = (R - 1) & rest_of_mask;
            }
        }
    }

    // 5) 首发行程: 枚举首发 trip 的子集 Q1, 剩余用 G[full ^ Q1]
    int bestTotal = INF;
    int bestQ1 = -1;
    for (int Q1 = full; Q1 > 0; Q1 = (Q1 - 1) & full) {
        if (firstCost[Q1].cost >= INF) continue;
        int leftover = full ^ Q1;
        if (G[leftover] >= INF) continue;
        int cand = firstCost[Q1].cost + G[leftover];
        if (cand < bestTotal) { bestTotal = cand; bestQ1 = Q1; }
    }

    if (bestTotal >= INF || bestQ1 < 0) {
        sol.ok = false; sol.status = "infeasible";
        sol.error = "重量/距离约束下没有可行方案";
        sol.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
        return sol;
    }

    // 6) 回溯: 首发 Q1, 然后从 G[mask] 链推得每个后续 trip
    auto build_trip = [&](int mask, int depotIdx, bool isFirst) {
        Trip trip;
        int last = isFirst ? firstCost[mask].lastIdx : laterCost[mask].lastIdx;
        auto& tspRef = isFirst ? tspS : tspT;
        auto order = recover_order(tspRef, dm, N, mask, last, depotIdx);
        trip.pointIndices = order;
        trip.load = 0;
        for (int idx : order) trip.load += kp.weights[idx];
        // 完整路径: depot -> P_{order[0]} -> ... -> P_{last} -> T
        std::vector<int> keySeq;
        keySeq.push_back(depotIdx);
        for (int idx : order) keySeq.push_back(IDX_P(idx));
        keySeq.push_back(IDX_T);
        trip.fullPath = expand_trip_path(dm, keySeq);
        trip.distance = static_cast<int>(trip.fullPath.size()) - 1;
        return trip;
    };

    sol.trips.push_back(build_trip(bestQ1, IDX_S, true));
    int rem = full ^ bestQ1;
    while (rem != 0) {
        int Q = pick[rem];
        sol.trips.push_back(build_trip(Q, IDX_T, false));
        rem ^= Q;
    }

    sol.totalDistance = bestTotal;
    sol.ok = true;
    sol.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
    return sol;
}

} // namespace gc
