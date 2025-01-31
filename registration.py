from flask import render_template, redirect, request
from db_init import get_db_conn
from werkzeug.security import generate_password_hash


def Registration():
    if request.method == "POST":
        username = request.form["nickname"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_pass = generate_password_hash(password)
        profile_pic = "img/profile_photo/default_profile.jpg"

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()
        
        if existing_user:
            return "Пользователь с таким логином или email уже существует"
        else:
            cur.execute("INSERT INTO users (username, email, password_hash, profile_picture) VALUES (%s, %s, %s, %s)", 
                        (username, email, hashed_pass, profile_pic))
            conn.commit()

            cur.close()
            conn.close()

            return redirect("/login")
    return render_template("registration.html")