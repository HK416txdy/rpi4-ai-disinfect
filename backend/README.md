# Backend Component

This is the backend component of the AImachine project, handling API routes, core logic, data management, and the Flask application.

## Structure

- `api/`: API routes for authentication, machines, detection, etc.
- `src/`: Core source code, including data management.
- `config/`: Configuration files.
- `data/`: Data files like machines.csv and disinfection data.
- `tests/`: Unit tests.
- `app.py`: Main Flask application.
- `run_new_app.py`: Script to run the new app.
- `requirements.txt`: Python dependencies.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python run_new_app.py
   ```

## API Endpoints

- Authentication: /login, /logout
- Machines: /api/machines, /api/add_machine, etc.
- Detection: /api/init_camera, /api/capture_image, etc.
- Reports: /api/generate_report, etc.

For full API documentation, see the main project docs.
