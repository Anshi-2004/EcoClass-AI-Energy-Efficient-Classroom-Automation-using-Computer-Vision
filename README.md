

## Overview

The **AI Smart Classroom System** is an end-to-end IoT + Computer Vision project that eliminates manual AC management in classrooms. Using a live webcam feed, it:

1. **Detects students** in real time with YOLOv8 (nano model, 45% confidence threshold)
2. **Maps occupancy to AC level** using a smart 4-tier control algorithm
3. **Sends serial commands** to an Arduino Uno to light LEDs reflecting the AC state
4. **Displays everything** on a Streamlit dashboard with live metrics, logs, and manual overrides

No cloud required. Runs 100% locally on any laptop with a webcam.

---

## Features

| Feature | Description |
|---|---|
| **Live Camera Feed** | Real-time annotated webcam stream with bounding boxes |
| **YOLOv8n Detection** | Ultra-fast nano model — no GPU required |
| **Smart AC Control** | 4-tier occupancy-based temperature management |
| **Grace Period Logic** | 30-second delay + 5-frame consecutive buffer prevents false shutoffs |
| **Arduino Integration** | Serial commands drive LEDs on D8, D9, D10 |
| **Auto Reconnect** | Background thread keeps Arduino serial link alive |
| **Manual Override** | Force any AC level instantly from the sidebar |
| **Activity Logs** | Timestamped event log with colour-coded severity levels |
| **CSV Export** | Download the full session log with one click |
| **Premium Dark UI** | Glassmorphism dashboard with animated metrics |

---

## How It Works

```
+------------------+    +------------------+    +------------------+    +------------------+
|     Webcam       |    |    YOLOv8n       |    |  ACController    |    |    Arduino Uno   |
|   (OpenCV)       |--->|    detection     |--->|   (logic.py)     |--->|  LEDs on D8/D9/  |
|                  |    |   person_count   |    |   level 0-3      |    |      D10         |
+------------------+    +------------------+    +------------------+    +------------------+
                                                        |
                                                        v
                                            +------------------------+
                                            |   Streamlit Dashboard  |
                                            |   - Live metrics       |
                                            |   - Activity logs      |
                                            |   - Manual controls    |
                                            +------------------------+
```

### Occupancy to AC Level Mapping

| Students Detected | AC Level  | Temperature | Room Status   | LED State       |
|:-----------------:|:---------:|:-----------:|:-------------:|:---------------:|
| 0                 | OFF       | —           | Empty         | All OFF         |
| 1 – 5             | LOW       | 28 °C       | Low Occupancy | D8 ON           |
| 6 – 10            | HIGH      | 24 °C       | Moderate      | D8 + D9 ON      |
| 11+               | FULL HIGH | 20 °C       | High Occupancy| D8 + D9 + D10   |

### Smart Empty-Room Protection

The system uses two safety layers to prevent false AC shutoffs:

- **5-frame streak buffer** — Requires 5 consecutive zero-count frames before starting the countdown. This eliminates single-frame detection misses caused by motion blur or brief occlusion.
- **30-second grace period** — Once the room is confirmed empty, the system waits 30 seconds before cutting AC power, in case students briefly step out and return.

---

## Project Structure

```
MINOR/
|-- app.py                  # Streamlit dashboard — main entry point
|-- detection.py            # YOLOv8 person detection wrapper
|-- logic.py                # ACController — occupancy-to-AC-level logic
|-- arduino.py              # Serial communication with Arduino Uno
|-- arduino_classroom.ino   # Arduino sketch (upload to board)
|-- requirements.txt        # Python dependencies
|-- yolov8n.pt              # Pre-trained YOLOv8 nano weights (~6 MB)
`-- README.md               # This file
```

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- A webcam (built-in or USB)
- Arduino Uno + 3 LEDs (optional — for physical LED output)

### 1. Clone the Repository

```bash
git clone https://github.com/Anshi-2004/GovGuide-AI.git
cd GovGuide-AI
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

What gets installed:

| Package | Purpose |
|---|---|
| `ultralytics` | YOLOv8 model and inference engine |
| `opencv-python` | Webcam capture and frame processing |
| `streamlit` | Interactive dashboard UI |
| `numpy` | Array and image operations |
| `pyserial` | Arduino serial communication |

### 3. Run the Dashboard

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### 4. Start Detection

1. Select your Arduino **COM Port** in the sidebar (or leave it on AUTO)
2. Click **Start** — the webcam activates and detection begins
3. Watch metrics update in real time
4. Use **Manual Override** buttons to force any AC level
5. Click **Stop** to pause — Arduino resets to OFF automatically

---

## Arduino Setup

Skip this section if you want software-only mode. The system works without Arduino.

### Hardware Required

- Arduino Uno
- 3 LEDs (any colour) with 3 x 220-ohm resistors
- USB-A to USB-B cable

### Wiring

```
Arduino Uno
+-------------------------------+
|                               |
|  D8  --[220 ohm]--[LED1]-- GND  |   AC LOW
|  D9  --[220 ohm]--[LED2]-- GND  |   AC HIGH
|  D10 --[220 ohm]--[LED3]-- GND  |   AC FULL HIGH
|                               |
+-------------------------------+
```

