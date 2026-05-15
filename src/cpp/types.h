#pragma once
// types.h —— 项目通用数据结构
// 描述: 网格坐标、关键点集合、行程(Trip)与解(Solution) 的统一类型定义。
//       所有算法/IO/求解器模块共享这一组类型,保持接口一致。

#include <string>
#include <vector>

namespace gc {  // gc = garbage collection (城市垃圾收运)

// 网格坐标 (r=行, c=列). 以左上角为原点, 行向下增长, 列向右增长.
struct Point {
    int r{0};
    int c{0};
    bool operator==(const Point& o) const noexcept { return r == o.r && c == o.c; }
    bool operator!=(const Point& o) const noexcept { return !(*this == o); }
    bool operator<(const Point& o)  const noexcept { return r != o.r ? r < o.r : c < o.c; }
};

// 关键点信息 —— 输入解析后传给求解器
struct KeyPoints {
    Point parking;                  // S 停车场
    Point plant;                    // T 处理厂
    std::vector<Point> collects;    // P0..P_{N-1} 收集点
    std::vector<int>   weights;     // 每个收集点的重量 w_i
    int                wMax{0};     // 车辆最大载重
    int N() const noexcept { return static_cast<int>(collects.size()); }
};

// 单次行程 —— 从某起点出发,依次访问若干收集点,最后到达 T
struct Trip {
    int                load{0};         // 本次行程总重量
    std::vector<int>   pointIndices;    // 访问的收集点编号 (0..N-1) ,按访问顺序排列
    std::vector<Point> fullPath;        // 完整网格路径(供 GUI 动画使用)
    int                distance{0};     // 本次行程的总移动距离
};

// 求解结果(可表达单/多车场景)
struct Solution {
    bool        ok{false};
    std::string status{"ok"};           // "ok" / "error" / "infeasible"
    std::string error;                  // 错误/不可行的原因
    std::string algorithm;              // 使用的算法名称
    int         totalDistance{0};       // 所有车所有行程的总距离
    double      runtimeMs{0.0};         // 算法耗时(毫秒)

    // 单车结果:只用 trips
    std::vector<Trip> trips;

    // 多车结果:外层 = 车辆,内层 = 行程
    std::vector<std::vector<Trip>> vehicleTrips;
};

} // namespace gc
