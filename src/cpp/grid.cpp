// grid.cpp —— BFS 实现
#include "grid.h"

#include <queue>
#include <utility>

namespace gc {

namespace {
// 4-邻接方向: 上下左右
constexpr int dR[4] = {-1, 1, 0, 0};
constexpr int dC[4] = { 0, 0,-1, 1};
} // namespace

std::vector<std::vector<int>> Grid::bfsDistances(const Point& from) const {
    std::vector<std::vector<int>> dist(rows, std::vector<int>(cols, -1));
    if (!walkable(from)) return dist;

    dist[from.r][from.c] = 0;
    std::queue<Point> q;
    q.push(from);
    while (!q.empty()) {
        Point cur = q.front(); q.pop();
        int d = dist[cur.r][cur.c];
        for (int k = 0; k < 4; ++k) {
            int nr = cur.r + dR[k];
            int nc = cur.c + dC[k];
            if (!walkable(nr, nc)) continue;
            if (dist[nr][nc] != -1) continue;
            dist[nr][nc] = d + 1;
            q.push({nr, nc});
        }
    }
    return dist;
}

void Grid::bfsWithPrev(const Point& from,
                       std::vector<std::vector<int>>& dist,
                       std::vector<std::vector<Point>>& prev) const {
    dist.assign(rows, std::vector<int>(cols, -1));
    prev.assign(rows, std::vector<Point>(cols, {-1, -1}));
    if (!walkable(from)) return;

    dist[from.r][from.c] = 0;
    std::queue<Point> q;
    q.push(from);
    while (!q.empty()) {
        Point cur = q.front(); q.pop();
        int d = dist[cur.r][cur.c];
        for (int k = 0; k < 4; ++k) {
            int nr = cur.r + dR[k];
            int nc = cur.c + dC[k];
            if (!walkable(nr, nc)) continue;
            if (dist[nr][nc] != -1) continue;
            dist[nr][nc] = d + 1;
            prev[nr][nc] = cur;
            q.push({nr, nc});
        }
    }
}

std::vector<Point> Grid::reconstructPath(const Point& from, const Point& to,
                                         const std::vector<std::vector<Point>>& prev) const {
    std::vector<Point> path;
    if (!walkable(from) || !walkable(to)) return path;
    if (from == to) { path.push_back(from); return path; }
    // to 不可达
    if (prev[to.r][to.c].r < 0) return path;

    Point cur = to;
    while (!(cur == from)) {
        path.push_back(cur);
        cur = prev[cur.r][cur.c];
        if (cur.r < 0) return {};  // 保险: 链断
    }
    path.push_back(from);
    for (size_t i = 0, j = path.size() - 1; i < j; ++i, --j) std::swap(path[i], path[j]);
    return path;
}

std::vector<Point> Grid::shortestPath(const Point& from, const Point& to) const {
    // 便利接口: 复合调用 bfsWithPrev + reconstructPath.
    // 在批量需求(距离矩阵构造) 中应直接复用同一次 BFS 的 prev 表,
    // 否则该接口每次调用都做一次完整 BFS, 导致 O(K^2 * ML) 而非 O(K * ML).
    std::vector<std::vector<int>>   dist;
    std::vector<std::vector<Point>> prev;
    bfsWithPrev(from, dist, prev);
    return reconstructPath(from, to, prev);
}

} // namespace gc