### Upload the Sketch

1. Open `arduino_classroom.ino` in the Arduino IDE
2. Set **Board:** Arduino Uno and **Port:** your COM port
3. Click **Upload**
4. In the Streamlit sidebar, click **Reconnect**

> Note: Click **Release Port** in the sidebar before uploading a new sketch, then **Reconnect** afterwards.

### Serial Protocol

| Command byte | Meaning      | LED State           |
|:------------:|:------------:|:-------------------:|
| `0`          | AC OFF       | All LEDs off        |
| `1`          | AC LOW       | D8 on only          |
| `2`          | AC HIGH      | D8 + D9 on          |
| `3`          | AC FULL HIGH | D8 + D9 + D10 on    |

Each command is sent 3 times with a 50 ms gap to guarantee reliable delivery.

---

## Architecture

### Module Breakdown

#### `detection.py` — Vision Layer

Wraps the YOLOv8n model. On each video frame it returns:
- An annotated frame with bounding boxes drawn around detected persons
- `person_count` — integer count of humans in the frame
- `boxes` — raw bounding box coordinates

The model runs at 45% confidence threshold to balance accuracy against false positives.

#### `logic.py` — Intelligence Layer

`ACController` manages all state transitions:
- Maps person count to AC level (0 = OFF, 1 = LOW, 2 = HIGH, 3 = FULL HIGH)
- Tracks the empty-room countdown with a consecutive-frame guard (5 frames)
- Implements a 30-second grace period before switching the AC off
- Computes an energy-saving percentage based on current temperature vs. baseline
- Exposes `update(count)` for automatic control and `force_level(level)` for manual overrides

#### `arduino.py` — Hardware Layer

`ArduinoController` manages reliable serial I/O:
- Auto-detects available COM ports if set to AUTO
- Runs a background reconnect thread that retries every 5 seconds
- Thread-safe writes protected by a `threading.Lock`
- Each command is sent 3 times to guarantee reception
- Clean `disconnect()` and `reconnect()` lifecycle for sketch uploads

#### `app.py` — Presentation Layer

Full Streamlit dashboard:
- Session state management keeps the detection loop alive across reruns
- Live camera feed with approximately 20 FPS updates
- 5-metric header row: People Detected, Room Status, AC Status, Temperature, Energy Saving
- Animated high-occupancy alert when more than 25 students are detected
- Tabbed activity log with colour-coded severity plus one-click CSV download

---

## Dashboard Layout

```
+-------------------------------------------------------------------------+
|                      AI Smart Classroom System                          |
|          Intelligent Occupancy Detection & Energy-Efficient AC Control  |
+----------+----------+----------+----------+----------------------------+
|  People  |  Room    |  AC      |  Temp    |  Energy Saving             |
|    12    | Moderate |   ON     |  24 C    |     50%                    |
+----------+----------+----------+----------+----------------------------+
|  Live Camera Feed                |  Detection Details                  |
|                                  |  Persons: 12                        |
|  [webcam stream with             |  Temp: 24 C                         |
|   bounding boxes]                |  Energy Save: 50%                   |
|                                  |  FPS: 18.4                          |
|                                  |  [==========     ] Energy Bar       |
|                                  |  AC HIGH                            |
+----------------------------------+-------------------------------------+
|  Activity Log  |  Export Logs                                          |
|  [14:23:01] AC -> HIGH (students: 12)                                  |
|  [14:22:55] Camera opened successfully                                 |
+-------------------------------------------------------------------------+
```

---

## Configuration

Key parameters you can tune directly in the source files:

| Parameter | File | Default | Description |
|---|---|---|---|
| `conf` | `detection.py` | `0.45` | YOLOv8 detection confidence threshold |
| `EMPTY_DELAY` | `logic.py` | `30 s` | Grace period before AC turns off |
| `_ZERO_STREAK_NEEDED` | `logic.py` | `5 frames` | Consecutive zero-count frames to confirm empty room |
| `BAUD_RATE` | `arduino.py` | `9600` | Serial baud rate (must match the .ino sketch) |
| `RECONNECT_INTERVAL` | `arduino.py` | `5 s` | Retry interval for background Arduino reconnect |

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Computer Vision | Ultralytics YOLOv8n | latest |
| Video Capture | OpenCV | 4.x |
| Dashboard UI | Streamlit | latest |
| Hardware I/O | Arduino Uno via PySerial | 3.5+ |
| Language | Python | 3.10+ |

---

## Contributing

Contributions are welcome. Here is the standard workflow:


---

## License

This project is licensed under the **MIT License** — free to use, modify, and distribute.

---

## Author

**Anshi** — Minor Project, 2026

[![GitHub](https://img.shields.io/badge/GitHub-Anshi--2004-181717?style=for-the-badge&logo=github)](https://github.com/Anshi-2004)

*Built with Streamlit, YOLOv8, and Arduino*

---

<div align="center">

If this project helped you, please give it a star.

</div>
