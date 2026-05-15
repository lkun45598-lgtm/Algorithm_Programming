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
    if (!walkable(from)) return dist;     // 起点不可达直接返回全 -1

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
            if (dist[nr][nc] != -1) continue;   // 已访问
            dist[nr][nc] = d + 1;
            q.push({nr, nc});
        }
    }
    return dist;
}

std::vector<Point> Grid::shortestPath(const Point& from, const Point& to) const {
    std::vector<Point> path;
    if (!walkable(from) || !walkable(to)) return path;
    if (from == to) { path.push_back(from); return path; }

    // 记录每格的"上一步"以便回溯
    std::vector<std::vector<Point>> prev(rows, std::vector<Point>(cols, {-1,-1}));
    std::vector<std::vector<bool>>  vis (rows, std::vector<bool>(cols, false));
    vis[from.r][from.c] = true;

    std::queue<Point> q;
    q.push(from);
    bool found = false;
    while (!q.empty() && !found) {
        Point cur = q.front(); q.pop();
        for (int k = 0; k < 4; ++k) {
            int nr = cur.r + dR[k];
            int nc = cur.c + dC[k];
            if (!walkable(nr, nc) || vis[nr][nc]) continue;
            vis[nr][nc]  = true;
            prev[nr][nc] = cur;
            if (nr == to.r && nc == to.c) { found = true; break; }
            q.push({nr, nc});
        }
    }
    if (!found) return path;

    // 从 to 反向回溯到 from
    Point cur = to;
    while (!(cur == from)) {
        path.push_back(cur);
        cur = prev[cur.r][cur.c];
    }
    path.push_back(from);
    // 翻转 -> from..to
    for (size_t i = 0, j = path.size() - 1; i < j; ++i, --j) std::swap(path[i], path[j]);
    return path;
}

} // namespace gc
