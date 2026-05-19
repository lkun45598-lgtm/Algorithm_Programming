// io_utils.cpp —— 输入解析与输出格式实现
#include "io_utils.h"

#include <iomanip>
#include <sstream>
#include <string>

namespace gc {

namespace {
// 去除字符串尾部的 \r (兼容 Windows CRLF 输入)
void strip_cr(std::string& s) {
    while (!s.empty() && (s.back() == '\r' || s.back() == '\n')) s.pop_back();
}
}

bool parse_input(std::istream& in, ParsedInput& out, std::string& err) {
    auto& g = out.grid;
    if (!(in >> g.rows >> g.cols)) { err = "读取 M N 失败"; return false; }
    if (g.rows <= 0 || g.cols <= 0) { err = "M N 必须为正整数"; return false; }
    in.ignore();    // 吃掉行末换行
    g.cells.assign(g.rows, std::string());
    for (int i = 0; i < g.rows; ++i) {
        std::string line;
        if (!std::getline(in, line)) {
            err = "读取地图第 " + std::to_string(i) + " 行失败"; return false;
        }
        strip_cr(line);  // 去掉 CRLF 的 \r
        // 严格校验: 长度必须等于 cols
        if (static_cast<int>(line.size()) != g.cols) {
            err = "地图第 " + std::to_string(i) + " 行长度 "
                + std::to_string(line.size()) + " 不等于 cols=" + std::to_string(g.cols);
            return false;
        }
        // 严格校验: 字符必须 ∈ {'.', '#'}
        for (int j = 0; j < g.cols; ++j) {
            char ch = line[(size_t)j];
            if (ch != '.' && ch != '#') {
                err = "地图第 " + std::to_string(i) + " 行第 " + std::to_string(j)
                    + " 列出现非法字符 '" + std::string(1, ch) + "', 仅允许 '.' 或 '#'";
                return false;
            }
        }
        g.cells[i] = line;
    }

    auto& kp = out.kp;
    if (!(in >> kp.parking.r >> kp.parking.c)) { err = "读取 S 失败"; return false; }
    if (!(in >> kp.plant.r   >> kp.plant.c))   { err = "读取 T 失败"; return false; }

    int K = 0;
    if (!(in >> K)) { err = "读取 K 失败"; return false; }
    if (K < 1 || K > 8) { err = "K 必须在 1..8 之间"; return false; }
    kp.collects.resize(K); kp.weights.resize(K);
    for (int i = 0; i < K; ++i) {
        if (!(in >> kp.collects[i].r >> kp.collects[i].c >> kp.weights[i])) {
            err = "读取收集点 " + std::to_string(i) + " 失败"; return false;
        }
    }
    if (!(in >> kp.wMax)) { err = "读取 W_max 失败"; return false; }

    std::string tag, val;
    if (!(in >> tag >> val) || tag != "ALGO") { err = "读取 ALGO 失败"; return false; }
    out.algo = val;
    return true;
}

void emit_solution(std::ostream& out, const Solution& sol) {
    out << "STATUS " << sol.status << "\n";
    if (!sol.ok) {
        out << "REASON " << sol.error << "\n";
        out << "END\n";
        return;
    }
    out << "ALGORITHM " << sol.algorithm << "\n";
    out << "TOTAL_DISTANCE " << sol.totalDistance << "\n";
    out << "RUNTIME_MS " << std::fixed << std::setprecision(3) << sol.runtimeMs << "\n";

    auto emitTrips = [&](const std::vector<Trip>& trips, int vid) {
        out << "VEHICLE " << vid << " TRIPS " << trips.size() << "\n";
        for (size_t t = 0; t < trips.size(); ++t) {
            const Trip& tr = trips[t];
            out << "TRIP " << (t + 1) << " LOAD " << tr.load << " DIST " << tr.distance << "\n";
            out << "POINTS";
            for (int idx : tr.pointIndices) out << " " << idx;
            out << "\n";
            out << "PATH";
            for (const auto& p : tr.fullPath) out << " " << p.r << "," << p.c;
            out << "\n";
        }
    };

    if (!sol.vehicleTrips.empty()) {
        out << "VEHICLES " << sol.vehicleTrips.size() << "\n";
        for (size_t v = 0; v < sol.vehicleTrips.size(); ++v) {
            emitTrips(sol.vehicleTrips[v], static_cast<int>(v) + 1);
        }
    } else {
        out << "VEHICLES 1\n";
        emitTrips(sol.trips, 1);
    }
    out << "END\n";
}

// ===================== JSON 输出 =====================
namespace {
// 转义 JSON 字符串里的特殊字符 (无 unicode 转义需求, 输入字符串均为 ASCII 算法名 + 错误描述)
std::string json_escape(const std::string& s) {
    std::string r; r.reserve(s.size() + 2);
    for (char c : s) {
        switch (c) {
            case '"':  r += "\\\""; break;
            case '\\': r += "\\\\"; break;
            case '\n': r += "\\n";  break;
            case '\r': r += "\\r";  break;
            case '\t': r += "\\t";  break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    char buf[8]; std::snprintf(buf, sizeof(buf), "\\u%04x", (unsigned)c);
                    r += buf;
                } else r += c;
        }
    }
    return r;
}

void emit_trips_json(std::ostream& out, const std::vector<Trip>& trips, const char* indent) {
    out << "[";
    for (size_t t = 0; t < trips.size(); ++t) {
        const Trip& tr = trips[t];
        if (t) out << ",";
        out << "\n" << indent << "  {";
        out << "\n" << indent << "    \"load\": "     << tr.load     << ",";
        out << "\n" << indent << "    \"distance\": " << tr.distance << ",";
        out << "\n" << indent << "    \"point_indices\": [";
        for (size_t i = 0; i < tr.pointIndices.size(); ++i) {
            if (i) out << ", ";
            out << tr.pointIndices[i];
        }
        out << "],";
        out << "\n" << indent << "    \"path\": [";
        for (size_t i = 0; i < tr.fullPath.size(); ++i) {
            if (i) out << ", ";
            out << "[" << tr.fullPath[i].r << ", " << tr.fullPath[i].c << "]";
        }
        out << "]";
        out << "\n" << indent << "  }";
    }
    if (!trips.empty()) out << "\n" << indent;
    out << "]";
}
} // anon

