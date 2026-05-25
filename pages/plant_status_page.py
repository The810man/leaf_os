"""Single-plant status page.

Replaces the old 6-pot grid. Shows the plant currently published on
`plants/<id>/state` (mocked locally for now) inside a clean container
with sensor + flag panels.
"""

from typing import List

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation
from models.plant import MQTTPlantMock, STAGE_NAMES
from models.plant_stage import PlantStageLoader
from pages.base_page import BasePage
from ui.panels import draw_text, rounded_box


class PlantStatusPage(BasePage):
    """Overview of the single tracked plant."""

    def __init__(self, plant_source: MQTTPlantMock):
        super().__init__("plants")
        self.source = plant_source
        self.stage_loader = PlantStageLoader()

    def get_title(self) -> str:
        return " PLANT STATUS "

    def draw(self, stdscr, y: int, x: int, h: int, w: int,
             monitor: SystemMonitor, animation: AsciiAnimation):
        self.source.tick()
        plant = self.source.plant

        # Outer container — modeled as the MQTT topic envelope.
        topic = f" plants/{plant.plant_id}/state "
        rounded_box(stdscr, y, x, h, w, topic, 1)

        # Header line
        header = f"{plant.name}  ·  {plant.strain}  ·  {plant.stage_name}"
        draw_text(stdscr, y + 1, x + 3, header, 2, True)
        sub = f"Age: {plant.age_days}d ({plant.age_weeks:.1f}w)   Stage {plant.stage}/9   Harvest in ~{plant.days_until_harvest}d"
        draw_text(stdscr, y + 2, x + 3, sub, 7)

        # Split into left (art) / right (info) columns
        inner_y = y + 4
        inner_h = h - 5
        left_w = max(28, w // 2 - 2)
        right_x = x + left_w + 2
        right_w = w - left_w - 4

        self._draw_art(stdscr, inner_y, x + 2, inner_h, left_w, plant.stage)
        self._draw_sensors(stdscr, inner_y, right_x, plant)
        self._draw_flags(stdscr, inner_y + 9, right_x, right_w, plant)
        self._draw_recent_events(stdscr, inner_y + 16, right_x, right_w, max(3, inner_h - 17), plant)

    def _draw_art(self, stdscr, y, x, h, w, stage: int):
        rounded_box(stdscr, y, x, h, w, f" stage_{stage} ", 1)
        art = self.stage_loader.get_stage(stage)
        if not art:
            return
        art_h = len(art)
        art_w = max((len(line) for line in art), default=0)
        start_y = y + max(1, (h - art_h) // 2)
        start_x = x + max(2, (w - art_w) // 2)
        for i, line in enumerate(art):
            if start_y + i < y + h - 1:
                draw_text(stdscr, start_y + i, start_x, line, 8, True)
        # Stage name caption
        caption = STAGE_NAMES.get(stage, "")
        if caption and h > 4:
            cx = x + max(2, (w - len(caption)) // 2)
            draw_text(stdscr, y + h - 2, cx, caption, 4, True)

    def _draw_sensors(self, stdscr, y, x, plant):
        rounded_box(stdscr, y, x, 8, 38, " plants/<id>/sensors ", 1)
        s = plant.sensors
        rows = [
            ("Temperature", f"{s.temp_c:5.1f} °C", 4),
            ("Humidity",    f"{s.humidity:5.1f} %", 4),
            ("Soil",        f"{s.soil_moisture:5.1f} %", 6 if s.soil_moisture < 35 else 4),
            ("Light",       f"{s.light_lux:>5} lux", 5),
        ]
        for i, (label, val, color) in enumerate(rows):
            draw_text(stdscr, y + 2 + i, x + 3, f"{label:<13}", 7)
            draw_text(stdscr, y + 2 + i, x + 18, val, color, True)

    def _draw_flags(self, stdscr, y, x, w, plant):
        rounded_box(stdscr, y, x, 6, 38, " flags ", 1)
        water_color = 6 if plant.needs_water else 4
        water_txt = "NEEDS WATER" if plant.needs_water else "OK"
        harvest_color = 8 if plant.can_harvest else 7
        harvest_txt = "READY" if plant.can_harvest else "not yet"
        draw_text(stdscr, y + 2, x + 3, "Water    :", 7)
        draw_text(stdscr, y + 2, x + 16, water_txt, water_color, True)
        draw_text(stdscr, y + 3, x + 3, "Harvest  :", 7)
        draw_text(stdscr, y + 3, x + 16, harvest_txt, harvest_color, True)

    def _draw_recent_events(self, stdscr, y, x, w, h, plant):
        if h < 4:
            return
        rounded_box(stdscr, y, x, h, min(w, 60), " plants/<id>/events ", 1)
        events = plant.events[-(h - 3):]
        for i, ev in enumerate(events):
            ts = ev.ts.strftime("%m-%d %H:%M")
            line = f"{ts}  {ev.kind:<11} {ev.note}"
            draw_text(stdscr, y + 1 + i, x + 3, line[: w - 4], 3)

    def handle_input(self, key: int, output_lines: List[str]) -> bool:
        # 'w' to water the current plant
        if key == ord("w"):
            self.source.water()
            output_lines.append(f"Watered {self.source.plant.name}.")
            return True
        return False
