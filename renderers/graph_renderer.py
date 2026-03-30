from collections import deque
from typing import Deque, List


class GraphRenderer:
    BARS = "⣀⣤⣷⣿⣿░▒░░⣿▒▒▒▓█████"

    @staticmethod
    def sparkline(data: Deque[float], width: int) -> str:
        values = list(data)[-width:]
        if not values:
            return " " * width

        out = []
        for v in values:
            idx = round((v / 100.0) * (len(GraphRenderer.BARS) - 1))
            idx = max(0, min(len(GraphRenderer.BARS) - 1, idx))
            out.append(GraphRenderer.BARS[idx])
        return "".join(out)

    @staticmethod
    def mini_columns(data: Deque[float], width: int, height: int) -> List[str]:
        values = list(data)[-width:]
        if not values:
            return [" " * width for _ in range(height)]

        rows = []
        for row in range(height):
            threshold = ((height - row) / height) * 100.0
            line = []
            for v in values:
                line.append("█" if v >= threshold else " ")
            rows.append("".join(line))
        return rows
