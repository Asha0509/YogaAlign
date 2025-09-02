from db_connection import get_db_connection
import hashlib
import sqlite3

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fileName TEXT NOT NULL,
            url TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            pose_name TEXT NOT NULL,
            score REAL,
            confidence REAL,
            is_correct INTEGER,
            verdict TEXT,
            feedback TEXT,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );
    ''')

    conn.commit()
    conn.close()


def add_user(name, email, password):
    print("📥 Trying to insert user:", name, email)
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
            (name, email, hashed_password)
        )
        conn.commit()
        print("✅ User inserted.")

        # Debug: Show all users
        cursor.execute("SELECT * FROM users")
        for row in cursor.fetchall():
            print("📄 User in DB:", dict(row))

    except sqlite3.IntegrityError:
        raise ValueError("Email already registered.")
    finally:
        conn.close()


def validate_user(email, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users WHERE email=? AND password=?", (email, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user  # Returns tuple (id, name) or None


def save_video_info(filename, url, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videos (fileName, url, user_id)
        VALUES (?, ?, ?)
    ''', (filename, url, user_id))
    conn.commit()
    conn.close()


def get_all_videos(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT v.*, (
            SELECT p.id FROM predictions p
            WHERE p.video_id = v.id
            ORDER BY p.id DESC
            LIMIT 1
        ) AS prediction_id
        FROM videos v
        WHERE v.user_id = ?
    ''', (user_id,))

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    videos = [dict(zip(columns, row)) for row in rows]

    conn.close()
    return videos


def delete_video_by_id(video_id):
    """Delete video by ID. Returns True if deleted, False if not."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()
    return rows_deleted > 0


def save_prediction(video_id, pose_name, score, confidence, is_correct, verdict, feedback):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (video_id, pose_name, score, confidence, is_correct, verdict, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (video_id, pose_name, score, confidence, int(is_correct), verdict, feedback))
    conn.commit()
    conn.close()


def get_prediction_by_id(prediction_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, v.url as video_url, v.fileName
        FROM predictions p
        JOIN videos v ON p.video_id = v.id
        WHERE p.id = ?
    ''', (prediction_id,))
    row = cursor.fetchone()

    if row:
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        if data.get('feedback'):
            # Adjust split method depending on how it's stored
            if '\n' in data['feedback']:
                data['feedback'] = data['feedback'].split('\n')
            elif ',' in data['feedback']:
                data['feedback'] = [item.strip() for item in data['feedback'].split(',')]
            else:
                data['feedback'] = [data['feedback']]
        conn.close()
        return data

    conn.close()
    return None


def get_prediction_by_video_id(video_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM predictions WHERE video_id = ?', (video_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None


def delete_prediction_by_id(prediction_id):
    """Delete prediction by ID. Returns True if deleted, False otherwise."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM predictions WHERE id = ?', (prediction_id,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()
    return rows_deleted > 0

def get_video_by_id(video_id):
    """Retrieve video by ID from the videos table. Returns a dictionary if found, None otherwise."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_prediction(video_id, pose_name, score, confidence, is_correct, verdict, feedback):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE predictions
        SET pose_name = ?, score = ?, confidence = ?, is_correct = ?, verdict = ?, feedback = ?
        WHERE video_id = ?
    ''', (pose_name, score, confidence, is_correct, verdict, feedback, video_id))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0

