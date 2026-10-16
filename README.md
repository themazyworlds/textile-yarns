# Textile Yarns (Official Capability Catalog)

This repository serves as the official catalog of first-party **Capability Yarns** for the [Textile](https://github.com/themazyworlds/textile) AI OS & desktop agent framework.

Each yarn is a **100% self-contained, isolated capability directory** with its own `pyproject.toml` and dedicated virtual environment.

---

## Catalog Index

| Yarn | Layer | Tailor | Description |
| :--- | :--- | :--- | :--- |
| **caelestia** | 100 | textile | Caelestia desktop shell IPC, drawer, lock screen, and screenshot controls |
| **canvas** | 100 | textile | Quickshell GTK desktop visual presence canvas overlay & emotive animations |
| **clipboard** | 50 | textile | Clipboard read and write integration via wl-clipboard and xclip |
| **dbus_system** | 50 | textile | D-Bus system and session bus inspection and call dispatching |
| **filesystem** | 10 | textile | Inotify file watching, disk usage, and storage mounts |
| **hyprland** | 100 | textile | Hyprland compositor IPC, workspace navigation, and window controls |
| **journal** | 50 | textile | Systemd journald logs inspection and query tool |
| **packagekit** | 10 | textile | Linux PackageKit D-Bus package installation and update query |
| **process** | 10 | textile | Process lifecycle management, list, priority, and signaling |
| **screen_vision**| 10 | textile | Desktop screenshot capture and screen vision analysis |
| **sensors** | 10 | textile | Hardware sensors, telemetry, and CPU frequency reporting |
| **timer** | 10 | textile | Countdown timers and reminder notifications |
| **uwsm** | 150 | textile | Systemd and UWSM scope and session management integration |
| **weave** | 150 | textile | Embedded LiveKit and Gemini Realtime voice companion client |
| **web_research** | 10 | textile | Live internet search and web page text extraction |
| **ydotool** | 50 | textile | Synthetic mouse and keyboard input events via ydotool / uinput |

---

## Installation via Textile CLI

Install individual yarns directly using the Textile CLI:

```bash
# Install a yarn by local path or git URL
uv run textile yarns install /path/to/textile-yarns/yarns/hyprland
uv run textile yarns install https://github.com/themazyworlds/textile-yarn-hyprland

# List all discovered and active yarns
uv run textile yarns

# Inspect discovery search paths
uv run textile yarns paths
```

---

## Creating a New Capability Yarn

Each yarn is a self-contained directory containing a standard `pyproject.toml` and an entry point Python class inheriting from `needle.Yarn`:

### 1. `pyproject.toml`
```toml
[project]
name = "textile-yarn-media_control"
version = "1.0.0"
description = "Media player control integration"
authors = [{ name = "community" }]
requires-python = ">=3.15"
dependencies = [
    "needle>=0.1.0",
    "mpris2>=1.0.2",
]

[tool.textile]
tailor = "community"
layer = 50                       # Numeric priority (0 to 1000, higher overrides lower)
resources = ["bin:playerctl", "socket:/run/user/1000/bus"]

[tool.textile.settings.default_player]
default = "spotify"
type = "str"
description = "Default media player client"
choices = ["spotify", "vlc", "firefox", "chromium"]
```

### 2. `media_control.py`
```python
from needle import Yarn, strand


class MediaControlYarn(Yarn):
    @strand.interact
    async def media_play_pause(self, target: str | None = None) -> str:
        """Play or pause media playback."""
        player = target or self.settings.default_player
        # Implementation...
        return f"Toggled media play/pause on {player}"
```
