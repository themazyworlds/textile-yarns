# Textile Yarns (Official Capability Catalog)

This repository serves as the official catalog of first-party **Capability Yarns** for the [Textile](https://github.com/mazy/textile) AI OS & desktop agent framework.

Each yarn is a **100% self-contained, isolated capability directory** with its own `pyproject.toml` and dedicated virtual environment.

---

## Catalog Index

| Yarn | Layer | Tailor | Description |
| :--- | :--- | :--- | :--- |
| **caelestia** | 100 (Compositor/DE) | textile | Caelestia desktop shell IPC, drawer, lock screen, and screenshot controls |
| **canvas** | 100 (Compositor/DE) | textile | Quickshell GTK desktop visual presence canvas overlay & emotive animations |
| **clipboard** | 50 (Middleware) | textile | Clipboard read and write integration via wl-clipboard and xclip |
| **dbus_system** | 50 (Middleware) | textile | D-Bus system and session bus inspection and call dispatching |
| **filesystem** | 10 (Hardware/OS) | textile | Inotify file watching, disk usage, and storage mounts |
| **hyprland** | 100 (Compositor/DE) | textile | Hyprland compositor IPC, workspace navigation, and window controls |
| **journal** | 50 (Middleware) | textile | Systemd journald logs inspection and query tool |
| **packagekit** | 10 (Hardware/OS) | textile | Linux PackageKit D-Bus package installation and update query |
| **process** | 10 (Hardware/OS) | textile | Process lifecycle management, list, priority, and signaling |
| **screen_vision**| 50 (Middleware) | textile | Desktop screenshot capture and screen vision analysis |
| **sensors** | 10 (Hardware/OS) | textile | Hardware sensors, telemetry, and CPU frequency reporting |
| **timer** | 10 (Hardware/OS) | textile | Countdown timers and reminder notifications |
| **uwsm** | 150 (Companion) | textile | Systemd and UWSM scope and session management integration |
| **weave** | 150 (Companion) | textile | Embedded LiveKit and Gemini Realtime voice companion client |
| **web_research** | 10 (Hardware/OS) | textile | Live internet search and web page text extraction |
| **ydotool** | 50 (Middleware) | textile | Synthetic mouse and keyboard input events via ydotool / uinput |

---

## Installation via Textile CLI

Install individual yarns directly using the Textile CLI:

```bash
# Install a yarn by local path or git URL
textile yarn install /path/to/textile-yarns/yarns/hyprland
textile yarn install https://github.com/mazy/textile-yarn-hyprland

# List all discovered and active yarns
textile yarn list
textile yarns

# Inspect discovery search paths
textile yarn paths
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
layer = 50                       # 0 (Core), 50 (Protocol/Default), 100 (Compositor), 150 (Session), 1000 (User)
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
