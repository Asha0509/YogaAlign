import os
import cv2
import numpy as np
import pickle
import joblib
import mediapipe as mp
from collections import Counter

# ========== Model Loading ==========

MODEL_DIR = os.path.dirname(__file__)

# Load SVM model for uploaded video
svm_model_path = os.path.join(MODEL_DIR, 'svm_asana_model.pkl')
svm_classifier = None
try:
    svm_classifier = joblib.load(svm_model_path)
    print(f"✅ SVM model loaded using joblib: {svm_model_path}")
except Exception as e:
    print(f"❌ Failed to load SVM model: {e}")

# Load Random Forest model for live frame
rf_model_path = os.path.join(MODEL_DIR, 'random_forest_model.joblib')
rf_classifier = None
try:
    rf_classifier = joblib.load(rf_model_path)
    print(f"✅ Random Forest model loaded: {rf_model_path}")
except Exception as e:
    print(f"❌ Failed to load Random Forest model: {e}")

# ========== Mediapipe Setup ==========

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.3, min_tracking_confidence=0.3)

# ========== Feedback ==========

FEEDBACK = {
    "tadasana": "Feet together, spine straight, chin up.",
    "trikonasana": "Stretch sideways, don't lean forward.",
    "vrikshasana": "Balance more evenly on standing leg.",
    "padmasana": "Knees down, spine upright.",
    "bhujangasana": "Keep elbows close, lift from chest.",
    "shavasana": "Relax fully, no muscle tension."
}

# ========== Utilities ==========

def extract_landmarks(results, mode="live"):
    if not results.pose_landmarks:
        return None
    if mode == "live":
        return np.array([[lm.x, lm.y, lm.visibility] for lm in results.pose_landmarks.landmark]).flatten()
    else:  # for SVM model trained on 2D only
        return np.array([[lm.x, lm.y] for lm in results.pose_landmarks.landmark]).flatten()

def display_summary(label, confidence, verdict, feedback_msg):
    print("\n✅ Final Results:")
    print(f"🎯 Predicted Asana: {label}")
    print(f"📊 Confidence: {confidence}%")
    print(f"{verdict}")
    print(f"💬 Feedback: {feedback_msg}")

def summary_failure(reason):
    print(f"❌ {reason}")
    return {"label": reason, "score": 0.0, "verdict": "", "feedback": ""}

# ========== SVM Pose Prediction (Uploaded Video) ==========

def predict_uploaded_pose(landmarks):
    if svm_classifier is None:
        return None
    return svm_classifier.predict([landmarks])[0]

def process_video(video_path):
    if svm_classifier is None:
        return summary_failure("SVM model not loaded")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return summary_failure("Invalid video path")

    predictions = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        print(f"📸 Processing frame {frame_count}")

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        landmarks = extract_landmarks(results, mode="video")

        if landmarks is not None:
            print(f"✅ Landmarks detected ({len(landmarks)} values)")
        else:
            print("❌ No landmarks detected")

        if landmarks is not None and len(landmarks) == 66:
            pred_class = predict_uploaded_pose(landmarks)
            predictions.append(pred_class)
            print(f"🎯 Frame {frame_count}: Predicted - {pred_class}")
        else:
            print(f"⚠️ Invalid landmarks in frame {frame_count}")

    cap.release()

    if not predictions:
        return summary_failure("No pose detected in video")

    counts = Counter(predictions)
    final_label, count = counts.most_common(1)[0]
    confidence = round(count / len(predictions) * 100, 2)
    verdict = "✅ Pose performed correctly!" if confidence >= 60 else "❌ Pose performed incorrectly!"
    feedback_msg = FEEDBACK.get(final_label.lower(), "👍 Good attempt!")

    display_summary(final_label, confidence, verdict, feedback_msg)
    return {
        "label": final_label,
        "score": confidence,
        "verdict": verdict,
        "feedback": feedback_msg
    }

# ========== RF Pose Prediction (Live Frame) ==========

def predict_live_pose(landmarks):
    if rf_classifier is None:
        return None, 0.0
    prediction = rf_classifier.predict([landmarks])[0]
    probas = rf_classifier.predict_proba([landmarks])[0]
    confidence = round(np.max(probas) * 100, 2)
    return prediction, confidence

def process_live_frame(frame):
    if rf_classifier is None:
        return summary_failure("Random Forest model not loaded")

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    landmarks = extract_landmarks(results, mode="live")

    print(f"🧪 Landmark length: {len(landmarks) if landmarks is not None else 'None'}")

    if landmarks is not None and len(landmarks) == 99:
        pred_class, confidence = predict_live_pose(landmarks)
        feedback_msg = FEEDBACK.get(str(pred_class).lower(), "👍 Good attempt!")
        verdict = "✅ Live pose detected!" if confidence >= 60 else "❌ Low confidence in prediction"
        display_summary(pred_class, confidence, verdict, feedback_msg)
        return {
            "label": pred_class,
            "score": confidence,
            "verdict": verdict,
            "feedback": feedback_msg
        }
    else:
        return summary_failure("No pose detected in frame")

# ========== CLI Debug Mode ==========

if __name__ == "__main__":
    print("🚀 Yoga Pose Detection CLI")
    mode = input("Choose mode (video/live): ").strip().lower()

    if mode == "video":
        video_path = input("📂 Enter video file path: ").strip()
        if not os.path.exists(video_path):
            print("❌ Video file does not exist.")
        else:
            result = process_video(video_path)
            print("\n🔚 Output:\n", result)

    elif mode == "live":
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open webcam.")
            exit()
        print("🎥 Starting live pose detection... Press 'q' to quit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame from webcam.")
                break
            result = process_live_frame(frame)
            cv2.imshow("Live Yoga Pose", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
    else:
        print("❌ Invalid mode. Use 'video' or 'live'.")
