// main.cpp —— 命令行入口
// 用法: solver.exe [<input_file>]   (省略文件名则从 stdin 读取)
// 输出: 见 io_utils.h 中的行式文本协议

#include "io_utils.h"
#include "feasibility.h"
#include "dp.h"
#include "greedy.h"
#include "dual.h"

#include <fstream>
#include <iostream>
#include <sstream>

int main(int argc, char** argv) {
    gc::ParsedInput in;
    std::string err;
    bool ok;
    if (argc >= 2) {
        std::ifstream fin(argv[1]);
        if (!fin) {
            std::cout << "STATUS error\nREASON 无法打开文件 " << argv[1] << "\nEND\n";
            return 1;
        }
        ok = gc::parse_input(fin, in, err);
    } else {
        ok = gc::parse_input(std::cin, in, err);
    }
    if (!ok) {
        std::cout << "STATUS error\nREASON " << err << "\nEND\n";
        return 1;
    }

    auto feas = gc::check_feasibility(in.grid, in.kp);
    if (!feas.ok) {
        std::cout << "STATUS infeasible\nREASON " << feas.reason << "\nEND\n";
        return 0;
    }

    auto dm = gc::build_distance_matrix(in.grid, in.kp);
    gc::Solution sol;
    if      (in.algo == "dp")            sol = gc::solve_dp    (in.grid, in.kp, dm, gc::DpMode::Standard);
    else if (in.algo == "dp_dc")         sol = gc::solve_dp    (in.grid, in.kp, dm, gc::DpMode::DivideConquer);
    else if (in.algo == "greedy")        sol = gc::solve_greedy(in.grid, in.kp, dm);
    else if (in.algo == "multi_dp")      sol = gc::solve_dual  (in.grid, in.kp, dm, gc::DualBackend::Dp);
    else if (in.algo == "multi_greedy")  sol = gc::solve_dual  (in.grid, in.kp, dm, gc::DualBackend::Greedy);
    else {
        std::cout << "STATUS error\nREASON 未知算法 " << in.algo << "\nEND\n";
        return 1;
    }

    gc::emit_solution(std::cout, sol);
    return 0;
}