void emit_solution_json(std::ostream& out, const Solution& sol) {
    out << "{\n";
    out << "  \"status\": \""    << json_escape(sol.status)    << "\"";
    if (!sol.ok) {
        out << ",\n  \"error\": \"" << json_escape(sol.error) << "\"";
        out << "\n}\n";
        return;
    }
    out << ",\n  \"algorithm\": \"" << json_escape(sol.algorithm) << "\"";
    out << ",\n  \"total_distance\": " << sol.totalDistance;
    out << ",\n  \"runtime_ms\": "  << std::fixed << std::setprecision(3) << sol.runtimeMs;
    out << ",\n  \"vehicles\": [";

    auto emit_vehicle = [&](int id, const std::vector<Trip>& trips, bool last) {
        out << "\n    {\n";
        out << "      \"id\": " << id << ",\n";
        out << "      \"trips\": ";
        emit_trips_json(out, trips, "      ");
        out << "\n    }";
        if (!last) out << ",";
    };

    if (!sol.vehicleTrips.empty()) {
        for (size_t v = 0; v < sol.vehicleTrips.size(); ++v) {
            emit_vehicle(static_cast<int>(v) + 1, sol.vehicleTrips[v],
                         v + 1 == sol.vehicleTrips.size());
        }
    } else {
        emit_vehicle(1, sol.trips, true);
    }
    out << "\n  ]\n}\n";
}

} // namespace gc
