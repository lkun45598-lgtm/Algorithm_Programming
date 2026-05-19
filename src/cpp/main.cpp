// main.cpp —— 命令行入口
// 用法:
//   solver.exe [<input_file>] [--json]
//     省略文件名则从 stdin 读取
//     默认输出行式文本协议 (前端 PyQt 依赖此协议)
//     带 --json 时改输出结构化 JSON, 便于第三方/Web 端解析

#include "io_utils.h"
#include "feasibility.h"
#include "dp.h"
#include "greedy.h"
#include "dual.h"

#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

int main(int argc, char** argv) {
    // ---- 参数解析: 可选 --json 开关 + 可选输入文件 (顺序任意) ----
    bool jsonMode = false;
    const char* inputFile = nullptr;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--json") jsonMode = true;
        else if (!inputFile) inputFile = argv[i];
    }

    auto emit_err = [&](const std::string& status, const std::string& reason) {
        if (jsonMode) {
            gc::Solution s; s.ok = false; s.status = status; s.error = reason;
            gc::emit_solution_json(std::cout, s);
        } else {
            std::cout << "STATUS " << status << "\nREASON " << reason << "\nEND\n";
        }
    };

    gc::ParsedInput in;
    std::string err;
    bool ok;
    if (inputFile) {
        std::ifstream fin(inputFile);
        if (!fin) { emit_err("error", std::string("无法打开文件 ") + inputFile); return 1; }
        ok = gc::parse_input(fin, in, err);
    } else {
        ok = gc::parse_input(std::cin, in, err);
    }
    if (!ok) { emit_err("error", err); return 1; }

    auto feas = gc::check_feasibility(in.grid, in.kp);
    if (!feas.ok) { emit_err("infeasible", feas.reason); return 0; }

    auto dm = gc::build_distance_matrix(in.grid, in.kp);
    gc::Solution sol;
    if      (in.algo == "dp")            sol = gc::solve_dp    (in.grid, in.kp, dm, gc::DpMode::Standard);
    else if (in.algo == "dp_dc")         sol = gc::solve_dp    (in.grid, in.kp, dm, gc::DpMode::DivideConquer);
    else if (in.algo == "greedy")        sol = gc::solve_greedy(in.grid, in.kp, dm);
    else if (in.algo == "multi_dp")      sol = gc::solve_dual  (in.grid, in.kp, dm, gc::DualBackend::Dp);
    else if (in.algo == "multi_greedy")  sol = gc::solve_dual  (in.grid, in.kp, dm, gc::DualBackend::Greedy);
    else { emit_err("error", "未知算法 " + in.algo); return 1; }

    if (jsonMode) gc::emit_solution_json(std::cout, sol);
    else          gc::emit_solution     (std::cout, sol);
    return 0;
}
