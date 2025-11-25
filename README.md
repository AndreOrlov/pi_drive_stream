# Pi Drive Stream

Remote-controlled car with video streaming based on Raspberry Pi 5.

## Features

- **Low-latency video streaming** via WebRTC
- **Real-time control** over WebSocket
- **Camera control** with D-Pad interface (pan/tilt servos ready)
- **OSD (On-Screen Display)** — modular overlay system with crosshair, telemetry, and warnings
- **Emergency stop** functionality
- **Centralized configuration** system with validation
- **Responsive design** — mobile-friendly interface (Tailwind CSS)
- **Ready for ROS2 migration** — modular architecture with event bus

## Hardware Requirements

- Raspberry Pi 5 (or 4)
- Camera Module (CSI) — OV5647 or compatible
- DC motors with motor driver (planned)
- Power supply 2S LiPo (7.4V)

## Software Stack

- **Backend:** Python 3.13, FastAPI, aiortc, Pydantic
- **Video:** Picamera2 (libcamera), WebRTC
- **OSD:** OpenCV with modular layer system (crosshair, telemetry, warnings)
- **Frontend:** Vanilla JS, WebRTC API, Tailwind CSS
- **Control:** WebSocket, event-driven architecture
- **Config:** Centralized configuration with validation

## Installation

### On Raspberry Pi

1. **Clone the repository:**

```bash
cd ~/projects
git clone https://github.com/AndreOrlov/pi_drive_stream.git
cd pi_drive_stream
```

2. **Install system dependencies:**

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-libcamera libcamera-apps
sudo apt install -y python3-opencv libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavfilter-dev
```

3. **Install pigpio for servo control:**

If pigpio is not available in your repositories, install from source:

```bash
# Download and install pigpio daemon and library
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make
sudo make install
cd ..
rm -rf pigpio-master master.zip
```

Alternatively, if available in repos (Raspberry Pi OS Bookworm and newer):

```bash
sudo apt install -y pigpio
```

4. **Enable pigpiod daemon auto-start:**

The pigpiod daemon must be running for servo control to work.

**If installed from source**, create systemd service:

```bash
# Create systemd unit file
sudo tee /etc/systemd/system/pigpiod.service > /dev/null << 'EOF'
[Unit]
Description=Pigpio daemon
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/pigpiod
ExecStop=/bin/systemctl kill pigpiod
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable
sudo systemctl daemon-reload
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

**If installed from apt**, simply enable:

```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

Check daemon status:

```bash
sudo systemctl status pigpiod
```

You should see "active (running)" in the output.

**Alternative: Manual start** (without systemd):

```bash
sudo pigpiod
```

5. **Create virtual environment with system packages:**

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
```

6. **Install Python dependencies (including pigpio):**

```bash
pip install -r requirements.txt
pip install pigpio
```

7. **Run the server:**

```bash
# Quick start (recommended)
./start.sh

# Or manually
python main.py
```

8. **Open in browser:**

```
http://<raspberry-pi-ip>:8000
```

### On macOS (development without camera)

1. **Clone and setup:**

```bash
git clone https://github.com/AndreOrlov/pi_drive_stream.git
cd pi_drive_stream
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Run:**

```bash
# Quick start
./start.sh

