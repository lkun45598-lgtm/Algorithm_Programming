"""controller.py —— 调用 solver.exe 并解析其行式输出"""
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# --- 数据模型 (与 C++ 端 Solution 对应) ---
@dataclass
class Trip:
    load: int = 0
    distance: int = 0
    point_indices: List[int] = field(default_factory=list)
    path: List[Tuple[int, int]] = field(default_factory=list)  # (r, c) 序列

@dataclass
class Solution:
    ok: bool = False
    status: str = "ok"
    reason: str = ""
    algorithm: str = ""
    total_distance: int = 0
    runtime_ms: float = 0.0
    vehicles: List[List[Trip]] = field(default_factory=list)   # 外层=车辆, 内层=trip


def _solver_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "build", "solver.exe"))


def build_input_text(grid_rows: List[str], parking, plant, points, weights, w_max, algo) -> str:
    M = len(grid_rows); N = len(grid_rows[0]) if M else 0
    lines = [f"{M} {N}"]
    lines.extend(grid_rows)
    lines.append(f"{parking[0]} {parking[1]}")
    lines.append(f"{plant[0]} {plant[1]}")
    lines.append(str(len(points)))
    for (r, c), w in zip(points, weights):
        lines.append(f"{r} {c} {w}")
    lines.append(str(w_max))
    lines.append(f"ALGO {algo}")
    return "\n".join(lines) + "\n"


def run_solver(input_text: str, timeout: float = 30.0) -> Solution:
    """写入临时文件 -> 调用 solver.exe -> 解析输出"""
    exe = _solver_path()
    if not os.path.exists(exe):
        s = Solution(ok=False, status="error", reason=f"找不到 {exe}, 请先 build")
        return s
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(input_text)
        in_path = f.name
    try:
        proc = subprocess.run(
            [exe, in_path],
            capture_output=True, text=True, timeout=timeout, encoding="utf-8"
        )
    except subprocess.TimeoutExpired:
        return Solution(ok=False, status="error", reason="solver 超时")
    finally:
        try: os.unlink(in_path)
        except OSError: pass

    return parse_solver_output(proc.stdout)


def parse_solver_output(text: str) -> Solution:
    sol = Solution()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    i = 0
    cur_vehicle: Optional[List[Trip]] = None
    cur_trip: Optional[Trip] = None
    while i < len(lines):
        ln = lines[i]; tok = ln.split()
        head = tok[0]
        if head == "STATUS":
            sol.status = tok[1]; sol.ok = (sol.status == "ok")
        elif head == "REASON":
            sol.reason = ln[len("REASON"):].strip()
        elif head == "ALGORITHM":
            sol.algorithm = tok[1]
        elif head == "TOTAL_DISTANCE":
            sol.total_distance = int(tok[1])
        elif head == "RUNTIME_MS":
            sol.runtime_ms = float(tok[1])
        elif head == "VEHICLES":
            # 暂只用于校验
            pass
        elif head == "VEHICLE":
            cur_vehicle = []
            sol.vehicles.append(cur_vehicle)
        elif head == "TRIP":
            # TRIP <id> LOAD <load> DIST <dist>
            cur_trip = Trip(load=int(tok[3]), distance=int(tok[5]))
            if cur_vehicle is None:
                cur_vehicle = []; sol.vehicles.append(cur_vehicle)
            cur_vehicle.append(cur_trip)
        elif head == "POINTS":
            if cur_trip is not None:
                cur_trip.point_indices = [int(x) for x in tok[1:]]
        elif head == "PATH":
            if cur_trip is not None:
                pts = []
                for x in tok[1:]:
                    r, c = x.split(",")
                    pts.append((int(r), int(c)))
                cur_trip.path = pts
        elif head == "END":
            break
        i += 1
    return sol
