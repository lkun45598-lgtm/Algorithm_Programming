@echo off
REM 编译 solver.exe (MSYS2 g++ 15.2.0)
if not exist build mkdir build
g++ -std=c++17 -O2 -Wall -Wextra ^
    src\cpp\grid.cpp ^
    src\cpp\feasibility.cpp ^
    src\cpp\solver_common.cpp ^
    src\cpp\dp.cpp ^
    src\cpp\greedy.cpp ^
    src\cpp\dual.cpp ^
    src\cpp\io_utils.cpp ^
    src\cpp\main.cpp ^
    -o build\solver.exe
if %errorlevel% neq 0 (
    echo BUILD FAILED
    exit /b 1
)
echo BUILD OK -^> build\solver.exe
