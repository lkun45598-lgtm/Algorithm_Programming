// solver_common.cpp —— 距离矩阵构建 + 路径拼接
//
// 实现说明: 关键点距离矩阵的构造严格做到每个源点只调用一次 BFS。
// 同次 BFS 的前驱表被用来 O(path_length) 回溯到该源点出发的所有目标点路径,
// 故总复杂度为 O(K * M*L),而非"每对都重新 BFS"的 O(K^2 * M*L)。
#include "solver_common.h"

namespace gc {

DistanceMatrix build_distance_matrix(const Grid& g, const KeyPoints& kp) {
    DistanceMatrix dm;
    int N = kp.N();
    dm.K = N + 2;

    std::vector<Point> idxToPoint(dm.K);
    idxToPoint[IDX_S] = kp.parking;
    idxToPoint[IDX_T] = kp.plant;
    for (int i = 0; i < N; ++i) idxToPoint[IDX_P(i)] = kp.collects[i];

    dm.dist.assign(dm.K, std::vector<int>(dm.K, -1));
    dm.path.assign(dm.K, std::vector<std::vector<Point>>(dm.K));

    // 每个源点只 BFS 一次, 然后从同一 prev 表回溯所有目标点路径.
    std::vector<std::vector<int>>   dist_field;
    std::vector<std::vector<Point>> prev_field;

    for (int u = 0; u < dm.K; ++u) {
        g.bfsWithPrev(idxToPoint[u], dist_field, prev_field);

        for (int v = 0; v < dm.K; ++v) {
            const Point& pv = idxToPoint[v];
            dm.dist[u][v] = dist_field[pv.r][pv.c];

            if (u == v) {
                dm.path[u][v] = { idxToPoint[u] };
            } else if (dm.dist[u][v] >= 0) {
                // O(path_length) 回溯, 不再发起 BFS
                dm.path[u][v] = g.reconstructPath(idxToPoint[u], pv, prev_field);
            }
        }
    }
    return dm;
}

std::vector<Point> expand_trip_path(const DistanceMatrix& dm,
                                    const std::vector<int>& seq) {
    std::vector<Point> full;
    if (seq.empty()) return full;
    for (size_t i = 0; i + 1 < seq.size(); ++i) {
        const auto& seg = dm.path[seq[i]][seq[i+1]];
        if (seg.empty()) return {};
        size_t start = (i == 0) ? 0 : 1;
        for (size_t k = start; k < seg.size(); ++k) full.push_back(seg[k]);
    }
    return full;
}

} // namespace gc
