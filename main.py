from flask import Flask, request, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = "toniks-secret"

ADMIN_CODE = "toniks123"

# Всё хранится в памяти
users = {}        # {ip: {"role": "user"/"admin", "banned": False}}
comments = []     # [{"ip": "...", "text": "..."}]

@app.before_request
def check_ban():
    ip = request.remote_addr
    user = users.get(ip)
    if user and user.get("banned") and not session.get("is_admin"):
        return redirect(url_for("banned"))

@app.route("/", methods=["GET", "POST"])
def home():
    ip = request.remote_addr
    user = users.get(ip)

    if request.method == "POST":
        # Продолжить с IP
        if "continue_ip" in request.form:
            if ip not in users:
                users[ip] = {"role": "user", "banned": False}
            session["ip"] = ip
            return redirect(url_for("home"))

        # Вход как админ
        if "admin_code" in request.form:
            code = request.form["admin_code"]
            if code == ADMIN_CODE:
                users[ip] = {"role": "admin", "banned": False}
                session["ip"] = ip
                session["is_admin"] = True
                return redirect(url_for("admin"))
            else:
                return "⛔ Неверный код администратора", 403

        # Добавление комментария
        if "comment" in request.form and user and not user["banned"]:
            text = request.form["comment"].strip()
            if len(text) < 3:
                return "⛔ Комментарий слишком короткий", 400
            comments.append({"ip": ip, "text": text})
            return redirect(url_for("home"))

    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>TikTok 2.0</title>
      <style>
        body { margin:0; background:#121212; color:#e0e0e0; font-family:Arial; }
        video { width:100vw; height:60vh; object-fit:cover; }
        .panel { padding:20px; }
        input, button { padding:10px; margin:5px; border-radius:8px; border:none; }
        button { background:#1f1f1f; color:#fff; cursor:pointer; }
        button:hover { background:#333; }
        .comment { padding:10px; margin:5px 0; background:#2a2a2a; border-radius:10px; }
      </style>
    </head>
    <body>
      <video autoplay loop muted>
        <source src="https://www.w3schools.com/html/mov_bbb.mp4" type="video/mp4">
      </video>
      <div class="panel">
        <h2>Добро пожаловать</h2>
        {% if not session.get("ip") %}
          <form method="POST">
            <button name="continue_ip">Продолжить с моим IP</button>
          </form>
          <form method="POST">
            <input type="password" name="admin_code" placeholder="Код администратора">
            <button type="submit">Войти как админ</button>
          </form>
        {% else %}
          <form method="POST">
            <input type="text" name="comment" placeholder="Ваш комментарий">
            <button type="submit">Отправить</button>
          </form>
        {% endif %}
        <h3>Комментарии</h3>
        <div>
          {% for c in comments %}
            <div class="comment">{{ c.ip }}: {{ c.text }}</div>
          {% endfor %}
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(html, comments=comments)

@app.route("/banned")
def banned():
    return "<h1>Ваш IP заблокирован</h1>"

# ---------------- Админ-панель ----------------
@app.route("/admin")
def admin():
    ip = session.get("ip")
    if not ip or users.get(ip, {}).get("role") != "admin":
        return redirect(url_for("home"))
    html = """
    <h1>Админ‑панель</h1>
    <h2>Пользователи</h2>
    <ul>
      {% for ip, data in users.items() %}
        <li>{{ ip }} ({{ data.role }}) {% if data.banned %}[Забанен]{% endif %}
          <a href="/ban/{{ ip }}">Бан</a>
          <a href="/unban/{{ ip }}">Разбан</a>
        </li>
      {% endfor %}
    </ul>
    <h2>Комментарии</h2>
    <ul>
      {% for i, c in enumerate(comments) %}
        <li>{{ c.ip }}: {{ c.text }} <a href="/delete/{{ i }}">Удалить</a></li>
      {% endfor %}
    </ul>
    """
    return render_template_string(html, users=users, comments=comments)

@app.route("/ban/<ip>")
def ban(ip):
    if session.get("ip") and users.get(session["ip"], {}).get("role") == "admin":
        if ip in users:
            users[ip]["banned"] = True
    return redirect(url_for("admin"))

@app.route("/unban/<ip>")
def unban(ip):
    if session.get("ip") and users.get(session["ip"], {}).get("role") == "admin":
        if ip in users:
            users[ip]["banned"] = False
    return redirect(url_for("admin"))

@app.route("/delete/<int:index>")
def delete_comment(index):
    if session.get("ip") and users.get(session["ip"], {}).get("role") == "admin":
        if 0 <= index < len(comments):
            comments.pop(index)
    return redirect(url_for("admin"))

# ---------------- Запуск ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
