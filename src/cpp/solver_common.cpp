// solver_common.cpp —— 距离矩阵构建 + 路径拼接
#include "solver_common.h"

namespace gc {

DistanceMatrix build_distance_matrix(const Grid& g, const KeyPoints& kp) {
    DistanceMatrix dm;
    int N = kp.N();
    dm.K = N + 2;

    // 索引 -> 网格坐标 的映射
    std::vector<Point> idxToPoint(dm.K);
    idxToPoint[IDX_S] = kp.parking;
    idxToPoint[IDX_T] = kp.plant;
    for (int i = 0; i < N; ++i) idxToPoint[IDX_P(i)] = kp.collects[i];

    dm.dist.assign(dm.K, std::vector<int>(dm.K, -1));
    dm.path.assign(dm.K, std::vector<std::vector<Point>>(dm.K));

    for (int u = 0; u < dm.K; ++u) {
        auto dfield = g.bfsDistances(idxToPoint[u]);
        for (int v = 0; v < dm.K; ++v) {
            dm.dist[u][v] = dfield[idxToPoint[v].r][idxToPoint[v].c];
            if (u != v && dm.dist[u][v] >= 0) {
                dm.path[u][v] = g.shortestPath(idxToPoint[u], idxToPoint[v]);
            } else if (u == v) {
                dm.path[u][v] = { idxToPoint[u] };
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
        // 第一段从头取, 后续段去掉重复的衔接点(seg 的第一个点等于上一段的末点)
        size_t start = (i == 0) ? 0 : 1;
        for (size_t k = start; k < seg.size(); ++k) full.push_back(seg[k]);
    }
    return full;
}

} // namespace gc
