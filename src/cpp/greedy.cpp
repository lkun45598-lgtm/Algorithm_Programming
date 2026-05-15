// greedy.cpp —— 最近邻贪心求解器实现
#include "greedy.h"

#include <chrono>
#include <limits>

namespace gc {

Solution solve_greedy(const Grid& /*g*/, const KeyPoints& kp,
                      const DistanceMatrix& dm) {
    using clock = std::chrono::high_resolution_clock;
    auto t0 = clock::now();

    Solution sol; sol.algorithm = "greedy";
    int N = kp.N();
    std::vector<bool> visited(N, false);
    int curIdx = IDX_S;          // 起点 = S
    int load = 0;
    int totalDist = 0;
    Trip cur;

    // 记录当前 trip 的关键点序列
    std::vector<int> keySeq;
    keySeq.push_back(curIdx);

    int remaining = N;
    while (remaining > 0) {
        // 找最近可装载点
        int best = -1, bestD = std::numeric_limits<int>::max();
        for (int i = 0; i < N; ++i) {
            if (visited[i]) continue;
            if (load + kp.weights[i] > kp.wMax) continue;
            int d = dm.dist[curIdx][IDX_P(i)];
            if (d < 0) continue;
            if (d < bestD) { bestD = d; best = i; }
        }
        if (best < 0) {
            // 没有可装载点 → 去 T 卸货, 开启新 trip
            int back = dm.dist[curIdx][IDX_T];
            if (back < 0) {
                sol.ok = false; sol.status = "infeasible";
                sol.error = "贪心:无法到达 T";
                sol.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
                return sol;
            }
            keySeq.push_back(IDX_T);
            cur.fullPath = expand_trip_path(dm, keySeq);
            cur.distance = static_cast<int>(cur.fullPath.size()) - 1;
            cur.load = load;
            sol.trips.push_back(cur);
            totalDist += cur.distance;
            // 重置
            cur = Trip{};
            load = 0;
            curIdx = IDX_T;
            keySeq.clear(); keySeq.push_back(curIdx);
            continue;
        }
        // 访问 best
        visited[best] = true;
        load += kp.weights[best];
        curIdx = IDX_P(best);
        keySeq.push_back(curIdx);
        cur.pointIndices.push_back(best);
        --remaining;
    }
    // 收尾: 最后一个 trip 也要回到 T
    if (!cur.pointIndices.empty()) {
        int back = dm.dist[curIdx][IDX_T];
        if (back < 0) {
            sol.ok = false; sol.status = "infeasible";
            sol.error = "贪心:最后无法回到 T";
            sol.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
            return sol;
        }
        keySeq.push_back(IDX_T);
        cur.fullPath = expand_trip_path(dm, keySeq);
        cur.distance = static_cast<int>(cur.fullPath.size()) - 1;
        cur.load = load;
        sol.trips.push_back(cur);
        totalDist += cur.distance;
    }

    sol.totalDistance = totalDist;
    sol.ok = true;
    sol.runtimeMs = std::chrono::duration<double, std::milli>(clock::now() - t0).count();
    return sol;
}

} // namespace gc
