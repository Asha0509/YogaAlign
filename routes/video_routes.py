from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from services.yoga_model import process_video  # Your updated prediction function
from db_services import save_video_info, get_all_videos, delete_video_by_id
import os
from collections import Counter
import base64
import uuid
from werkzeug.utils import secure_filename

video_bp = Blueprint('video', __name__)

def get_feedback_for_pose(pose):
    feedback_map = {
        "Tadasana": ["Bring your feet together", "Keep your spine straight"],
        "Bhujangasana": ["Lift your chest higher", "Place hands under shoulders"],
        "Trikonasana": ["Raise your left arm", "Lower your right hand towards your foot"],
        "Padmasana": ["Keep your back straight"],
        "Vrikshasana": ["Balance on one leg", "Keep hands together"],
        "Shavasana": [],
        "No pose detected": [],
    }
    return feedback_map.get(pose, [])

@video_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login.signin'))

    user_id = session.get('user_id')
    videos = get_all_videos(user_id)
    total_videos = len(videos)

    return render_template('dashboard.html', user=session['user'], total_videos=total_videos, videos=videos)



@video_bp.route('/upload', methods=['GET', 'POST'])
def upload_video():
    if 'user_id' not in session:
        return redirect(url_for('login.signin'))

    upload_folder = current_app.config['UPLOAD_FOLDER']
    user_id = session['user_id']

    if request.method == 'POST':
        # ✅ 1. Handle recorded camera video (base64)
        base64_video = request.form.get('camera-video-data')
        if base64_video and base64_video.startswith('data:video/webm;base64,'):
            try:
                video_data = base64.b64decode(base64_video.split(',')[1])
                filename = f"camera_{uuid.uuid4().hex}.webm"
                filepath = os.path.join(upload_folder, filename)

                with open(filepath, 'wb') as f:
                    f.write(video_data)

                relative_url = os.path.join('static', 'videos', filename).replace("\\", "/")
                save_video_info(filename, relative_url, user_id)
                flash('Camera video uploaded successfully!')
                return redirect(url_for('video.uploaded_videos'))
            except Exception as e:
                print("Camera video upload error:", e)
                flash('Failed to upload camera video.')
                return redirect(url_for('video.upload_video'))

        # ✅ 2. Handle file upload from input[type=file]
        file = request.files.get('file')
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            relative_url = os.path.join('static', 'videos', filename).replace("\\", "/")
            save_video_info(filename, relative_url, user_id)
            flash('Video uploaded successfully!')
            return redirect(url_for('video.uploaded_videos'))

        flash('No file or video provided.')
        return redirect(request.url)

    # GET request
    videos = get_all_videos(user_id)
    return render_template('dashboard.html', user=session.get('user'), videos=videos)


from flask import send_from_directory

@video_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)



@video_bp.route('/uploaded-videos')
def uploaded_videos():
    if 'user' not in session or 'user_id' not in session:
        return redirect(url_for('login.signin'))

    user_id = session['user_id']
    user_email = session['user']  # Get email from session

    videos = get_all_videos(user_id)

    # Count analyzed videos (with prediction_id present)
    analyzed_count = sum(1 for video in videos if video.get('prediction_id'))

    return render_template(
        'uploaded_videos.html',
        videos=videos,
        uploads=videos,  # Optional alias
        analyzed_count=analyzed_count,
        username=user_email.split('@')[0]  # Use email safely
    )




from db_services import delete_video_by_id, get_prediction_by_video_id, delete_prediction_by_id

