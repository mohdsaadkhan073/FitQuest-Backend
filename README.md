# FitQuest Backend

The backend layer manages application services, API routes, workout progress tracking, scoring, hardware communication (Arduino UNO / Servo reward box), and the exercise recognition model.

## Subdirectories

- `src/`: Modular backend application logic (`controllers`, `routes`, `services`, `models`, `config`, `utils`).
- `model/`: Computer Vision Exercise Recognition Model using MediaPipe Pose & OpenCV.
- `tests/`: Automated unit and integration tests.

## Running the Exercise Recognition Model

From the `FitQuest/` project root directory:

```bash
python backend/model/main.py
```
