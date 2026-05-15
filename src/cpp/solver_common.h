#pragma once
// solver_common.h —— 距离矩阵与路径拼接的公共基础设施
// 关键点统一编号: 0 = S, 1 = T, 2..N+1 = 收集点 P0..P_{N-1}
// 所有求解器都基于 DistanceMatrix 工作,完整网格路径通过 expand_trip_path 拼接.

#include "types.h"
#include "grid.h"
#include <vector>

namespace gc {

constexpr int IDX_S = 0;
constexpr int IDX_T = 1;
inline int IDX_P(int i) { return 2 + i; }

// 预计算所有关键点之间的最短距离 (BFS) + 完整路径
struct DistanceMatrix {
    int K{0};                                                 // K = N + 2
    std::vector<std::vector<int>> dist;                       // K x K 距离, 不可达 = -1
    std::vector<std::vector<std::vector<Point>>> path;        // path[u][v] = u→v 完整网格路径
};

DistanceMatrix build_distance_matrix(const Grid& g, const KeyPoints& kp);

// 把若干"关键点索引"序列展开为完整网格路径(拼接时去掉重复衔接点).
// 若任一段不可达,返回空 vector.
std::vector<Point> expand_trip_path(const DistanceMatrix& dm,
                                    const std::vector<int>& keyIdxSeq);

} // namespace gc
