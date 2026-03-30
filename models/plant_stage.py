from pathlib import Path
from typing import List, Dict


class PlantStageLoader:
    """Loads and manages plant stage ASCII art."""

    def __init__(self, ascii_dir: str = "ascii"):
        self.ascii_dir = Path(ascii_dir)
        self.stages: Dict[int, List[str]] = {}
        self._load_stages()

    def _load_stages(self):
        """Load all stage files from the ascii directory."""
        for stage_num in range(10):  # stage_0 to stage_9
            stage_file = self.ascii_dir / f"stage_{stage_num}"
            if stage_file.exists():
                with stage_file.open("r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                    # Remove empty lines at the beginning and end
                    while lines and not lines[0].strip():
                        lines.pop(0)
                    while lines and not lines[-1].strip():
                        lines.pop()
                    self.stages[stage_num] = lines

    def get_stage(self, stage_num: int) -> List[str]:
        """Get ASCII art for a specific stage."""
        return self.stages.get(stage_num, ["[No art available]"])

    def get_stage_names(self) -> Dict[int, str]:
        """Get human-readable names for each stage."""
        return {
            0: "Empty Pot",
            1: "Seedling",
            2: "Sprout",
            3: "Young Plant",
            4: "Growing Plant",
            5: "Medium Plant",
            6: "Large Plant",
            7: "Mature Plant",
            8: "Flowering",
            9: "Harvest Ready"
        }
