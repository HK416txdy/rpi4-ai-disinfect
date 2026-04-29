# Hardware Component

This is the hardware component of the AImachine project, intended for Raspberry Pi-specific hardware interfaces and deployment scripts.

Currently, hardware-related code (like camera detection) is integrated in the backend's machine_core module for simplicity. This folder is reserved for future hardware-specific extensions, such as:

- GPIO control scripts
- Hardware monitoring
- Raspberry Pi deployment configurations
- Sensor integrations

## Future Structure

- `gpio/`: GPIO control modules
- `sensors/`: Sensor reading interfaces
- `deployment/`: Pi-specific deployment scripts
- `camera/`: Advanced camera controls (if separated from backend)

## Setup

For Raspberry Pi deployment:

1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-opencv
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Notes

Hardware code is currently in `backend/src/machine_core/` for integrated operation. This separation allows for future modular hardware management.