@video_bp.route('/delete/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    if 'user' not in session or 'user_id' not in session:
        return redirect(url_for('login.signin'))

    user_id = session['user_id']
    videos = get_all_videos(user_id)
    video_to_delete = next((v for v in videos if v['id'] == video_id), None)

    if video_to_delete:
        # 1. Delete the physical video file
        file_path = os.path.join(current_app.root_path, video_to_delete['url'])
        if os.path.exists(file_path):
            os.remove(file_path)

        # 2. Delete the prediction associated with this video (if any)
        prediction = get_prediction_by_video_id(video_id)
        if prediction:
            delete_prediction_by_id(prediction['id'])

        # 3. Delete video record from DB
        delete_video_by_id(video_id)

        flash('Video and associated prediction deleted successfully!')
    else:
        flash('Video not found.')

    return redirect(url_for('video.uploaded_videos'))





from collections import Counter
from db_services import update_prediction

from db_services import save_prediction  # ✅ import the function

@video_bp.route('/analyze/<int:video_id>', methods=['POST'])
def analyze_video(video_id):
    if 'user' not in session or 'user_id' not in session:
        return redirect(url_for('login.signin'))

    user_id = session['user_id']
    videos = get_all_videos(user_id)
    video = next((v for v in videos if v['id'] == video_id), None)

    if not video:
        flash('Video not found.')
        return redirect(url_for('video.uploaded_videos'))

    file_path = os.path.join(current_app.root_path, video['url'])
    if not os.path.exists(file_path):
        flash('Video file is missing.')
        return redirect(url_for('video.uploaded_videos'))

    result = process_video(file_path)
    correct = result["score"] >= 60
    video_filename = os.path.basename(video['url'])

    feedback_list = get_feedback_for_pose(result["label"]) or [result["feedback"]]
    feedback_string = ', '.join(feedback_list)

    existing_prediction = get_prediction_by_video_id(video_id)

    if existing_prediction:
        update_prediction(
            video_id=video_id,
            pose_name=result["label"],
            score=result["score"],
            confidence=result["score"],
            is_correct=correct,
            verdict="✅ Pose performed correctly!" if correct else "❌ Pose performed incorrectly!",
            feedback=feedback_string
        )
    else:
        save_prediction(
            video_id=video_id,
            pose_name=result["label"],
            score=result["score"],
            confidence=result["score"],
            is_correct=correct,
            verdict="✅ Pose performed correctly!" if correct else "❌ Pose performed incorrectly!",
            feedback=feedback_string
        )

    # ✅ Now always define analysis here
    analysis = {
        "pose_name": result["label"],
        "score": result["score"],
        "confidence": result["score"],
        "is_correct": correct,
        "verdict": "✅ Pose performed correctly!" if correct else "❌ Pose performed incorrectly!",
        "feedback": feedback_list,
        "video_url": video_filename,
        "media_type": 'video'
    }

    return render_template(
        'prediction_result.html',
        video=video,
        video_url=video_filename,
        analysis=analysis,
        media_type='video'
    )

# ... (all your existing imports and routes remain unchanged)

from db_services import save_prediction, get_prediction_by_id, get_video_by_id # ✅ make sure you have this function

@video_bp.route('/view_result/<int:prediction_id>')
def view_result(prediction_id):
    if 'user' not in session:
        return redirect(url_for('login.signin'))

    prediction = get_prediction_by_id(prediction_id)
    user_id = session['user_id']
    user_email = session['user']  # Email from session

    videos = get_all_videos(user_id)

    if not prediction:
        flash('Prediction not found.')
        return redirect(url_for('video.uploaded_videos'))

    feedback_list = prediction.get('feedback', [])

    # ✅ Get video_id from prediction
    video_id = prediction["video_id"]

    # ✅ Get the video by video_id (you must have this function implemented)
    video = get_video_by_id(video_id)

    # If video not found, use fallback
    if not video:
        flash("Video not found for the prediction.")
        return redirect(url_for('video.uploaded_videos'))

    analysis = {
        "pose_name": prediction["pose_name"],
        "score": prediction["score"],
        "confidence": prediction["confidence"],
        "is_correct": bool(prediction["is_correct"]),
        "verdict": prediction["verdict"],
        "feedback": feedback_list,
        "video_url": video["fileName"],  # ✅ Use filename from fetched video
        "media_type": 'video'
    }

    # ✅ Construct video dict properly
    video_data = {
        "id": video["id"],
        "fileName": video["fileName"],
        "url": os.path.join("static", "videos", video["fileName"]),
    }

    return render_template(
        'results_db.html',
        videos=videos,
        uploads=videos,
        prediction=analysis,
        video=video_data
    )
