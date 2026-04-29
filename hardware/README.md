# Hardware Component

This is the hardware component of the AImachine project, handling Raspberry Pi-specific hardware interfaces, camera detection, and sensor integrations.

## Structure

- `machine_core/`: Core hardware modules for camera detection and processing
  - `detector.py`: Stain detection using OpenCV
  - `raspberry_pi_camera.py`: Raspberry Pi camera interface
  - `new.py`: Advanced stain detection algorithms
  - `hardware_communicator.py`: Network communication with backend server

## Features

- 🔍 **Real-time Camera Detection** - Raspberry Pi camera integration
- 🧠 **Intelligent Stain Analysis** - OpenCV-based image processing
- 📊 **Gray Scale Analysis** - Pollution level assessment
- 🎥 **Continuous Capture** - Threaded video processing

## Setup

For Raspberry Pi deployment:

1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-opencv python3-picamera
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```python
from hardware.machine_core.raspberry_pi_camera import RaspberryPiStainDetector

detector = RaspberryPiStainDetector()
if detector.initialize_camera():
    results = detector.detect_stains_from_camera()
    detector.release_camera()
```

## Notes

Hardware modules are now properly separated from backend logic for better modularity and Raspberry Pi-specific optimizations.
