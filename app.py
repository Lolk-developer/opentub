import os
from flask import Flask, render_template, redirect, request, flash, url_for
import psycopg2
from model_user import User
from secret_key import SECRET_KEY
from db_init import get_db_conn
from flask_login import LoginManager, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/videos"
PREVIEW_FOLDER = "static/img/preview"
ALLOWED_EXTENSIONS = {"mp4"}
PREVIEW_EXTENSIONS = {"jpg", "jpeg", "png"}

app.config["SECRET_KEY"] = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PREVIEW_FOLDER"] = PREVIEW_FOLDER

login_manager = LoginManager(app)
login_manager.login_view = "login" 

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if user_data:
        return User(*user_data)
    return None

@app.route("/")
def main():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM videos")
    videos = cur.fetchall()

    if videos:
        user_ids = [video[1] for video in videos] 
        cur.execute("SELECT user_id, username FROM users WHERE user_id IN %s", (tuple(user_ids),))
        channels = {row[0]: row[1] for row in cur.fetchall()}
    else:
        channels = {}

    cur.close()
    conn.close()
    return render_template("index.html", videos=videos, channels=channels)

@app.route("/music")
def music():
    return render_template("categories/music.html")

@app.route("/movies")
def movies():
    return render_template("categories/movies.html")

@app.route("/videogame")
def videogame():
    return render_template("categories/videogames.html")

@app.route("/news")
def news():
    return render_template("categories/news.html")

@app.route("/sport")
def sport():
    return render_template("categories/sport.html")

@app.route("/learn")
def learn():
    return render_template("categories/learn.html")

@app.route("/login", methods=["GET", "POST"])
def login_user():
    import login
    return login.Login()

@app.route("/registration", methods=["GET", "POST"])
def registration_user():
    import registration
    return registration.Registration()

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/video/<int:video_id>")
def show_video(video_id):
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("SELECT video_id, title, description, upload_date, video_url, views_count FROM videos WHERE video_id = %s", (video_id,))
    video_data = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM likes WHERE video_id = %s AND like_type = 1", (video_id,))
    likes_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM likes WHERE video_id = %s AND like_type = -1", (video_id,))
    dislikes_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return render_template("video.html", video_data=video_data, likes=likes_count, dislikes=dislikes_count)

@app.route('/video/<int:video_id>/like', methods=['POST'])
def like_video(video_id):
    user_id = current_user.id
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT like_type FROM likes WHERE user_id = %s AND video_id = %s", (user_id, video_id))
    existing_like = cur.fetchone()
    if existing_like:
        new_status = 1 if existing_like[0] != 1 else 0
        cur.execute("UPDATE likes SET like_type = %s WHERE user_id = %s AND video_id = %s", (new_status, user_id, video_id))
    else:
        cur.execute("INSERT INTO likes (user_id, video_id, like_type) VALUES (%s, %s, 1)", (user_id, video_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

@app.route('/video/<int:video_id>/dislike', methods=['POST'])
def dislike_video(video_id):
    user_id = current_user.id
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT like_type FROM likes WHERE user_id = %s AND video_id = %s", (user_id, video_id))
    existing_like = cur.fetchone()
    if existing_like:
        new_status = -1 if existing_like[0] != -1 else 0
        cur.execute("UPDATE likes SET like_type = %s WHERE user_id = %s AND video_id = %s", (new_status, user_id, video_id))
    else:
        cur.execute("INSERT INTO likes (user_id, video_id, like_type) VALUES (%s, %s, -1)", (user_id, video_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

@app.route("/channel")
@login_required
def account():
    return render_template("account.html")

@app.route("/myaccount")
@login_required
def my_account():
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM videos WHERE user_id=%s", (current_user.id,))
    video_count = cur.fetchone()

    cur.execute("SELECT video_id, user_id, title, thumbnail_url, views_count FROM videos WHERE user_id=%s", (current_user.id,))
    video_data = cur.fetchall()
    
    cur.close()
    conn.close()

    return render_template("myaccount.html", video_count=video_count, video_data=video_data)


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions

@app.route("/myaccount/upload", methods=["GET", "POST"])
@login_required
def upload_video():
    if request.method == "POST":
        if "video_upload" not in request.files or "preview" not in request.files:
            flash("Файл не выбран", "error")
            return redirect(request.url)

        video = request.files["video_upload"]
        preview = request.files["preview"]
        video_name = request.form["video-name"]
        description = request.form["description"]
        category = request.form["category"]

        if video.filename == "" or preview.filename == "":
            flash("Файл не выбран", "error")
            return redirect(request.url)

        if not allowed_file(video.filename, ALLOWED_EXTENSIONS):
            flash("Неподдерживаемый формат видео", "error")
            return redirect(request.url)

        if not allowed_file(preview.filename, PREVIEW_EXTENSIONS):
            flash("Неподдерживаемый формат изображения", "error")
            return redirect(request.url)

        video_filename = secure_filename(video.filename)
        preview_filename = secure_filename(preview.filename)

        video_path = os.path.abspath(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"], video_filename))
        preview_path = os.path.abspath(os.path.join(app.root_path, app.config["PREVIEW_FOLDER"], preview_filename))

        # Создаём папки, если их нет
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)

        video.save(video_path)
        preview.save(preview_path)

        # Сохраняем относительный путь для preview
        preview_rel_path = os.path.relpath(preview_path, app.root_path)

        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO videos (user_id, title, description, category, video_url, thumbnail_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (current_user.id, video_name, description, category, video_filename, preview_rel_path),
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Видео успешно загружено!", "success")
        return redirect("/myaccount")

    return render_template("upload-video.html")



@app.route("/www/admin")
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect('/')
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute('SELECT user_id, username, email FROM users')
    users = cur.fetchall()

    cur.execute('SELECT video_id, title, views_count, category FROM videos')
    videos = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("admin/admin.html", users=users, videos=videos)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect("/")
    
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/www/admin')

@app.route('/delete_video/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    if current_user.role != 'admin':
        return redirect("/")

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT video_url, thumbnail_url FROM videos WHERE video_id = %s', (video_id,))
    filesname = cur.fetchone()

    video_path = f"static/video/{filesname[0]}"
    preview_path = filesname[1]

    if os.path.exists(video_path) and os.path.exists(preview_path):
        os.remove(video_path)
        os.remove(preview_path)
        cur.execute('DELETE FROM videos WHERE video_id = %s', (video_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/www/admin')
    else:
        return redirect('/www/admin')

    

if __name__ == '__main__':
    app.run(debug=True)
