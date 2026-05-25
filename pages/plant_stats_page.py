"""Plant stats page — sensor history graphs + growth metrics."""

from typing import List

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation
from models.plant import MQTTPlantMock
from pages.base_page import BasePage
from renderers.graph_renderer import GraphRenderer
from ui.panels import draw_text, rounded_box


class PlantStatsPage(BasePage):
    def __init__(self, plant_source: MQTTPlantMock):
        super().__init__("plant_stats")
        self.source = plant_source

    def get_title(self) -> str:
        return " PLANT STATS "

    def draw(self, stdscr, y: int, x: int, h: int, w: int,
             monitor: SystemMonitor, animation: AsciiAnimation):
        self.source.tick()
        plant = self.source.plant

        rounded_box(stdscr, y, x, h, w, f" plants/{plant.plant_id}/stats ", 1)

        # Top summary
        summary = (
            f"{plant.name} ({plant.strain})  ·  Stage {plant.stage}/9 - {plant.stage_name}  ·  "
            f"Age {plant.age_days}d  ·  Harvest in ~{plant.days_until_harvest}d"
        )
        draw_text(stdscr, y + 1, x + 3, summary, 2, True)

        # Two-column layout: numeric tiles on the left, graphs on the right
        tile_x = x + 2
        tile_w = max(28, w // 3)
        graph_x = tile_x + tile_w + 2
        graph_w = w - tile_w - 6

        self._draw_tiles(stdscr, y + 3, tile_x, tile_w, plant)
        self._draw_graph(stdscr, y + 3, graph_x, 7, graph_w,
                         " Soil Moisture (%) ",
                         [r.soil_moisture for r in plant.sensor_history],
                         plant.sensors.soil_moisture)
        self._draw_graph(stdscr, y + 10, graph_x, 7, graph_w,
                         " Temperature (°C) ",
                         [r.temp_c for r in plant.sensor_history],
                         plant.sensors.temp_c)
        self._draw_graph(stdscr, y + 17, graph_x, 7, graph_w,
                         " Humidity (%) ",
                         [r.humidity for r in plant.sensor_history],
                         plant.sensors.humidity)

    def _draw_tiles(self, stdscr, y, x, w, plant):
        rounded_box(stdscr, y, x, 21, w, " METRICS ", 1)
        s = plant.sensors
        rows = [
            ("Plant ID",       f"#{plant.plant_id}"),
            ("Strain",         plant.strain),
            ("Planted",        plant.planted_at.strftime("%Y-%m-%d")),
            ("Age",            f"{plant.age_days} days ({plant.age_weeks:.1f}w)"),
            ("Stage",          f"{plant.stage} - {plant.stage_name}"),
            ("Temp",           f"{s.temp_c:.1f} °C"),
            ("Humidity",       f"{s.humidity:.1f} %"),
            ("Soil Moisture",  f"{s.soil_moisture:.1f} %"),
            ("Light",          f"{s.light_lux} lux"),
            ("Events Logged",  f"{len(plant.events)}"),
            ("Harvest In",     f"{plant.days_until_harvest} days"),
            ("Needs Water",    "YES" if plant.needs_water else "no"),
            ("Can Harvest",    "YES" if plant.can_harvest else "no"),
        ]
        for i, (label, val) in enumerate(rows):
            if i + 2 >= 20:
                break
            draw_text(stdscr, y + 2 + i, x + 3, f"{label:<15}", 7)
            draw_text(stdscr, y + 2 + i, x + 19, str(val)[: max(1, w - 22)], 3, True)

    def _draw_graph(self, stdscr, y, x, h, w, title, data: List[float], current: float):
        rounded_box(stdscr, y, x, h, w, title, 1)
        inner_w = w - 4
        plot_h = max(1, h - 3)
        if inner_w < 8 or plot_h < 1 or not data:
            draw_text(stdscr, y + 2, x + 3, "(no data yet)", 7)
            return
        cols = GraphRenderer.mini_columns(data, inner_w, plot_h)
        for i, row in enumerate(cols):
            draw_text(stdscr, y + 1 + i, x + 2, row, 4)
        spark = GraphRenderer.sparkline(data, max(8, inner_w - 12))
        label = f"{current:6.1f} "
        draw_text(stdscr, y + h - 2, x + 2, spark, 2)
        draw_text(stdscr, y + h - 2, x + 2 + inner_w - len(label), label, 8, True)
