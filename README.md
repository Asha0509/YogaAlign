# YogaAlign

YogaAlign is a Flask-based computer vision application that evaluates yoga poses from uploaded videos and live camera frames, then returns pose labels, scores, and corrective feedback.

## Features

- User authentication (`signup`, `login`, `logout`)
- Video upload and per-user video history
- Pose analysis pipeline with saved predictions
- Live camera frame inference endpoint
- Dashboard view for uploads, analysis status, and results

## Architecture

The project is organized into four layers:

1. Application Layer
- `app.py` initializes Flask, configures upload paths, registers blueprints, and exposes global routes.

2. Routing Layer
- `routes/signup_route.py`, `routes/login_route.py`, `routes/logout_route.py`: auth flows
- `routes/video_routes.py`: upload, analyze, result retrieval, and delete flows

3. Service Layer
- `services/yoga_model.py`: model inference helpers for video and live-frame prediction
- `db_services.py`: CRUD operations for users, videos, and predictions
- `db_connection.py`: SQLite connection helper

4. Presentation Layer
- `templates/`: Jinja pages for auth, dashboard, uploads, and results
- `static/css`, `static/js`, `static/images`, `static/videos`: frontend assets and uploaded/sample media

## Request Workflows

### Upload and Analyze

1. Authenticated user uploads a file or recorded camera video.
2. Video metadata is stored in SQLite.
3. User triggers analysis for a video.
4. `process_video()` runs inference and computes score/feedback.
5. Prediction is inserted/updated in DB and rendered in result templates.

### Live Camera Inference

1. Frontend sends base64-encoded frame to `/predict_live_frame`.
2. Server decodes the frame and passes it to `process_live_frame()`.
3. JSON response returns feedback list for real-time guidance.

## Tech Stack

- Python 3.x
- Flask
- OpenCV
- scikit-learn
- TensorFlow / MediaPipe dependencies (listed in `requirements.txt`)
- SQLite

## Project Structure

```text
YogaAlign/
|-- app.py
|-- models.py
|-- db_connection.py
|-- db_services.py
|-- requirements.txt
|-- my_database.db
|-- routes/
|   |-- __init__.py
|   |-- signup_route.py
|   |-- login_route.py
|   |-- logout_route.py
|   `-- video_routes.py
|-- services/
|   |-- __init__.py
|   |-- yoga_model.py
|   |-- label_encoder.pkl
|   |-- random_forest_model.joblib
|   |-- svm_pose_classifier.pkl
|   `-- svm_asana_model.pkl
|-- templates/
|-- static/
|   |-- css/
|   |-- js/
|   |-- images/
|   `-- videos/
`-- README.md
```

## Setup

1. Clone the repository

```bash
git clone https://github.com/Asha0509/YogaAlign.git
cd YogaAlign
```

2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run the application

```bash
python app.py
```

The app starts at `http://127.0.0.1:5000`.

## Notes

- Uploaded videos are stored under `static/videos/`.
- Database tables are initialized automatically at app startup via `create_tables()`.
- The repository currently includes generated artifacts (`__pycache__`, media samples, and local DB snapshot) because they were part of the original tracked history.
