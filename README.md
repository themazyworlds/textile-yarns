# Textile Yarns (Official Capability Catalog)

This repository serves as the official monorepo catalog of first-party **Capability Yarns** for the [Textile](https://github.com/mazy/textile) AI OS & desktop agent framework.

---

## Catalog Index

| Yarn | Layer | Description | Dependencies |
| :--- | :--- | :--- | :--- |
| **caelestia** | 100 (Compositor/DE) | Caelestia desktop shell IPC, drawer, lock screen, and screenshot controls | System D-Bus |
| **canvas** | 100 (Compositor/DE) | Quickshell GTK desktop visual presence canvas overlay & emotive animations | Quickshell |
| **clipboard** | 50 (Middleware) | Clipboard read and write integration via wl-clipboard and xclip | `wl-clipboard`, `xclip` |
| **dbus_system** | 50 (Middleware) | D-Bus system and session bus inspection and call dispatching | `dbus-fast` |
| **filesystem** | 10 (Hardware/OS) | File viewing, editing, creation, directory analysis, and search | Standard Library |
| **hyprland** | 100 (Compositor/DE) | Hyprland compositor IPC, workspace navigation, and window controls | `hyprctl` |
| **journal** | 50 (Middleware) | Systemd journald logs inspection and query tool | `systemd-journal` |
| **packagekit** | 10 (Hardware/OS) | Linux PackageKit D-Bus package installation and update query | PackageKit D-Bus |
| **process** | 10 (Hardware/OS) | Process lifecycle management, list, priority, and signaling | Standard Library |
| **screen_vision**| 50 (Middleware) | Screen capture, OCR text extraction, and visual element detection | `grim`, `slurp`, `tesseract` |
| **sensors** | 10 (Hardware/OS) | Hardware sensors, telemetry, and CPU frequency reporting | `psutil` |
| **timer** | 10 (Hardware/OS) | Countdown timers and reminder notifications | Standard Library |
| **uwsm** | 150 (Companion) | Systemd and UWSM scope and session management integration | `uwsm` |
| **weave** | 150 (Companion) | Embedded LiveKit and Gemini Realtime voice companion client | `livekit-agents` |
| **web_research** | 10 (Hardware/OS) | Live internet search and web page text extraction | `httpx`, `trafilatura` |
| **ydotool** | 50 (Middleware) | Synthetic mouse and keyboard input events via ydotool / uinput | `ydotool` |

---

## Installation via Textile CLI

Install individual yarns directly using the Textile CLI:

```bash
# Install a yarn by path or URL
textile yarn install /path/to/textile-yarns/yarns/hyprland

# List all discovered and active yarns
textile yarn list

# Inspect discovery search paths
textile yarn paths
```

---

## Creating a New Yarn

Each yarn is a standalone directory with a manifest file (`<name>.toml` or `yarn.toml`) and an entry point Python class inheriting from `textile.Yarn`:

```toml
[yarn]
name = "my_custom_yarn"
version = "1.0.0"
manifest_version = 1
layer = 50
author = "Your Name"
description = "Description of the capability"
entry_point = "my_custom_yarn:MyCustomYarn"
dependencies = []

[capabilities]
read = true
write = false
network = false
```

```python
from textile import Yarn, Strand, strand

class MyCustomYarn(Yarn):
    def is_available(self) -> bool:
        return True

    @strand(description="Say hello", tier="observe")
    def say_hello(self, name: str) -> str:
        return f"Hello, {name}!"
```
