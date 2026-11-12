# 食光 AI · 每日饮食推荐系统
# 阶段1：初始化项目，搭建页面框架

import json
import os

from flask import Flask, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

app = Flask(__name__)
app.secret_key = "shiguang-ai-demo-secret"


def init_files():
    """文件初始化判断：不存在则创建为空列表"""
    for path in (USERS_FILE, HISTORY_FILE):
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)


PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>食光 AI · 每日饮食推荐系统</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      background: radial-gradient(900px 500px at 80% 0%, #dfeeda, transparent 60%), #f3f0e8;
      color: #1d2619;
    }
    .nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 18px 34px;
      background: rgba(255, 253, 248, 0.8);
      border-bottom: 1px solid #e7e0d1;
    }
    .brand {
      font-family: "Songti SC", serif;
      font-size: 20px;
      font-weight: 700;
      color: #184434;
    }
    .nav span { font-size: 12px; color: #a7ac9c; letter-spacing: 0.12em; }
    .hero { max-width: 900px; margin: 14vh auto 0; padding: 0 32px; }
    .eyebrow {
      font-size: 11px;
      letter-spacing: 0.22em;
      color: #2f7f5b;
      font-weight: 700;
    }
    h1 {
      font-family: "Songti SC", serif;
      font-size: clamp(36px, 6vw, 62px);
      line-height: 1.35;
      margin: 18px 0 16px;
    }
    h1 em { font-style: normal; color: #21694b; }
    p { max-width: 470px; font-size: 14px; line-height: 1.9; color: #6f7768; }
  </style>
</head>
<body>
  <header class="nav">
    <div class="brand">食光 AI</div>
    <span>AI DAILY MEAL PLANNER</span>
  </header>
  <main class="hero">
    <p class="eyebrow">每日饮食推荐系统</p>
    <h1>今天吃什么，<br>交给 <em>AI</em> 来搭配。</h1>
    <p>根据身高、体重、忌口与口味偏好，生成营养均衡的一日三餐。</p>
  </main>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


init_files()

if __name__ == "__main__":
    app.run(debug=True)
