# 食光 AI · 每日饮食推荐系统
# 阶段2：注册登录，区分普通用户与管理员

import json
import os
from datetime import datetime
from functools import wraps
from uuid import uuid4

from flask import (
    Flask, flash, redirect, render_template_string,
    request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

app = Flask(__name__)
app.secret_key = "shiguang-ai-demo-secret"


# ---------- 文件初始化 ----------
def init_files():
    for path in (USERS_FILE, HISTORY_FILE):
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)


def load_data(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_data(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_user(username):
    for user in load_data(USERS_FILE):
        if user["username"].lower() == username.lower():
            return user
    return None


def seed_demo_users():
    """首次运行时写入两个演示账号"""
    users = load_data(USERS_FILE)
    if users:
        return
    demo = [
        ("demo", "demo123", "user", "体验用户"),
        ("admin", "admin123", "admin", "平台管理员"),
    ]
    for username, password, role, name in demo:
        users.append({
            "id": str(uuid4()),
            "username": username,
            "password": generate_password_hash(password),
            "role": role,
            "name": name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    save_data(USERS_FILE, users)


# ---------- 登录校验装饰器 ----------
def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("请先登录后再访问", "error")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("当前账号没有访问该页面的权限", "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapper
    return decorator


# ---------- 页面模板 ----------
BASE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} · 食光 AI</title>
<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
       background: radial-gradient(900px 480px at 85% 0%, #e4f0dd, transparent 62%), #f3f0e8;
       color: #1d2619; }
a { color: inherit; }
.nav { display: flex; justify-content: space-between; align-items: center;
       padding: 16px 32px; background: rgba(255,253,248,.86);
       border-bottom: 1px solid #e7e0d1; }
.brand { font-family: "Songti SC", serif; font-size: 20px; font-weight: 700;
         color: #184434; text-decoration: none; letter-spacing: .04em; }
.nav-right { display: flex; align-items: center; gap: 16px; font-size: 12px; color: #79806e; }
.nav-right a { color: #184434; text-decoration: none; }
.container { max-width: 980px; margin: 0 auto; padding: 36px 24px 64px; }
.flash { padding: 10px 14px; border-radius: 10px; margin-bottom: 14px; font-size: 13px; }
.flash.success { background: #e9f2e8; color: #21694b; }
.flash.error { background: #f9eaea; color: #a44040; }
.auth-card { max-width: 430px; margin: 5vh auto 0; background: #fffdf8;
             border: 1px solid #e7e0d1; border-radius: 20px; padding: 32px;
             box-shadow: 0 24px 60px -40px rgba(32,44,27,.45); }
.auth-card h1 { font-family: "Songti SC", serif; margin: 0 0 4px; font-size: 25px; }
.muted { color: #79806e; font-size: 13px; margin: 0 0 20px; }
.form { display: flex; flex-direction: column; gap: 13px; }
.form label { display: flex; flex-direction: column; gap: 6px;
              font-size: 12px; font-weight: 600; color: #3c4636; }
.form input, .form select, .form textarea {
  padding: 11px 12px; border: 1px solid #d9d1bf; border-radius: 10px;
  font-size: 14px; background: #fffefb; font-family: inherit; }
.form input:focus, .form select:focus, .form textarea:focus {
  outline: none; border-color: #2f7f5b; box-shadow: 0 0 0 3px rgba(47,127,91,.12); }
.form-label { display: block; font-size: 12px; font-weight: 600;
              color: #3c4636; margin-bottom: 7px; }
.role-select { display: flex; gap: 10px; }
.role-select label { flex: 1; flex-direction: row; align-items: center; gap: 7px;
                     padding: 11px 12px; border: 1px solid #d9d1bf; border-radius: 10px;
                     background: #fffefb; cursor: pointer; font-weight: 500; }
.role-select input { width: auto; margin: 0; }
.btn { border: 0; background: #184434; color: #f4f8ee; padding: 12px 16px;
       border-radius: 11px; font-size: 14px; font-weight: 600; cursor: pointer; }
.btn:hover { background: #123a2b; }
.switch { text-align: center; font-size: 12px; color: #79806e; margin: 18px 0 0; }
.switch a { color: #1f6b4a; font-weight: 600; }
.demo { margin-top: 16px; padding-top: 14px; border-top: 1px dashed #e7e0d1;
        font-size: 11px; color: #a7ac9c; text-align: center; line-height: 1.8; }
.panel { background: #fffdf8; border: 1px solid #e7e0d1; border-radius: 20px;
         padding: 30px; box-shadow: 0 24px 60px -42px rgba(32,44,27,.38); }
.panel h1 { font-family: "Songti SC", serif; font-size: 27px; margin: 10px 0 8px; }
.panel h2 { font-family: "Songti SC", serif; font-size: 18px; margin: 26px 0 10px; }
.panel p { color: #6f7768; font-size: 13px; line-height: 1.8; }
.tag { display: inline-block; padding: 4px 10px; border-radius: 999px;
       background: #e9f2e8; color: #21694b; font-size: 11px; font-weight: 600; }
.tag.admin { background: #fbf0da; color: #94601c; }
.placeholder { margin-top: 22px; padding: 40px; border: 1px dashed #d9d1bf;
               border-radius: 16px; text-align: center; color: #a7ac9c;
               font-size: 13px; background: #faf7ef; }
.stats { display: flex; gap: 14px; margin: 22px 0; }
.stats > div { flex: 1; background: #faf7ef; border: 1px solid #e7e0d1;
               border-radius: 14px; padding: 16px; }
.stats strong { display: block; font-family: "Songti SC", serif; font-size: 24px; }
.stats span { font-size: 11px; color: #79806e; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; color: #a7ac9c; font-size: 10px; letter-spacing: .06em;
     padding: 8px; border-bottom: 1px solid #e7e0d1; font-weight: 600; }
td { padding: 10px 8px; border-bottom: 1px solid #f1ecdf; color: #3c4636; }
</style>
</head>
<body>
<header class="nav">
  <a class="brand" href="{{ url_for('dashboard') if session.get('user_id') else url_for('login') }}">食光 AI</a>
  <div class="nav-right">
    {% if session.get('user_id') %}
      <span>{{ session.get('name') }} · {{ '管理员' if session.get('role') == 'admin' else '普通用户' }}</span>
      <a href="{{ url_for('logout') }}">退出登录</a>
    {% endif %}
  </div>
</header>
<main class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, message in messages %}
      <div class="flash {{ category }}">{{ message }}</div>
    {% endfor %}
  {% endwith %}
  {{ content|safe }}
</main>
</body>
</html>
"""

LOGIN_PAGE = """
<section class="auth-card">
  <h1>登录食光 AI</h1>
  <p class="muted">登录后继续你的每日饮食计划</p>
  <form method="post" class="form">
    <label>用户名<input name="username" maxlength="16" required placeholder="请输入用户名"></label>
    <label>密码<input type="password" name="password" required placeholder="请输入密码"></label>
    <button class="btn" type="submit">登录</button>
  </form>
  <p class="switch">还没有账号？<a href="{{ url_for('register') }}">去注册</a></p>
  <p class="demo">演示账号：demo / demo123（普通用户）<br>admin / admin123（管理员）</p>
</section>
"""

REGISTER_PAGE = """
<section class="auth-card">
  <h1>创建账号</h1>
  <p class="muted">选择账号类型，开始使用食光 AI</p>
  <form method="post" class="form">
    <label>用户名<input name="username" maxlength="16" required placeholder="2-16 位中英文或数字"></label>
    <label>密码<input type="password" name="password" minlength="6" required placeholder="至少 6 位字符"></label>
    <label>确认密码<input type="password" name="confirm" minlength="6" required placeholder="再次输入密码"></label>
    <div>
      <span class="form-label">账号类型</span>
      <div class="role-select">
        <label><input type="radio" name="role" value="user" checked> 普通用户</label>
        <label><input type="radio" name="role" value="admin"> 管理员</label>
      </div>
    </div>
    <button class="btn" type="submit">注册</button>
  </form>
  <p class="switch">已有账号？<a href="{{ url_for('login') }}">去登录</a></p>
</section>
"""

USER_PAGE = """
<section class="panel">
  <span class="tag">普通用户</span>
  <h1>你好，{{ session.get('name') }}</h1>
  <p>账号已登录成功。下一阶段将在这里填写身高、体重、忌口与口味，生成一日三餐。</p>
  <div class="placeholder">AI 食谱推荐 · 即将上线</div>
</section>
"""

ADMIN_PAGE = """
<section class="panel">
  <span class="tag admin">管理员</span>
  <h1>管理后台</h1>
  <p>当前登录账号为管理员，可查看平台用户与后续的推荐记录。</p>
  <div class="stats">
    <div><strong>{{ user_count }}</strong><span>注册用户</span></div>
    <div><strong>{{ record_count }}</strong><span>推荐记录</span></div>
  </div>
  <h2>全部账号</h2>
  <table>
    <thead>
      <tr><th>用户名</th><th>昵称</th><th>角色</th><th>注册时间</th></tr>
    </thead>
    <tbody>
      {% for user in users %}
      <tr>
        <td>{{ user.username }}</td>
        <td>{{ user.name }}</td>
        <td>{{ '管理员' if user.role == 'admin' else '普通用户' }}</td>
        <td>{{ user.created_at }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</section>
"""


def page(title, content):
    return render_template_string(BASE, title=title, content=content)


# ---------- 路由 ----------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        role = request.form.get("role", "user")
        if role not in ("user", "admin"):
            role = "user"

        if not 2 <= len(username) <= 16:
            flash("用户名需为 2-16 位字符", "error")
            return redirect(url_for("register"))
        if find_user(username):
            flash("该用户名已被注册，请换一个", "error")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("密码至少需要 6 位", "error")
            return redirect(url_for("register"))
        if password != confirm:
            flash("两次输入的密码不一致", "error")
            return redirect(url_for("register"))

        users = load_data(USERS_FILE)
        users.append({
            "id": str(uuid4()),
            "username": username,
            "password": generate_password_hash(password),
            "role": role,
            "name": username,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        save_data(USERS_FILE, users)
        flash("注册成功，请登录", "success")
        return redirect(url_for("login"))

    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return page("注册", render_template_string(REGISTER_PAGE))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = find_user(username)
        if not user or not check_password_hash(user["password"], password):
            flash("用户名或密码错误", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["name"] = user.get("name") or user["username"]
        session["role"] = user["role"]
        flash("登录成功，欢迎回来", "success")
        return redirect(url_for("dashboard"))

    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return page("登录", render_template_string(LOGIN_PAGE))


@app.route("/logout")
def logout():
    session.clear()
    flash("已退出登录", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required()
def dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin_home"))
    return redirect(url_for("user_home"))


@app.route("/user")
@login_required("user")
def user_home():
    return page("普通用户", render_template_string(USER_PAGE))


@app.route("/admin")
@login_required("admin")
def admin_home():
    users = load_data(USERS_FILE)
    records = load_data(HISTORY_FILE)
    content = render_template_string(
        ADMIN_PAGE, users=users, user_count=len(users), record_count=len(records)
    )
    return page("管理后台", content)


init_files()
seed_demo_users()

if __name__ == "__main__":
    app.run(debug=True)
