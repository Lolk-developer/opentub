from flask import render_template, redirect, request
from db_init import get_db_conn
from flask_login import login_user, current_user
from werkzeug.security import check_password_hash
from model_user import User

def Login():
    if current_user.is_authenticated:
        return redirect("/")
    
    if request.method == "POST":
        login = request.form["login"]
        password = request.form["password"]

        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s", (login,))
        user_data = cur.fetchone()

        cur.close()
        conn.close()

        if user_data and check_password_hash(user_data[3], password):
            user = User(*user_data)
            login_user(user)
            return redirect("/")
        else:
            return "Неверный логин или пароль"

    return render_template("login.html")