#pragma once
// grid.h —— 网格地图 + BFS 最短路计算
// 描述: 提供网格判通行、单源 BFS 距离表、两点最短路径恢复等基础原语。
//       这是后续所有算法 (合法性检查 / DP / 贪心) 的基础设施。

#include "types.h"
#include <string>
#include <vector>

namespace gc {

class Grid {
public:
    int                       rows{0};
    int                       cols{0};
    // 每行长度=cols, 字符 '.' 表示可通行空地, '#' 表示障碍.
    std::vector<std::string>  cells;

    Grid() = default;
    Grid(int r, int c, std::vector<std::string> cs)
        : rows(r), cols(c), cells(std::move(cs)) {}

    // 该格是否可通行(越界视为不可通行)
    bool walkable(int r, int c) const noexcept {
        if (r < 0 || r >= rows || c < 0 || c >= cols) return false;
        return cells[static_cast<size_t>(r)][static_cast<size_t>(c)] != '#';
    }
    bool walkable(const Point& p) const noexcept { return walkable(p.r, p.c); }

    // 从 from 出发的 BFS 距离场. 不可达格子记为 -1.
    std::vector<std::vector<int>> bfsDistances(const Point& from) const;

    // 从 from 出发的 BFS, 同时返回距离场与前驱表 (用于从同一次 BFS 回溯到
    // 多个目标点的路径, 避免重复 BFS).
    // - dist: 不可达 = -1
    // - prev: 不可达 = {-1, -1}; from 本身 = {-1, -1}
    void bfsWithPrev(const Point& from,
                     std::vector<std::vector<int>>& dist,
                     std::vector<std::vector<Point>>& prev) const;

    // 给定 from 的前驱表与目标点 to, 在 O(path_length) 内回溯路径.
    std::vector<Point> reconstructPath(const Point& from, const Point& to,
                                       const std::vector<std::vector<Point>>& prev) const;

    // 从 from 到 to 的最短路径(包含起止两点). 若不可达则返回空向量.
    // (便利接口: 内部调用 bfsWithPrev + reconstructPath. 在距离矩阵构造里
    //  应直接用 bfsWithPrev + reconstructPath 以共享一次 BFS.)
    std::vector<Point> shortestPath(const Point& from, const Point& to) const;
};

} // namespace gc
