# 基于多策略的城市垃圾收运路线规划

本项目是《算法设计与分析》课程设计作业。系统包含一个 C++ 算法核心(BFS + 动态规划 + 贪心 + 双车协同 + 分治法子集枚举)和一个 PyQt6 图形化前端(交互式地图编辑 + 车辆动画演示)。

## 目录结构

```
Program Design/
├── docs/
│   └── superpowers/plans/2026-05-15-garbage-collection-route-planning.md
├── src/
│   ├── cpp/                      # C++ 算法核心
│   │   ├── types.h               # 通用数据结构
│   │   ├── grid.{h,cpp}          # 网格 + BFS
│   │   ├── feasibility.{h,cpp}   # check_feasibility()
│   │   ├── solver_common.{h,cpp} # 距离矩阵 + 路径恢复
│   │   ├── dp.{h,cpp}            # 动态规划 (含分治变体)
│   │   ├── greedy.{h,cpp}        # 贪心法
│   │   ├── dual.{h,cpp}          # 双车协同
│   │   ├── io_utils.{h,cpp}      # I/O 协议
│   │   └── main.cpp              # CLI 入口
│   └── gui/                      # PyQt6 GUI
│       ├── controller.py         # 调用 solver.exe 并解析输出
│       ├── map_view.py           # QGraphicsView 网格可视化 + 自适应缩放
│       ├── editor.py             # 编辑状态管理
│       ├── animator.py           # QVariantAnimation 补间动画 (InOutQuad)
│       └── main.py               # 主窗口 (KPI 卡片 / 状态徽章 / 实时状态)
├── data/                         # 测试样例
│   ├── sample_small.txt          # 8×8, 4 收集点
│   ├── sample_medium.txt         # 12×12, 6 收集点
│   ├── sample_large.txt          # 15×15, 8 收集点
│   └── sample_library/           # 分类样例库 (10 类, 20 用例, 见其内 README)
├── tests/                        # 自动化测试与基准
│   ├── brute_force_checker.py    # n!×2^(n-1) 暴力对拍 (720 例, 0 mismatch)
│   ├── dense_benchmark.py        # n∈[3,8]×ρ×种子 密集基准 (1940 数据点)
│   ├── verify_sample_library.py  # 样例库分类自检 (20/20 PASS)
│   ├── random_case_generator.py  # 随机实例生成器 (seed→实例)
│   └── seeds.txt                 # 60 个固定素数种子
├── docs/figures/                 # 报告图: 流程图 / 性能图 / 路径可视化
├── build/
│   └── solver.exe                # 编译产物
├── build.bat                     # 编译脚本
├── run_gui.bat                   # 启动 GUI
├── README.md                     # 本文件
├── report.typ                    # 课程设计报告源文件 (Typst)
└── report.pdf                    # 课程设计报告 (36 页, 编译产物)
```

## 依赖环境

- **C++ 编译器:** g++ 15.2.0 (MSYS2 mingw64), 支持 C++17
- **Python:** 3.13 (推荐使用 Anaconda 的 `pytorch` 环境)
- **PyQt6** (`pip install PyQt6` 或者用 conda)

## 编译

```bat
build.bat
```

或在 Git Bash 中:

```bash
g++ -std=c++17 -O2 -Wall -Wextra \
    src/cpp/grid.cpp src/cpp/feasibility.cpp src/cpp/solver_common.cpp \
    src/cpp/dp.cpp src/cpp/greedy.cpp src/cpp/dual.cpp \
    src/cpp/io_utils.cpp src/cpp/main.cpp -o build/solver.exe
```

## 运行

### 命令行模式

```bash
./build/solver.exe data/sample_small.txt
./build/solver.exe data/sample_medium.txt
./build/solver.exe data/sample_large.txt

# JSON 输出 (与 Web 前端/外部工具对接时使用; PyQt 仍走默认行式协议)
./build/solver.exe data/sample_small.txt --json
```

切换算法只需修改输入文件最后一行的 `ALGO` 字段。可选值:

