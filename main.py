from flask import Flask, request, redirect, url_for, session, render_template_string
import os

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"

# Хранилища в памяти
users = {}        # {username: {"banned": False, "ip": "1.2.3.4"}}
comments = []     # [{"user": "ник", "text": "коммент"}]
banned_ips = set()

@app.before_request
def check_ban():
    ip = request.remote_addr
    user = session.get("user")
    if ip in banned_ips and not session.get("is_admin"):
        return redirect(url_for("banned"))
    if user and users.get(user, {}).get("banned") and not session.get("is_admin"):
        return redirect(url_for("banned"))

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>TikTok 2.0</title>
      <style>
        body { margin:0; background:#121212; color:#e0e0e0; font-family:Arial; overflow:hidden; }
        video { width:100vw; height:100vh; object-fit:cover; }
        .comments-btn { position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
          background:#1f1f1f; color:#fff; padding:12px 24px; border-radius:30px; border:none;
          cursor:pointer; transition:background 0.3s ease; }
        .comments-btn:hover { background:#333; }
        .comments-panel { position:fixed; bottom:-60%; left:0; width:100%; height:60%;
          background:#1c1c1c; border-top-left-radius:20px; border-top-right-radius:20px;
          box-shadow:0 -4px 20px rgba(0,0,0,0.5); transition:bottom 0.5s ease;
          padding:20px; overflow-y:auto; }
        .comments-panel.active { bottom:0; }
        .comment { padding:10px; margin:5px 0; background:#2a2a2a; border-radius:10px; }
      </style>
    </head>
    <body>
      <video autoplay loop muted>
        <source src="https://www.w3schools.com/html/mov_bbb.mp4" type="video/mp4">
      </video>
      <button class="comments-btn" onclick="toggleComments()">Комментарии</button>
      <div id="commentsPanel" class="comments-panel">
        <h2>Комментарии</h2>
        {% if not session.get("user") %}
          <form method="POST" action="/register">
            <input type="text" name="username" placeholder="Ваш ник" required>
            <button type="submit">Зарегистрироваться</button>
          </form>
        {% else %}
          <form method="POST" action="/add_comment">
            <textarea name="text" required style="width:100%;height:60px;"></textarea>
            <button type="submit">Отправить</button>
          </form>
        {% endif %}
        <div>
          {% for c in comments %}
            <div class="comment">{{ c.user }}: {{ c.text }}</div>
          {% endfor %}
        </div>
      </div>
      <script>
        function toggleComments() {
          document.getElementById("commentsPanel").classList.toggle("active");
        }
      </script>
    </body>
    </html>
    """
    return render_template_string(html, comments=comments)

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    if username not in users:
        users[username] = {"banned": False, "ip": request.remote_addr}
    session["user"] = username
    return redirect(url_for("index"))

@app.route("/add_comment", methods=["POST"])
def add_comment():
    user = session.get("user")
    if not user or users[user]["banned"]:
        return redirect(url_for("banned"))
    text = request.form["text"]
    comments.append({"user": user, "text": text})
    return redirect(url_for("index"))

@app.route("/banned")
def banned():
    return "<h1>Ваш аккаунт или IP заблокирован. Обратитесь к администратору.</h1>"
ADMIN_PASSWORD = "9448868"

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method=="POST" and request.form["password"]==ADMIN_PASSWORD:
        session["is_admin"]=True
        return redirect(url_for("admin_console"))
    return '<form method="POST"><input type="password" name="password"><button>Войти</button></form>'

@app.route("/admin/console")
def admin_console():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    html = """
    <h1>Админ-консоль</h1>
    <h2>Пользователи</h2>
    <ul>
      {% for u, data in users.items() %}
        <li>{{ u }} (IP: {{ data.ip }}) {% if data.banned %}[Забанен]{% endif %}
          <a href="/admin/ban_user/{{ u }}">Бан</a>
          <a href="/admin/unban_user/{{ u }}">Разбан</a>
        </li>
      {% endfor %}
    </ul>
    <h2>Заблокированные IP</h2>
    <ul>
      {% for ip in banned_ips %}
        <li>{{ ip }} <a href="/admin/unban_ip/{{ ip }}">Разбанить</a></li>
      {% endfor %}
    </ul>
    <form method="POST" action="/admin/ban_ip">
      <input type="text" name="ip" placeholder="IP для бана">
      <button type="submit">Забанить IP</button>
    </form>
    <h2>Комментарии</h2>
    <ul>
      {% for i, c in enumerate(comments) %}
        <li>{{ c.user }}: {{ c.text }} <a href="/admin/delete/{{ i }}">Удалить</a></li>
      {% endfor %}
    </ul>
    """
    return render_template_string(html, users=users, banned_ips=banned_ips, comments=comments)

@app.route("/admin/ban_user/<user>")
def ban_user(user):
    if session.get("is_admin") and user in users:
        users[user]["banned"]=True
    return redirect(url_for("admin_console"))

@app.route("/admin/unban_user/<user>")
def unban_user(user):
    if session.get("is_admin") and user in users:
        users[user]["banned"]=False
    return redirect(url_for("admin_console"))

@app.route("/admin/ban_ip", methods=["POST"])
def ban_ip():
    if session.get("is_admin"):
        ip = request.form["ip"]
        banned_ips.add(ip)
    return redirect(url_for("admin_console"))

@app.route("/admin/unban_ip/<ip>")
def unban_ip(ip):
    if session.get("is_admin"):
        banned_ips.discard(ip)
    return redirect(url_for("admin_console"))

@app.route("/admin/delete/<int:index>")
def delete_comment(index):
    if session.get("is_admin") and 0 <= index < len(comments):
        comments.pop(index)
    return redirect(url_for("admin_console"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render задаёт PORT автоматически
    app.run(host="0.0.0.0", port=port)

