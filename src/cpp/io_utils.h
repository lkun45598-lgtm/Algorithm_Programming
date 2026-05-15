#pragma once
// io_utils.h —— 输入解析 + 输出格式
// 输入: 见 docs/superpowers/plans/...md 中的 I/O 协议
// 输出: 行式文本协议(STATUS / ALGORITHM / VEHICLES / VEHICLE / TRIP / POINTS / PATH / END)

#include "types.h"
#include "grid.h"
#include <istream>
#include <ostream>
#include <string>

namespace gc {

struct ParsedInput {
    Grid        grid;
    KeyPoints   kp;
    std::string algo;   // dp | greedy | dp_dc | multi_dp | multi_greedy
};

bool parse_input(std::istream& in, ParsedInput& out, std::string& error);

void emit_solution(std::ostream& out, const Solution& sol);

} // namespace gc
