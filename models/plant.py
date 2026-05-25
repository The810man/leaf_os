"""Plant data model shaped after a future MQTT topic layout.

Topic schema (for when a real broker is wired in):
    plants/<id>/state    -> name, strain, planted_at, stage, flags
    plants/<id>/sensors  -> temp_c, humidity, soil_moisture, light_lux
    plants/<id>/events   -> {ts, kind, note}  (e.g. watered, topped, flipped)

The mock just generates this same payload shape locally so that a real
MQTT subscriber can replace `MQTTPlantMock.tick()` without touching the UI.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Stage names — index matches stage 0..9
STAGE_NAMES: Dict[int, str] = {
    0: "Empty Pot",
    1: "Seedling",
    2: "Sprout",
    3: "Young",
    4: "Vegetative",
    5: "Late Veg",
    6: "Pre-Flower",
    7: "Flowering",
    8: "Late Flower",
    9: "Harvest Ready",
}

# Approximate week thresholds for each stage (typical 12-week cycle).
# weeks_to_stage(6) -> 5 ("Late Veg"), matching the user's 6-week-old plant.
_STAGE_WEEKS = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12]


def weeks_to_stage(weeks: float) -> int:
    """Map plant age in weeks to a stage 0..9."""
    stage = 0
    for i, threshold in enumerate(_STAGE_WEEKS):
        if weeks >= threshold:
            stage = i
    return stage


@dataclass
class SensorReading:
    """Latest sensor values from `plants/<id>/sensors`."""
    temp_c: float = 23.5
    humidity: float = 55.0
    soil_moisture: float = 62.0
    light_lux: int = 28000


@dataclass
class PlantEvent:
    """Entry from `plants/<id>/events`."""
    ts: datetime
    kind: str
    note: str = ""


@dataclass
class Plant:
    """State payload shaped after `plants/<id>/state`."""
    plant_id: int
    name: str
    strain: str
    planted_at: datetime
    stage: int = 0
    needs_water: bool = False
    can_harvest: bool = False
    sensors: SensorReading = field(default_factory=SensorReading)
    events: List[PlantEvent] = field(default_factory=list)
    sensor_history: List[SensorReading] = field(default_factory=list)

    @property
    def age_days(self) -> int:
        return max(0, (datetime.now() - self.planted_at).days)

    @property
    def age_weeks(self) -> float:
        return self.age_days / 7.0

    @property
    def stage_name(self) -> str:
        return STAGE_NAMES.get(self.stage, "Unknown")

    @property
    def days_until_harvest(self) -> int:
        target = self.planted_at + timedelta(weeks=12)
        return max(0, (target - datetime.now()).days)


class MQTTPlantMock:
    """Stand-in for an MQTT subscriber.

    Owns one plant and mutates its sensor + state values on a tick.
    Replace `tick()` with a real `on_message` handler when the broker
    is wired up — the rest of the UI reads `self.plant` either way.
    """

    def __init__(self, plant: Optional[Plant] = None, tick_interval: float = 1.5):
        self.plant = plant or self._default_plant()
        self.tick_interval = tick_interval
        self._last_tick = 0.0
        self._t0 = time.monotonic()

    @staticmethod
    def _default_plant() -> Plant:
        # 6-week-old plant per user's setup.
        planted = datetime.now() - timedelta(weeks=6)
        p = Plant(
            plant_id=1,
            name="Bessie",
            strain="Northern Lights",
            planted_at=planted,
            stage=weeks_to_stage(6),
        )
        p.events.extend([
            PlantEvent(planted, "planted", "Seed in soil"),
            PlantEvent(planted + timedelta(days=4), "germinated", "First leaves"),
            PlantEvent(planted + timedelta(weeks=2), "watered", "200ml + nutes"),
            PlantEvent(planted + timedelta(weeks=4), "topped", "FIM topping"),
            PlantEvent(planted + timedelta(weeks=5), "watered", "300ml"),
        ])
        return p

    def tick(self) -> None:
        """Advance the mock; safe to call every frame."""
        now = time.monotonic()
        if now - self._last_tick < self.tick_interval:
            return
        self._last_tick = now

        p = self.plant
        # Re-derive stage from age so the life view evolves over (real) time.
        p.stage = weeks_to_stage(p.age_weeks)
        p.can_harvest = p.stage >= 9

        # Drift sensors with smooth sine + jitter so the graphs look alive.
        t = now - self._t0
        s = p.sensors
        s.temp_c = round(23.0 + 2.0 * math.sin(t / 30.0) + random.uniform(-0.3, 0.3), 1)
        s.humidity = round(55.0 + 8.0 * math.sin(t / 45.0) + random.uniform(-1.0, 1.0), 1)
        s.soil_moisture = round(max(15.0, s.soil_moisture - random.uniform(0.05, 0.25)), 1)
        s.light_lux = int(28000 + 4000 * math.sin(t / 20.0))

        p.needs_water = s.soil_moisture < 35.0

        # Keep a short rolling history for graphs.
        p.sensor_history.append(SensorReading(s.temp_c, s.humidity, s.soil_moisture, s.light_lux))
        if len(p.sensor_history) > 120:
            p.sensor_history = p.sensor_history[-120:]

    def water(self) -> None:
        """User action — refill soil moisture and log an event."""
        self.plant.sensors.soil_moisture = 80.0
        self.plant.needs_water = False
        self.plant.events.append(PlantEvent(datetime.now(), "watered", "Manual"))