# Or manually
python main.py
```

The app will fall back to OpenCV camera (built-in webcam) if Picamera2 is not available.

## Project Structure

```
pi_drive_stream/
├── app/
│   ├── bus.py              # Event bus (mini-ROS pub/sub)
│   ├── config.py           # Centralized configuration (Pydantic)
│   ├── messages.py         # Message types (DriveCommand, CameraCommand, etc.)
│   ├── video.py            # WebRTC video streaming with Picamera2
│   ├── nodes/
│   │   ├── drive.py        # Drive control node (with timeout safety)
│   │   └── camera.py       # Camera control node
│   ├── hw/
│   │   ├── servos.py       # Camera servo control (pigpio implementation)
│   │   └── motors_stub.py  # Drive motor control stub (TODO: GPIO/PWM)
│   ├── overlay/
│   │   ├── base.py         # OSD interfaces (Protocol, ABC)
│   │   ├── cv_renderer.py  # OpenCV OSD renderer
│   │   └── layers/         # OSD layers (crosshair, telemetry, warnings)
│   └── web/
│       └── server.py       # FastAPI server, WebSocket, WebRTC signaling
├── frontend/
│   ├── index.html          # Web UI (Tailwind CSS, responsive)
│   └── main.js             # WebRTC client, controls
├── tests/
│   ├── test_overlay_layers.py  # OSD layers tests
│   ├── test_cv_renderer.py     # Renderer tests
│   └── test_config.py          # Configuration tests
├── main.py                 # Entry point
├── start.sh                # Quick start script
├── requirements.txt        # Python dependencies
├── CONFIG.md               # Configuration guide
└── PLAN_OSD.md             # OSD system architecture and roadmap
```

## Architecture

The project follows a **node-based architecture** inspired by ROS2:

- **Event Bus** (`app/bus.py`) — async pub/sub for internal communication
- **Nodes** — independent components (drive, camera) subscribed to topics
- **Messages** — typed data structures (DriveCommand, CameraCommand)
- **WebRTC** — low-latency video with custom `CameraVideoTrack` + `MediaRelay`
- **WebSocket** — bidirectional control channel

### Event Flow

```
Browser → WebSocket → Event Bus → Drive Node → Motor Control (stub)
                                → Camera Node → Camera Control (stub)

Camera (Picamera2) → CameraVideoTrack → MediaRelay → WebRTC → Browser
```

## Control Interface

### Keyboard (planned)
- **W/↑** — Forward
- **S/↓** — Backward
- **A/←** — Left
- **D/→** — Right
- **Space** — Emergency Stop

### Touch/Click (current)

#### Drive Control
- **Forward** — Drive forward at full speed
- **Backward** — Reverse at full speed
- **Left** — Turn left at half speed
- **Right** — Turn right at half speed
- **STOP** — Emergency stop

#### Camera Control (D-Pad)
- **▲/▼** — Tilt camera up/down
- **◀/▶** — Pan camera left/right
- **●** (HOME) — Reset camera to center
- **Click** — Discrete step movement
- **Hold** — Continuous smooth movement

### Gamepad (planned)
- Left stick — steering
- Right trigger — throttle
- Right bumper — emergency stop

## Safety Features

- **Command timeout** — motors stop if no commands received for 0.5s
- **Emergency stop** — immediately sets mode to `EMERGENCY_STOP`
- **Graceful degradation** — falls back to OpenCV if Picamera2 unavailable

## Configuration

All settings are centralized in `app/config.py` using Pydantic for validation.

See **[CONFIG.md](CONFIG.md)** for complete configuration guide.

### Quick Examples

**Change video resolution (for low-power Pi):**
```python
# app/config.py
video=VideoConfig(
    width=320,
    height=240,
    fps=15
)
```

**Change server port:**
```python
# app/config.py
server=ServerConfig(
    port=8080
)
```

**Disable camera control logging:**
```python
# app/config.py
camera=CameraConfig(
    enable_logging=False
)
```

**Invert camera axes (if servos mounted backwards):**
```python
# app/config.py
camera=CameraConfig(
    invert_pan=True,
    invert_tilt=False
)
```

**Переворот изображения (если камера установлена вверх ногами):**
```python
# app/config.py
video=VideoConfig(
    flip_vertical=True,
    flip_horizontal=True
)
```

**Configure OSD (On-Screen Display):**
```python
# app/config.py
overlay=OverlayConfig(
    enabled=True,      # Enable/disable OSD
    crosshair=True,    # Show crosshair
    telemetry=True,    # Show date/time
    warnings=False,    # Hide warnings
)
```

Configuration is loaded via `/api/config` endpoint and synced with frontend automatically.

## Network Access

### Local Network
Access directly via `http://<pi-ip>:8000`

### VPN (recommended for internet access)
Use Tailscale, WireGuard, or ZeroTier for secure remote access.

### Port Forwarding (not recommended)
If exposing to internet, add authentication (not implemented yet).

## Troubleshooting

### Camera not detected

```bash
# Check camera
rpicam-hello
libcamera-hello  # on older systems

# Check /dev/video*
ls -la /dev/video*
```

### "Device or resource busy"

Camera already in use. Stop other processes:

```bash
pkill -9 -f python
pkill -9 rpicam
```

### WebRTC black screen

- Check browser console for errors
- Try hard refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
- Check if camera works: `rpicam-hello`

### High latency

- Reduce resolution in `app/video.py` (e.g., 320x240)
- Check network bandwidth
- Disable other services on Pi

### Servo not moving / "Cannot connect to pigpiod"

Make sure the pigpiod daemon is running:

```bash
sudo systemctl status pigpiod
```

If systemd service doesn't exist (installed from source):

```bash
# Start manually
sudo pigpiod

# Or create systemd service (see installation section)
```

If service exists but not running:

```bash
sudo systemctl start pigpiod
sudo systemctl enable pigpiod  # enable auto-start on boot
```

Check if daemon is actually running:

```bash
pgrep pigpiod  # should return a process ID
```

Check servo connections:
- Pan servo → GPIO 17 (physical pin 11)
- Tilt servo → GPIO 18 (physical pin 12)
- Verify power supply (servos need 5V, not 3.3V)
- Common (brown/black wire) → GND
- Power (red wire) → 5V
- Signal (orange/yellow/white wire) → GPIO pin

## Development

### Quick Start Script

The project includes `start.sh` for convenient one-command launch:

```bash
./start.sh
```

**Features:**
- ✅ Automatically activates virtual environment
- ✅ Checks if pigpiod is running (on Raspberry Pi)
- ✅ Shows helpful warnings if setup is incomplete
- ✅ Starts the server with proper error handling

### Running with auto-reload

```bash
python main.py  # uvicorn with --reload enabled
```

### Viewing logs

Logs go to stdout. Increase verbosity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing camera

```bash
# On Raspberry Pi
rpicam-vid -t 10000 --inline -o test.h264
```

### Running tests

The project includes comprehensive unit tests for the OSD system:

```bash
# Install pytest (if not already installed)
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_overlay_layers.py -v

# Run with coverage (optional)
pip install pytest-cov
pytest tests/ --cov=app/overlay --cov-report=term-missing
```

**Test coverage:**
- OSD layers (crosshair, telemetry, warnings)
- OpenCV renderer
- Configuration validation
- Multiple resolutions support

All tests run without hardware dependencies (no camera or GPIO required).

## CI/CD

The project uses GitHub Actions for continuous integration:

- **Automated testing** on every push and pull request
- **Code linting** with ruff
- **Type checking** with mypy (warnings only)
- **Branch protection** for `dev` and `master`

### GitHub Actions Workflow

The CI pipeline runs:
1. Install dependencies
2. Run ruff linter
3. Run mypy type checker
4. Run pytest with coverage

### Pre-commit Hooks (optional)

Install pre-commit hooks to run checks locally before committing:

```bash
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Branch Protection

- **master**: Requires PR approval + passing CI
- **dev**: Requires PR approval + passing CI
- Direct push allowed only for repository owner

See `.github/BRANCH_PROTECTION.md` for setup instructions.

## Future Plans

- [ ] Real motor control (GPIO/PWM via `pigpio` or `lgpio`)
- [x] Camera control UI (D-Pad interface)
- [x] Camera servo hardware integration (pan/tilt with pigpio on GPIO 18)
- [x] OSD system with modular layers (crosshair, telemetry, warnings)
- [ ] Dynamic telemetry overlay (battery, speed, servo angles, FPS)
- [ ] Hardware-accelerated OSD (Picamera2 DRM overlays, GStreamer)
- [ ] Gamepad support (Gamepad API)
- [ ] Recording to file
- [ ] Multiple camera support
- [ ] **Migration to ROS2** — seamless transition with minimal code changes

## ROS2 Migration Path

The architecture is designed for easy ROS2 migration:

1. **Event Bus** → ROS2 Topics (`std_msgs`, `geometry_msgs/Twist`)
2. **Nodes** → ROS2 Nodes (`rclpy`)
3. **Messages** → ROS2 Messages (`.msg` files)
4. **WebRTC** → Keep as bridge node or use `web_video_server`

## License

MIT

## Author

Andrey Orlov (@AndreOrlov)

## Contributing

This is a personal learning project, but PRs are welcome!
