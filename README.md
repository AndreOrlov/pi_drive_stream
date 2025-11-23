# Pi Drive Stream

Remote-controlled car with video streaming based on Raspberry Pi 5.

## Features

- **Low-latency video streaming** via WebRTC
- **Real-time control** over WebSocket
- **Emergency stop** functionality
- **Ready for ROS2 migration** — modular architecture with event bus

## Hardware Requirements

- Raspberry Pi 5 (or 4)
- Camera Module (CSI) — OV5647 or compatible
- DC motors with motor driver (planned)
- Power supply 2S LiPo (7.4V)

## Software Stack

- **Backend:** Python 3.13, FastAPI, aiortc
- **Video:** Picamera2 (libcamera), WebRTC
- **Frontend:** Vanilla JS, WebRTC API
- **Control:** WebSocket, event-driven architecture

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

3. **Create virtual environment with system packages:**

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
```

4. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

5. **Run the server:**

```bash
python main.py
```

6. **Open in browser:**

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
python main.py
```

The app will fall back to OpenCV camera (built-in webcam) if Picamera2 is not available.

## Project Structure

```
pi_drive_stream/
├── app/
│   ├── bus.py              # Event bus (mini-ROS pub/sub)
│   ├── messages.py         # Message types (DriveCommand, CameraCommand, etc.)
│   ├── video.py            # WebRTC video streaming with Picamera2
│   ├── nodes/
│   │   ├── drive.py        # Drive control node (with timeout safety)
│   │   └── camera.py       # Camera control node
│   ├── hw/
│   │   └── motors_stub.py  # Motor control stubs (TODO: GPIO/PWM)
│   └── web/
│       └── server.py       # FastAPI server, WebSocket, WebRTC signaling
├── frontend/
│   ├── index.html          # Web UI
│   └── main.js             # WebRTC client, controls
├── main.py                 # Entry point
└── requirements.txt        # Python dependencies
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
- **Forward** — Drive forward at full speed
- **Backward** — Reverse at full speed
- **Left** — Turn left at half speed
- **Right** — Turn right at half speed
- **STOP** — Emergency stop

### Gamepad (planned)
- Left stick — steering
- Right trigger — throttle
- Right bumper — emergency stop

## Safety Features

- **Command timeout** — motors stop if no commands received for 0.5s
- **Emergency stop** — immediately sets mode to `EMERGENCY_STOP`
- **Graceful degradation** — falls back to OpenCV if Picamera2 unavailable

## Configuration

Edit `app/web/server.py` to change:

```python
drive_node = DriveNode(timeout_s=0.5)  # Command timeout
```

Edit `app/video.py` to change camera resolution:

```python
config = cam.create_preview_configuration(
    main={"format": "RGB888", "size": (640, 480)}  # Resolution
)
```

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

## Development

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

## Future Plans

- [ ] Real motor control (GPIO/PWM via `pigpio` or `lgpio`)
- [ ] Camera servo control (pan/tilt)
- [ ] Telemetry overlay on video (battery, FPS, signal strength)
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