| 算法标识      | 含义                                |
|---------------|-------------------------------------|
| `dp`          | 标准动态规划(子集枚举 O(3^N))      |
| `dp_dc`       | 动态规划 + 分治法子集枚举(加分项 3)|
| `greedy`      | 最近邻贪心                          |
| `multi_dp`    | 双车协同 + DP(加分项 1)            |
| `multi_greedy`| 双车协同 + 贪心(加分项 1)          |

### 图形化界面模式

```bat
run_gui.bat
```

或:

```bash
source D:/Anaconda/etc/profile.d/conda.sh && conda activate pytorch
python src/gui/main.py
```

GUI 用法:
1. 左侧"编辑模式"选择障碍 / S / T / 收集点 (每种带色块图标)
2. 在中间网格点击放置元素 (右键擦除)
3. 设置 W_max 与算法
4. 点 "运行求解 + 动画":
   - 右上 4 张 KPI 卡片定格 *总距离 / 耗时 / 车辆数 / 总行程*
   - 状态徽章变 *运行中*, 小车沿规划路径滑动
   - "实时状态"面板每移动一格刷新 *当前 trip / 载重 / 已行驶距离*
   - 完成时徽章变 *完成*, 行背景变绿
5. "行程详情"区域列出每辆车每条 trip 的载重 / 距离 / 访问点序列

也可点 "载入样例文件" 直接读取 `data/` 下的 `.txt`, 或 "随机生成示例" 一键创建。

## 输入文件格式

```
M N                  # 行数 列数
<M 行地图: '.'=空地, '#'=障碍>
S_row S_col          # 停车场
T_row T_col          # 处理厂
K                    # 收集点数 (K ≤ 8)
P_row P_col w        # 重复 K 行: 收集点坐标 + 重量
...
W_max                # 最大载重
ALGO <algo>          # 算法标识 (见上表)
```

## 输出协议

默认为行式文本协议:

```
STATUS ok | error | infeasible
[REASON ...]                    # 仅在 status != ok 时出现
ALGORITHM <name>
TOTAL_DISTANCE <int>
RUNTIME_MS <float>
VEHICLES <n>                    # 1=单车, 2=双车
VEHICLE <id> TRIPS <count>
TRIP <id> LOAD <load> DIST <dist>
POINTS <i1> <i2> ...
PATH <r1>,<c1> <r2>,<c2> ...
...
END
```

加 `--json` 后改用结构化 JSON, schema 示例:

```json
{
  "status": "ok",
  "algorithm": "dp",
  "total_distance": 34,
  "runtime_ms": 0.011,
  "vehicles": [
    { "id": 1, "trips": [
        { "load": 3, "distance": 14, "point_indices": [0, 1],
          "path": [[0,0], [1,0], ...] }
    ]}
  ]
}
```

错误/不可行情形 JSON 输出 `{"status": "error"|"infeasible", "error": "..."}`。

## 实现的加分项

| 加分项 | 实现位置 | 关键特性 |
|--------|----------|----------|
| (1) 双车协同 | `src/cpp/dual.{h,cpp}` + 算法 `multi_dp`/`multi_greedy` | `singleCost[mask]` 表复用 + 对称性消除, 460× 加速 |
| (2) 图形化界面 + 动画 | `src/gui/` 整个目录 | KPI 卡片 / 状态徽章 / 实时载重 + 已行驶距离 / 多色路径 / 自适应缩放 |
| (3) 分治法子集枚举 | `src/cpp/dp.cpp` 中 `DpMode::DivideConquer` | pivot 规范化, 候选规模 $2^k - 1$ → $2^{k-1}$ |

## 测试

```bash
# 暴力对拍 (黄金标准, 验证 dp / dp_dc 与 n!×2^(n-1) 暴力解一致)
python tests/brute_force_checker.py tests/seeds.txt 5
# → 输出: PASS 658, MISMATCH 0, SKIP 62

# 样例库自检 (20 用例 × 3 类预期状态)
python tests/verify_sample_library.py
# → 输出: 20/20 PASS

# 密集基准 (n=3..8 × ρ × 种子, 生成 4 张性能图)
python tests/dense_benchmark.py 20 5
# → 输出 1940 数据点 + docs/figures/bench_*.png
```

详细原理与实验结果见 `report.pdf` (36 页, Typst 排版)。
