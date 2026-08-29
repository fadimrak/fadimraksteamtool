<img width="1257" height="807" alt="Ekran görüntüsü 2026-08-29 141219" src="https://github.com/user-attachments/assets/db1f5d6b-6708-41b2-83bf-6321ab198208" />
<img width="1253" height="807" alt="Ekran görüntüsü 2026-08-29 141042" src="https://github.com/user-attachments/assets/2d3e50a1-2943-4453-b370-419bba399cc3" />
# Fadimrak Steam Tool

Fadimrak Steam Tool is a comprehensive library, achievement, DLC, and account management utility developed for the Steam client. Built with a Python-based asynchronous backend architecture and a PyWebView-powered modern responsive user interface, it provides users with a fast, lightweight, and modular experience.

---

## Features

- **Game & Manifest Management:** Automatically resolves depot and manifest configurations for selected games via ManifestHub sources and integrates them directly into your local Steam library.
- **DLC Unlocker Integration:** Automatically detects, configures, and manages DLC unlockers (SmokeAPI, ScreamAPI, and Koaloader) across your game directories.
- **Steam Achievement Manager (SAM):** Directly interfaces with the Steamworks API via `steam_api64.dll` to inspect game achievements and statistics, allowing users to unlock or lock achievements individually or in bulk.
- **Card & Playtime Farmer (Idle Farmer):** Farms Steam trading cards and boosts playtime in the background without needing to launch the game binaries, using isolated background subprocesses. Includes full Windows System Tray integration for silent background operation.
- **Online-Fix Integration:** Automatically extracts and deploys multiplayer/network bypass patches for supported games into target game directories.
- **Multi-Account Manager:** Enables fast switching and session management between registered Steam accounts on the system.
- **Bilingual Interface (English & Turkish):** Full localization support with seamless runtime switching between English and Turkish across all pages, modals, notifications, and menus.
- **Modern Web Interface:** Hardware-accelerated, responsive UI running on Chromium / Edge-WebView2 engine with asynchronous Python-to-JS IPC bridge.

---

## Architecture & How It Works

The application is structured into two main layers:

1. **Frontend (UI):** Modern HTML5, CSS3, and JavaScript interface rendered inside PyWebView. Communicates with Python services through an asynchronous IPC bridge (`ui_web/bridge.py`).
2. **Backend & Core Engine:**
   - `core/installer.py`: Manifest downloads, archive extraction, and Steam config file management.
   - `core/achievement_manager.py`: Steamworks API integration and achievement state management.
   - `core/idle_farmer.py`: Ctypes and subprocess-based idle farming engine.
   - `core/dlc_unlocker.py`: SmokeAPI / ScreamAPI configuration generator.
   - `core/onlinefix.py`: Online-fix archive extraction and patch deployment.
   - `core/steam_account.py`: VDF and registry-based Steam account detection and switching module.
   - `core/tray_manager.py`: Windows System Tray notifications and background runner.

---

## Installation & Running from Source

### Prerequisites

- Windows 10 or Windows 11 (x64)
- Python 3.10 or newer
- Steam Client installed

### Steps

1. Clone the repository:
```bash
git clone https://github.com/fadimrak/fadimraksteamtool.git
cd fadimraksteamtool
```

2. Install the required Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

---

## Building & Packaging

A build script is provided to compile the project into a standalone `.exe` or an Inno Setup installer package.

### Prerequisites for Building

- `pyinstaller`
- Inno Setup 6 (Optional, required to generate the setup installer)

### Build Process

Run the `build.bat` script to start the automated build process:

```bat
build.bat
```

The script performs the following steps automatically:
1. Verifies required dependencies.
2. Uses `fadimrak.spec` to create the standalone executable at `dist/FadimrakSteamTool.exe`.
3. If Inno Setup is detected on the system, compiles `installer.iss` to produce the installer package in the `output/` directory.

---

## Project Structure

```text
fadimraksteamtool/
├── core/
│   ├── achievement_manager.py  # Achievement management and Steamworks integration
│   ├── dlc_unlocker.py         # DLC unlocker configuration module
│   ├── game_manager.py         # Installed games tracking and status
│   ├── idle_farmer.py          # Card drop and playtime farming engine
│   ├── installer.py            # Manifest downloading and installation service
│   ├── onlinefix.py            # Multiplayer patch integration
│   ├── steam_account.py        # Steam account manager
│   ├── steam_utils.py          # Steam directory and process utilities
│   └── tray_manager.py         # System Tray management and background notifications
├── ui_web/
│   ├── bridge.py               # Python <-> JS IPC communication bridge
│   ├── window.py               # PyWebView window configuration
│   └── static/                 # Frontend assets (HTML, CSS, JS, Images)
│       ├── css/                # Stylesheets
│       └── js/                 # Modular frontend logic & i18n localization
├── build.bat                   # Automated build and packaging script
├── config.py                   # Global application configuration
├── fadimrak.spec               # PyInstaller build specification
├── installer.iss               # Inno Setup installer script
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── steam_api.py                # Steam Web API and app list manager
├── steam_api64.dll             # Steamworks 64-bit API library
└── verison                     # Version information
```

---

## Disclaimer

This software is developed strictly for educational purposes, reverse engineering analysis, API examination, and security research. Any account restrictions (such as VAC or Game Bans) or other consequences resulting from the misuse of this tool are entirely the responsibility of the user. Please purchase licensed products to support original game and software developers.

---

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the `LICENSE` file for details.
