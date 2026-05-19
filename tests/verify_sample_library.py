"""verify_sample_library.py —— 样例库自检脚本.

对 data/sample_library/ 下每个 .txt 实例跑 solver, 校验输出 STATUS 与
EXPECTED 表一致, 并把结果写入 tests/sample_library_log.csv.

预期表按子目录推断:
  basic/, capacity/, obstacle/, compare/, multi_vehicle/                  → ok
  invalid_load/, invalid_unreachable/, invalid_weight/, invalid_duplicate/ → infeasible
  invalid_format/                                                         → error

注: 容量/重量/重复/可达性 均落在 feasibility 模块, 统一返回 infeasible;
    仅输入解析期能识别的硬错误 (格式/字符/越界 K) 才返回 error.
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOLVER = os.path.abspath(os.path.join(ROOT, "build", "solver.exe"))
LIB = os.path.join(ROOT, "data", "sample_library")

EXPECT_BY_DIR = {
    "basic":               "ok",
    "capacity":            "ok",
    "obstacle":            "ok",
    "compare":             "ok",
    "multi_vehicle":       "ok",
    "invalid_load":        "infeasible",
    "invalid_unreachable": "infeasible",
    "invalid_weight":      "infeasible",
    "invalid_duplicate":   "infeasible",
    "invalid_format":      "error",
}

OVERRIDES: dict = {}


def run_solver(path):
    proc = subprocess.run([SOLVER, path], capture_output=True, text=True,
                          encoding="utf-8", timeout=15)
    status = ""
    for ln in proc.stdout.splitlines():
        tok = ln.split()
        if tok and tok[0] == "STATUS":
            status = tok[1] if len(tok) > 1 else ""
            break
    return status, proc.stdout


def main():
    rows = []
    fail = 0
    for cat in sorted(os.listdir(LIB)):
        cat_dir = os.path.join(LIB, cat)
        if not os.path.isdir(cat_dir):
            continue
        expected_default = EXPECT_BY_DIR.get(cat)
        for fn in sorted(os.listdir(cat_dir)):
            if not fn.endswith(".txt"):
                continue
            full = os.path.join(cat_dir, fn)
            expected = OVERRIDES.get((cat, fn), expected_default)
            status, _ = run_solver(full)
            ok = status == expected
            if not ok:
                fail += 1
            rows.append((cat, fn, expected, status, "PASS" if ok else "FAIL"))
            marker = "OK " if ok else "!! "
            print(f"  {marker}{cat}/{fn:30s} expected={expected:11s} got={status}")

    log = os.path.join(HERE, "sample_library_log.csv")
    with open(log, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "file", "expected", "actual", "verdict"])
        w.writerows(rows)
    print(f"\n  {len(rows)} 个样例, {fail} 个 FAIL. 日志: {log}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
