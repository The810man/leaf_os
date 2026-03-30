import curses
import time
import random
from typing import List, Dict, Any

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation
from pages.base_page import BasePage
from ui.panels import draw_text, rounded_box


# ASCII MQTT Logo
MQTT_LOGO = [
    "    ╔══════════════════════════════════════╗",
    "    ║         MQTT MESSAGE BROKER          ║",
    "    ╠══════════════════════════════════════╣",
    "    ║                                      ║",
    "    ║    ┌─────────┐      ┌─────────┐      ║",
    "    ║    │ PUBLISH │ ───► │SUBSCRIBE│      ║",
    "    ║    └─────────┘      └─────────┘      ║",
    "    ║         │                ▲            ║",
    "    ║         │                │            ║",
    "    ║         ▼                │            ║",
    "    ║    ┌─────────────────────────┐        ║",
    "    ║    │      MESSAGE BROKER     │        ║",
    "    ║    │   ┌───┐ ┌───┐ ┌───┐   │        ║",
    "    ║    │   │ Q │ │ Q │ │ Q │   │        ║",
    "    ║    │   └───┘ └───┘ └───┘   │        ║",
    "    ║    └─────────────────────────┘        ║",
    "    ║                                      ║",
    "    ╚══════════════════════════════════════╝",
]


class MQTTPage(BasePage):
    """MQTT overview page with mock data."""

    def __init__(self):
        super().__init__("mqtt")
        self.mock_topics = [
            "sensors/temperature",
            "sensors/humidity",
            "sensors/soil_moisture",
            "devices/pump",
            "devices/light",
            "devices/fan",
        ]
        self.mock_messages: List[Dict[str, Any]] = []
        self.last_update = 0.0
        self.update_interval = 2.0
        self.connection_status = "CONNECTED"
        self.broker_address = "localhost:1883"
        self.client_id = "leaf_board_client"

    def get_title(self) -> str:
        return " MQTT OVERVIEW "

    def _generate_mock_message(self) -> Dict[str, Any]:
        """Generate a mock MQTT message."""
        topic = random.choice(self.mock_topics)
        if "temperature" in topic:
            value = round(random.uniform(18.0, 28.0), 1)
            payload = f'{{"value": {value}, "unit": "°C"}}'
        elif "humidity" in topic:
            value = round(random.uniform(40.0, 70.0), 1)
            payload = f'{{"value": {value}, "unit": "%"}}'
        elif "soil_moisture" in topic:
            value = round(random.uniform(20.0, 80.0), 1)
            payload = f'{{"value": {value}, "unit": "%"}}'
        elif "pump" in topic:
            status = random.choice(["ON", "OFF"])
            payload = f'{{"status": "{status}"}}'
        elif "light" in topic:
            status = random.choice(["ON", "OFF"])
            intensity = random.randint(0, 100)
            payload = f'{{"status": "{status}", "intensity": {intensity}}}'
        else:  # fan
            status = random.choice(["ON", "OFF"])
            speed = random.randint(1, 3)
            payload = f'{{"status": "{status}", "speed": {speed}}}'

        return {
            "topic": topic,
            "payload": payload,
            "timestamp": time.strftime("%H:%M:%S"),
            "qos": random.choice([0, 1, 2]),
        }

    def _update_mock_data(self):
        """Update mock MQTT data."""
        now = time.monotonic()
        if now - self.last_update >= self.update_interval:
            # Add 1-3 new messages
            for _ in range(random.randint(1, 3)):
                self.mock_messages.append(self._generate_mock_message())
            # Keep only last 20 messages
            self.mock_messages = self.mock_messages[-20:]
            self.last_update = now

    def draw(self, stdscr, y: int, x: int, h: int, w: int,
             monitor: SystemMonitor, animation: AsciiAnimation):
        """Draw the MQTT overview page."""
        self._update_mock_data()

        # Draw MQTT logo on the left
        logo_w = len(MQTT_LOGO[0]) if MQTT_LOGO else 0
        logo_h = len(MQTT_LOGO)
        logo_x = x + 2
        logo_y = y + 1

        for i, line in enumerate(MQTT_LOGO):
            if logo_y + i < h - 2:
                draw_text(stdscr, logo_y + i, logo_x, line, 8)

        # Draw connection info
        info_x = x + 2
        info_y = y + logo_h + 2
        if info_y < h - 10:
            rounded_box(stdscr, info_y, info_x, 8, 40, " CONNECTION ", 1)
            draw_text(stdscr, info_y + 2, info_x + 3, f"Status: {self.connection_status}", 8, True)
            draw_text(stdscr, info_y + 3, info_x + 3, f"Broker: {self.broker_address}", 3)
            draw_text(stdscr, info_y + 4, info_x + 3, f"Client: {self.client_id}", 3)
            draw_text(stdscr, info_y + 5, info_x + 3, f"Topics: {len(self.mock_topics)}", 3)

        # Draw message log on the right
        log_x = x + 45
        log_w = w - 47
        if log_w > 20:
            rounded_box(stdscr, y, log_x, h - 2, log_w, " MESSAGE LOG ", 1)
            
            # Draw messages
            msg_y = y + 1
            for msg in self.mock_messages[-(h - 5):]:
                if msg_y >= h - 3:
                    break
                # Topic
                topic_str = f"[{msg['timestamp']}] {msg['topic']}"
                draw_text(stdscr, msg_y, log_x + 2, topic_str[:log_w - 4], 2, True)
                msg_y += 1
                # Payload
                payload_str = msg['payload'][:log_w - 4]
                draw_text(stdscr, msg_y, log_x + 4, payload_str, 3)
                msg_y += 1
                # QoS
                qos_str = f"QoS: {msg['qos']}"
                draw_text(stdscr, msg_y, log_x + 4, qos_str, 7)
                msg_y += 2

        # Draw topic list
        topics_x = x + 2
        topics_y = info_y + 9 if info_y < h - 10 else y + logo_h + 2
        if topics_y < h - 8:
            rounded_box(stdscr, topics_y, topics_x, len(self.mock_topics) + 3, 40, " SUBSCRIBED TOPICS ", 1)
            for i, topic in enumerate(self.mock_topics):
                if topics_y + 2 + i < h - 2:
                    draw_text(stdscr, topics_y + 2 + i, topics_x + 3, f"• {topic}", 3)
