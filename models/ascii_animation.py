import json
import time
from pathlib import Path
from typing import List, Any


class AsciiAnimation:
    def __init__(self, json_path: str, fallback_fps: float = 12.0):
        self.json_path = Path(json_path)
        self.frames: List[List[str]] = []
        self.frame_index = 0
        self.last_advance = 0.0
        self.frame_duration = 1.0 / fallback_fps
        self.max_width = 0
        self.max_height = 0
        self.load()

    def load(self):
        with self.json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        frames = self._extract_frames(data)
        if not frames:
            raise ValueError("No frames found in ascii animation json")

        self.frames = [self._normalize_frame(frame) for frame in frames]

        fps = self._extract_fps(data)
        if fps and fps > 0:
            self.frame_duration = 1.0 / fps

        self._measure_frames()

    def _extract_frames(self, data: Any) -> List[Any]:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("frames", "ascii_frames", "images", "animation"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

    def _extract_fps(self, data: Any) -> float | None:
        if not isinstance(data, dict):
            return None

        for key in ("fps", "frame_rate", "framerate"):
            value = data.get(key)
            if isinstance(value, (int, float)) and value > 0:
                return float(value)

        delay = data.get("frame_duration") or data.get("delay")
        if isinstance(delay, (int, float)) and delay > 0:
            if delay > 1:
                return 1.0 / (delay / 1000.0)
            return 1.0 / float(delay)

        return None

    def _normalize_frame(self, frame: Any) -> List[str]:
        if isinstance(frame, str):
            return frame.splitlines()

        if isinstance(frame, list):
            return [str(line).rstrip("\n") for line in frame]

        if isinstance(frame, dict):
            for key in ("content", "frame", "text", "ascii"):
                value = frame.get(key)
                if isinstance(value, str):
                    return value.splitlines()
                if isinstance(value, list):
                    return [str(line).rstrip("\n") for line in value]

        return ["[invalid frame]"]

    def _measure_frames(self):
        self.max_height = 0
        self.max_width = 0
        for frame in self.frames:
            self.max_height = max(self.max_height, len(frame))
            self.max_width = max(self.max_width, max((len(line) for line in frame), default=0))

    def tick(self):
        now = time.monotonic()
        if now - self.last_advance >= self.frame_duration:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_advance = now

    def current_frame(self) -> List[str]:
        if not self.frames:
            return ["[no frames]"]
        return self.frames[self.frame_index]
