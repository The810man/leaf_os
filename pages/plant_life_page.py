"""Plant life view — large ASCII drawing of the plant per its current stage,
with a growth timeline showing past, current, and upcoming stages.
"""

from typing import List

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation
from models.plant import MQTTPlantMock, STAGE_NAMES, weeks_to_stage, _STAGE_WEEKS
from models.plant_stage import PlantStageLoader
from pages.base_page import BasePage
from ui.panels import draw_text, rounded_box


class PlantLifeViewPage(BasePage):
    def __init__(self, plant_source: MQTTPlantMock):
        super().__init__("plant_life")
        self.source = plant_source
        self.stage_loader = PlantStageLoader()

    def get_title(self) -> str:
        return " PLANT LIFE VIEW "

    def draw(self, stdscr, y: int, x: int, h: int, w: int,
             monitor: SystemMonitor, animation: AsciiAnimation):
        self.source.tick()
        plant = self.source.plant

        rounded_box(stdscr, y, x, h, w, f" plants/{plant.plant_id}/life ", 1)

        title = f"{plant.name}  ·  Week {plant.age_weeks:.1f}  ·  {plant.stage_name}"
        draw_text(stdscr, y + 1, x + (w - len(title)) // 2, title, 2, True)

        # Big art panel takes most of the screen, timeline strip at the bottom
        art_h = h - 8
        self._draw_big_art(stdscr, y + 3, x + 2, art_h, w - 4, plant.stage)
        self._draw_timeline(stdscr, y + h - 5, x + 2, w - 4, plant.stage)

    def _draw_big_art(self, stdscr, y, x, h, w, stage: int):
        rounded_box(stdscr, y, x, h, w, f" stage {stage} - {STAGE_NAMES.get(stage, '')} ", 1)
        art = self.stage_loader.get_stage(stage)
        if not art:
            return
        # Scale up by repeating each char horizontally and each line vertically
        # to make the tiny stage art readable on the big panel.
        scaled = self._scale_up(art, h - 4, w - 6)
        sh = len(scaled)
        sw = max((len(line) for line in scaled), default=0)
        start_y = y + 1 + max(0, (h - 2 - sh) // 2)
        start_x = x + max(2, (w - sw) // 2)
        for i, line in enumerate(scaled):
            if start_y + i < y + h - 1:
                draw_text(stdscr, start_y + i, start_x, line, 8, True)

    @staticmethod
    def _scale_up(art: List[str], max_h: int, max_w: int) -> List[str]:
        if not art:
            return []
        src_h = len(art)
        src_w = max((len(line) for line in art), default=1)
        # Pick integer scale factors that fit. Char cells are ~2x tall as wide,
        # so use 2*sx for vertical to keep proportions roughly correct.
        sx = max(1, min(max_w // max(1, src_w), max_h // max(1, src_h * 2)))
        sx = max(1, sx)
        sy = max(1, sx * 2)
        out = []
        for line in art:
            wide = "".join(ch * sx for ch in line.ljust(src_w))
            for _ in range(sy):
                out.append(wide)
        return out

    def _draw_timeline(self, stdscr, y, x, w, current_stage: int):
        rounded_box(stdscr, y, x, 4, w, " GROWTH TIMELINE (weeks) ", 1)
        # Build a strip showing each stage with its week threshold.
        slot_w = max(6, (w - 4) // 10)
        for i in range(10):
            cx = x + 2 + i * slot_w
            if cx + slot_w > x + w - 2:
                break
            marker = "●" if i == current_stage else ("○" if i < current_stage else "·")
            color = 8 if i == current_stage else (4 if i < current_stage else 7)
            label = f"{marker} {i}"
            draw_text(stdscr, y + 1, cx, label, color, i == current_stage)
            wk = f"{_STAGE_WEEKS[i]}w"
            draw_text(stdscr, y + 2, cx, wk, 7)
