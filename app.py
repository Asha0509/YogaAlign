from flask import Flask, redirect, session, request, render_template, jsonify
from db_services import create_tables
from routes import signup_bp, login_bp, logout_bp, video_bp
import os
import base64
import numpy as np
import cv2

# Import the prediction function for live frame
from services.yoga_model import process_live_frame

app = Flask(__name__)
app.secret_key = 'hello123'

create_tables()

UPLOAD_FOLDER = os.path.join('static', 'videos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(signup_bp)
app.register_blueprint(login_bp)
app.register_blueprint(logout_bp)
app.register_blueprint(video_bp)

@app.route('/camera')
def camera_page():
    return render_template('camera_analysis.html')


@app.route('/')
def home():
    return render_template('home.html')

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/predict_live_frame', methods=['POST'])
def predict_live_frame_route():
    try:
        data = request.get_json()
        frame_data = data.get("frame", "")

        if "," in frame_data:
            frame_data = frame_data.split(",")[1]

        image_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        result = process_live_frame(frame)  # ✅ must return a list of strings
        return jsonify({ "feedback": result })  # ✅ wrap in a dict
    except Exception as e:
        print("❌ Error in /predict_live_frame:", str(e))
        return jsonify({"feedback": [f"Error: {str(e)}"]}), 500


if __name__ == '__main__':
    print("✅ Flask app starting on http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)
