# Leaf Board 🌿

A terminal UI for homegrow monitoring with real-time system stats in retro style.

## Features

- **ASCII Cannabis Leaf**: Beautiful ASCII art display in neon orange
- **Real-time Monitoring**: Detailed CPU and RAM usage graphs with borders
- **Command Interface**: Interactive terminal input for commands
- **Retro Color Scheme**: Dark black background with neon orange accents
- **Bordered Graphs**: Clean ASCII borders around system metrics

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Commands

- `help` - Show available commands
- `clear` - Clear the output area
- `stats` - Display current CPU and RAM usage
- `quit` or `exit` - Exit the application

## Requirements

- Python 3.7+
- Terminal with minimum size 50x20
- `psutil` library

## Layout

```
┌─────────────────────────────────────────────────┐
│  🌿 ASCII Leaf    │  ┌CPU Usage Graph┐         │
│                   │  │  ███          │         │
│                   │  └──────────────┘         │
│                   │  ┌RAM Usage Graph┐         │
│                   │  │  ████         │         │
│                   │  └──────────────┘         │
│  CPU: XX% | RAM: XX%                          │
│─────────────────────────────────────────────────│
│  Output area for command results                │
│─────────────────────────────────────────────────│
│  > Command input                                │
└─────────────────────────────────────────────────┘
```

## License

MIT
