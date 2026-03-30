import curses
import time
from typing import List, Dict, Any, Optional

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation
from models.plant_stage import PlantStageLoader
from pages.base_page import BasePage
from ui.panels import draw_text, rounded_box
from renderers.frame_utils import fit_frame_to_box


class Plant:
    """Represents a plant with its status."""

    def __init__(self, plant_id: int, name: str, strain: str, stage: int, 
                 needs_water: bool, can_harvest: bool, days_in_stage: int):
        self.plant_id = plant_id
        self.name = name
        self.strain = strain
        self.stage = stage  # 0-9
        self.needs_water = needs_water
        self.can_harvest = can_harvest
        self.days_in_stage = days_in_stage

    def get_status_color(self) -> int:
        """Get color based on plant status."""
        if self.can_harvest:
            return 8  # Green - ready to harvest
        elif self.needs_water:
            return 6  # Red - needs water
        elif self.stage == 0:
            return 7  # Cyan - empty
        else:
            return 4  # Green - healthy


class PlantStatusPage(BasePage):
    """Plant status page showing multiple plants."""

    def __init__(self):
        super().__init__("plants")
        self.stage_loader = PlantStageLoader()
        # Mock data: 6 plants - 2 active, 4 empty
        self.plants: List[Plant] = [
            Plant(1, "Plant Alpha", "Northern Lights", 3, False, False, 5),
            Plant(2, "Plant Beta", "White Widow", 1, False, False, 2),
            Plant(3, "Plant Gamma", "Empty", 0, False, False, 0),
            Plant(4, "Plant Delta", "Empty", 0, False, False, 0),
            Plant(5, "Plant Epsilon", "Empty", 0, False, False, 0),
            Plant(6, "Plant Zeta", "Empty", 0, False, False, 0),
        ]
        self.current_plant_index = 0
        self.last_update = 0.0
        self.update_interval = 5.0
        self.creation_mode = False
        self.creation_step = 0
        self.creation_data: Dict[str, str] = {}

    def get_title(self) -> str:
        return " PLANT STATUS "

    def _update_mock_data(self):
        """Update mock plant data periodically."""
        now = time.monotonic()
        if now - self.last_update >= self.update_interval:
            # Simulate plant growth and status changes
            for plant in self.plants:
                if plant.stage > 0:
                    plant.days_in_stage += 1
                    # Random chance to need water
                    if plant.days_in_stage % 3 == 0:
                        plant.needs_water = not plant.needs_water
            self.last_update = now

    def draw(self, stdscr, y: int, x: int, h: int, w: int,
             monitor: SystemMonitor, animation: AsciiAnimation):
        """Draw the plant status page with multiple pots."""
        self._update_mock_data()

        # Draw page header
        draw_text(stdscr, y, x + 2, "╔══════════════════════════════════════════════════════════════╗", 1)
        draw_text(stdscr, y + 1, x + 2, "║                    CULTIVATION MONITOR                      ║", 2, True)
        draw_text(stdscr, y + 2, x + 2, "╚══════════════════════════════════════════════════════════════╝", 1)

        # Draw navigation header
        nav_y = y + 4
        draw_text(stdscr, nav_y, x + 2, f"Showing {len(self.plants)} plants │ Press 1-6 to select │ 'c' to create new plant", 7)

        # Draw plants in a grid (3 columns)
        plant_start_x = x + 2
        plant_start_y = nav_y + 2
        plant_width = 25
        plant_height = 20
        cols = 3

        for i, plant in enumerate(self.plants):
            col = i % cols
            row = i // cols
            px = plant_start_x + col * (plant_width + 2)
            py = plant_start_y + row * (plant_height + 2)

            if py + plant_height >= h - 2:
                break

            # Draw plant box
            color = plant.get_status_color()
            stage_name = self.stage_loader.get_stage_names().get(plant.stage, "Unknown")
            
            # Box title with strain name
            if plant.stage == 0:
                box_title = f" {plant.name} - EMPTY "
            else:
                box_title = f" {plant.name} - {plant.strain} "
            
            rounded_box(stdscr, py, px, plant_height, plant_width, box_title, color)

            # Draw plant ASCII art
            stage_art = self.stage_loader.get_stage(plant.stage)
            if stage_art:
                # Calculate inner dimensions for the art
                inner_w = plant_width - 4
                inner_h = plant_height - 8  # Leave space for info text
                
                # Fit the art to the container
                fitted_art = fit_frame_to_box(stage_art, inner_w, inner_h, char_aspect=1.0)
                
                # Draw the fitted art
                art_y = py + 1
                for line in fitted_art:
                    if art_y < py + plant_height - 7:
                        draw_text(stdscr, art_y, px + 2, line, color)
                        art_y += 1

            # Draw plant info below the art
            info_y = py + plant_height - 7
            if info_y < py + plant_height - 1:
                draw_text(stdscr, info_y, px + 2, f"Stage: {stage_name}", 3, True)
                info_y += 1
            if info_y < py + plant_height - 1:
                draw_text(stdscr, info_y, px + 2, f"Days: {plant.days_in_stage}", 3)
                info_y += 1
            if info_y < py + plant_height - 1:
                water_status = "YES" if plant.needs_water else "NO"
                water_color = 6 if plant.needs_water else 4
                draw_text(stdscr, info_y, px + 2, f"Water: {water_status}", water_color)
                info_y += 1
            if info_y < py + plant_height - 1:
                harvest_status = "YES" if plant.can_harvest else "NO"
                harvest_color = 8 if plant.can_harvest else 7
                draw_text(stdscr, info_y, px + 2, f"Harvest: {harvest_status}", harvest_color)

        # Draw legend at the bottom
        legend_y = h - 6
        if legend_y > plant_start_y + 10:
            rounded_box(stdscr, legend_y, x + 2, 5, w - 4, " LEGEND ", 1)
            draw_text(stdscr, legend_y + 2, x + 5, "Stages: 0=Empty │ 1=Seedling │ 2=Sprout │ 3=Young │ 4=Growing │ 5=Medium │ 6=Large │ 7=Mature │ 8=Flowering │ 9=Harvest", 3)
            draw_text(stdscr, legend_y + 3, x + 5, "Commands: water <id> │ harvest <id> │ create │ remove <id> │ 1-6 (select plant)", 7)

    def handle_input(self, key: int, output_lines: List[str]) -> bool:
        """Handle input for plant navigation and creation."""
        if self.creation_mode:
            return self._handle_creation_input(key, output_lines)
        
        # Plant navigation with number keys
        if key in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5"), ord("6")):
            plant_num = int(chr(key))
            if 1 <= plant_num <= len(self.plants):
                self.current_plant_index = plant_num - 1
                output_lines.append(f"Selected plant {plant_num}: {self.plants[self.current_plant_index].name}")
                return True
        
        # Create new plant
        if key == ord("c"):
            self.creation_mode = True
            self.creation_step = 0
            self.creation_data = {}
            output_lines.append("Entering plant creation mode...")
            return True
        
        return False

    def _handle_creation_input(self, key: int, output_lines: List[str]) -> bool:
        """Handle input during plant creation."""
        if key == 27:  # ESC
            self.creation_mode = False
            output_lines.append("Plant creation cancelled.")
            return True
        
        if key in (10, 13, curses.KEY_ENTER):  # ENTER
            steps = ["name", "strain"]
            if self.creation_step < len(steps):
                current_key = steps[self.creation_step]
                if current_key in self.creation_data and self.creation_data[current_key]:
                    self.creation_step += 1
                    if self.creation_step >= len(steps):
                        # Find first empty pot
                        empty_pot_index = None
                        for i, plant in enumerate(self.plants):
                            if plant.stage == 0:
                                empty_pot_index = i
                                break
                        
                        if empty_pot_index is not None:
                            # Update the empty pot
                            self.plants[empty_pot_index].name = self.creation_data.get("name", f"Plant {empty_pot_index + 1}")
                            self.plants[empty_pot_index].strain = self.creation_data.get("strain", "Unknown")
                            self.plants[empty_pot_index].stage = 1  # Start as seedling
                            output_lines.append(f"Created new plant: {self.plants[empty_pot_index].name} ({self.plants[empty_pot_index].strain})")
                        else:
                            # Add new plant
                            new_id = len(self.plants) + 1
                            new_plant = Plant(
                                new_id,
                                self.creation_data.get("name", f"Plant {new_id}"),
                                self.creation_data.get("strain", "Unknown"),
                                1,  # Start as seedling
                                False,
                                False,
                                0
                            )
                            self.plants.append(new_plant)
                            output_lines.append(f"Created new plant: {new_plant.name} ({new_plant.strain})")
                else:
                    output_lines.append("Please enter a value before pressing ENTER.")
            else:
                self.creation_mode = False
                output_lines.append("Plant creation complete!")
            return True
        
        # Backspace
        if key in (curses.KEY_BACKSPACE, 127, 8):
            steps = ["name", "strain"]
            if self.creation_step < len(steps):
                current_key = steps[self.creation_step]
                if current_key in self.creation_data:
                    self.creation_data[current_key] = self.creation_data[current_key][:-1]
            return True
        
        # Regular character input
        if 32 <= key <= 126:
            steps = ["name", "strain"]
            if self.creation_step < len(steps):
                current_key = steps[self.creation_step]
                if current_key not in self.creation_data:
                    self.creation_data[current_key] = ""
                self.creation_data[current_key] += chr(key)
            return True
        
        return False
