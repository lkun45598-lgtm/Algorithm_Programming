"""editor.py —— 编辑模式与状态管理"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

MODE_OBSTACLE = "obstacle"
MODE_PARKING = "parking"
MODE_PLANT = "plant"
MODE_POINT = "point"
MODE_ERASE = "erase"


@dataclass
class EditorState:
    rows: int = 10
    cols: int = 10
    cells: List[List[str]] = field(default_factory=list)
    parking: Optional[Tuple[int, int]] = None
    plant: Optional[Tuple[int, int]] = None
    points: List[Tuple[int, int]] = field(default_factory=list)
    weights: List[int] = field(default_factory=list)
    w_max: int = 3
    mode: str = MODE_OBSTACLE

    def __post_init__(self):
        if not self.cells:
            self.cells = [['.' for _ in range(self.cols)] for _ in range(self.rows)]

    def apply_click(self, r, c, button, weight_input=1):
        # 右键 = 擦除
        if button == 2:
            self._erase_at(r, c)
            return
        if self.mode == MODE_OBSTACLE:
            if self._is_key_cell(r, c):
                return
            self.cells[r][c] = '#' if self.cells[r][c] == '.' else '.'
        elif self.mode == MODE_PARKING:
            if self.cells[r][c] == '#':
                return
            self.parking = (r, c)
        elif self.mode == MODE_PLANT:
            if self.cells[r][c] == '#':
                return
            self.plant = (r, c)
        elif self.mode == MODE_POINT:
            if self.cells[r][c] == '#':
                return
            if (r, c) == self.parking or (r, c) == self.plant:
                return
            if (r, c) in self.points:
                return
            if len(self.points) >= 8:
                return
            self.points.append((r, c))
            self.weights.append(int(weight_input))
        elif self.mode == MODE_ERASE:
            self._erase_at(r, c)

    def _is_key_cell(self, r, c):
        if self.parking == (r, c):
            return True
        if self.plant == (r, c):
            return True
        return (r, c) in self.points

    def _erase_at(self, r, c):
        if self.parking == (r, c):
            self.parking = None
            return
        if self.plant == (r, c):
            self.plant = None
            return
        if (r, c) in self.points:
            i = self.points.index((r, c))
            self.points.pop(i)
            self.weights.pop(i)
            return
        if self.cells[r][c] == '#':
            self.cells[r][c] = '.'

    def serialize_grid_rows(self):
        return [''.join(row) for row in self.cells]
