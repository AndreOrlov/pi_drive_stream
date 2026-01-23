# Code

## Run commands (MainControl.py)

Raspberry Pi (venv example):
```bash
# Connect to Raspberry Pi
ssh pi@192.168.1.100

# Go to the project folder
cd ~/projects/KS0223-Keyestudio-Smart-Car-Kit-for-Raspberry-Pi/Code/RaspberryPi-Car

# Create venv (if not created yet)
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run
python3 MainControl.py
```

Client:
`python3 RaspberryPi-Client/interactive_client.py`
Note: Remote control is implemented only for `MainControl.py`.

Notes:
- The server binds to the Raspberry Pi local IP and port `5051`.
- Set `HOST` in `RaspberryPi-Client/interactive_client.py` to the Raspberry Pi IP.

## What is in the Code folder

- `RaspberryPi-Car/` - Raspberry Pi side code for motors, camera servos, and the TCP server.
- `RaspberryPi-Car/MainControl.py` - Main entry point for car control (TCP server + actions).
- `RaspberryPi-Car/Ai_recognition/` - Camera and AI demos: camera driver, color detection, color follow with PID, QR decode, face detection, and TensorFlow object detection.
- `RaspberryPi-Car/Ai_recognition/Ai5_face_detection/` - OpenCV Haar cascade models and a face detection demo.
- `RaspberryPi-Car/Ai_recognition/Ai6_TensorflowObject_recognition/` - TensorFlow object detection demo with a COCO model, label map, and Object Detection API sources.
- `RaspberryPi-Car/basic_project/` - Basic sensor and actuator demos: buzzer, tracking sensors, ultrasonic distance, servos, LED matrix, IR remote, motor tests, line tracking, following, and obstacle avoidance.
- `RaspberryPi-Car/OledModule/` - OLED display helper with Adafruit SSD1306 library, wrapper class, and font file.
- `RaspberryPi-Car/opencv_project/` - OpenCV image processing demos: read/show, grayscale, histogram, geometric transforms, filtering, edges, and drawing/text.
- `RaspberryPi-Client/interactive_client.py` - Keyboard client that sends control commands.
