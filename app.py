# 食光 AI · 每日饮食推荐系统
# 阶段3：接入 AI，完成饮食推荐核心功能

import json
import os
import random
import sys
import threading
import webbrowser
from datetime import datetime
from functools import wraps
from uuid import uuid4

from flask import (
    Flask, flash, redirect, render_template_string,
    request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash


def app_dir():
    """打包成 exe 后，数据文件放在 exe 同级目录"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = app_dir()
USERS_FILE = os.path.join(BASE_DIR, "users.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

app = Flask(__name__)
app.secret_key = "shiguang-ai-demo-secret"

RESTRICTIONS = ["香菜", "辣椒", "海鲜", "牛肉", "猪肉", "鸡蛋", "牛奶", "花生", "素食"]
FLAVORS = ["清淡", "家常", "香辣", "酸甜", "鲜香"]
MEALS = ["早餐", "午餐", "晚餐"]
MEAL_RATIOS = {"早餐": 0.3, "午餐": 0.4, "晚餐": 0.3}


# =========================================================
# 食谱库（AI 推荐候选）
# =========================================================
RECIPES = [
    # 早餐
    {"name": "香菇鸡肉粥", "meal": "早餐", "kcal": 330, "protein": 22, "flavor": "清淡",
     "tags": [], "ingredients": "大米、鸡胸肉、香菇、姜丝"},
    {"name": "小米南瓜粥", "meal": "早餐", "kcal": 260, "protein": 7, "flavor": "清淡",
     "tags": ["素食"], "ingredients": "小米、南瓜、枸杞"},
    {"name": "番茄鸡蛋面", "meal": "早餐", "kcal": 420, "protein": 18, "flavor": "家常",
     "tags": ["鸡蛋"], "ingredients": "挂面、番茄、鸡蛋、小青菜"},
    {"name": "燕麦香蕉酸奶杯", "meal": "早餐", "kcal": 300, "protein": 11, "flavor": "清淡",
     "tags": ["牛奶", "素食"], "ingredients": "燕麦、酸奶、香蕉、蓝莓"},
    {"name": "鲜虾小馄饨", "meal": "早餐", "kcal": 390, "protein": 24, "flavor": "鲜香",
     "tags": ["海鲜", "香菜", "猪肉"], "ingredients": "馄饨皮、鲜虾、猪肉馅、紫菜、香菜"},
    {"name": "日式梅子饭团", "meal": "早餐", "kcal": 360, "protein": 10, "flavor": "鲜香",
     "tags": ["素食"], "ingredients": "米饭、腌梅子、海苔、白芝麻"},
    {"name": "蔬菜鸡蛋饼", "meal": "早餐", "kcal": 340, "protein": 16, "flavor": "家常",
     "tags": ["鸡蛋"], "ingredients": "鸡蛋、面粉、胡萝卜丝、西葫芦丝"},
    {"name": "豆浆油条", "meal": "早餐", "kcal": 450, "protein": 12, "flavor": "家常",
     "tags": ["素食"], "ingredients": "黄豆、油条、榨菜"},
    {"name": "牛油果全麦吐司", "meal": "早餐", "kcal": 380, "protein": 14, "flavor": "清淡",
     "tags": ["素食"], "ingredients": "全麦吐司、牛油果、黑胡椒、柠檬汁"},
    {"name": "香蕉花生酱吐司", "meal": "早餐", "kcal": 400, "protein": 13, "flavor": "清淡",
     "tags": ["花生", "素食"], "ingredients": "全麦吐司、花生酱、香蕉"},

    # 午餐
    {"name": "香煎鸡胸藜麦碗", "meal": "午餐", "kcal": 520, "protein": 42, "flavor": "清淡",
     "tags": [], "ingredients": "鸡胸肉、藜麦、西兰花、圣女果"},
    {"name": "番茄牛腩饭", "meal": "午餐", "kcal": 650, "protein": 35, "flavor": "家常",
     "tags": ["牛肉"], "ingredients": "牛腩、番茄、土豆、洋葱、米饭"},
    {"name": "鱼香肉丝盖饭", "meal": "午餐", "kcal": 620, "protein": 24, "flavor": "香辣",
     "tags": ["猪肉", "辣椒"], "ingredients": "猪里脊、木耳、胡萝卜、泡椒、米饭"},
    {"name": "日式照烧鸡腿饭", "meal": "午餐", "kcal": 640, "protein": 32, "flavor": "鲜香",
     "tags": [], "ingredients": "去骨鸡腿、米饭、西兰花、照烧汁"},
    {"name": "清蒸鲈鱼配糙米", "meal": "午餐", "kcal": 480, "protein": 38, "flavor": "清淡",
     "tags": ["海鲜", "香菜"], "ingredients": "鲈鱼、糙米、姜丝、葱段、香菜"},
    {"name": "麻婆豆腐盖饭", "meal": "午餐", "kcal": 560, "protein": 22, "flavor": "香辣",
     "tags": ["辣椒", "猪肉"], "ingredients": "嫩豆腐、猪肉末、豆瓣酱、花椒、米饭"},
    {"name": "时蔬牛肉炒面", "meal": "午餐", "kcal": 610, "protein": 28, "flavor": "家常",
     "tags": ["牛肉"], "ingredients": "牛肉片、面条、洋葱、彩椒"},
    {"name": "韩式蔬菜拌饭", "meal": "午餐", "kcal": 580, "protein": 20, "flavor": "香辣",
     "tags": ["鸡蛋", "辣椒"], "ingredients": "米饭、菠菜、胡萝卜、豆芽、鸡蛋、辣酱"},
    {"name": "冬阴功海鲜汤面", "meal": "午餐", "kcal": 540, "protein": 30, "flavor": "酸甜",
     "tags": ["海鲜", "辣椒", "香菜"], "ingredients": "虾、鱿鱼、米粉、香茅、椰浆、香菜"},
    {"name": "香菇青菜豆腐煲", "meal": "午餐", "kcal": 420, "protein": 24, "flavor": "清淡",
     "tags": ["素食"], "ingredients": "北豆腐、香菇、小青菜、高汤"},
    {"name": "香煎三文鱼沙拉", "meal": "午餐", "kcal": 480, "protein": 34, "flavor": "清淡",
     "tags": ["海鲜"], "ingredients": "三文鱼、生菜、牛油果、小番茄"},
    {"name": "杂粮时蔬饭", "meal": "午餐", "kcal": 480, "protein": 16, "flavor": "清淡",
     "tags": ["素食"], "ingredients": "糙米、玉米、青豆、胡萝卜、香菇"},
    {"name": "凉拌豆腐藜麦碗", "meal": "午餐", "kcal": 430, "protein": 22, "flavor": "酸甜",
     "tags": ["素食"], "ingredients": "嫩豆腐、藜麦、黄瓜、番茄、香醋"},

    # 晚餐
    {"name": "白灼虾配时蔬", "meal": "晚餐", "kcal": 380, "protein": 32, "flavor": "清淡",
     "tags": ["海鲜"], "ingredients": "鲜虾、西兰花、芦笋、姜片"},
    {"name": "西兰花炒鸡胸", "meal": "晚餐", "kcal": 420, "protein": 38, "flavor": "清淡",
     "tags": [], "ingredients": "鸡胸肉、西兰花、蒜末、黑胡椒"},
    {"name": "清炒时蔬杂粮饭", "meal": "晚餐", "kcal": 390, "protein": 14, "flavor": "清淡",
     "tags": ["素食"], "ingredients": "杂粮饭、菠菜、口蘑、胡萝卜"},
    {"name": "红烧牛肉面", "meal": "晚餐", "kcal": 560, "protein": 30, "flavor": "家常",
     "tags": ["牛肉"], "ingredients": "牛腱肉、面条、青菜、八角、姜片"},
    {"name": "味噌豆腐烤鱼", "meal": "晚餐", "kcal": 460, "protein": 34, "flavor": "鲜香",
     "tags": ["海鲜"], "ingredients": "鳕鱼、嫩豆腐、味噌、海苔、秋葵"},
    {"name": "番茄豆腐煲", "meal": "晚餐", "kcal": 350, "protein": 20, "flavor": "酸甜",
     "tags": ["素食"], "ingredients": "番茄、嫩豆腐、金针菇、葱花"},
    {"name": "香辣鸡丝凉面", "meal": "晚餐", "kcal": 480, "protein": 26, "flavor": "香辣",
     "tags": ["辣椒", "花生"], "ingredients": "鸡胸肉、面条、黄瓜丝、花生碎、辣椒油"},
    {"name": "蔬菜咖喱饭", "meal": "晚餐", "kcal": 520, "protein": 16, "flavor": "香辣",
     "tags": ["辣椒", "素食"], "ingredients": "米饭、土豆、胡萝卜、洋葱、咖喱、椰浆"},
    {"name": "南瓜浓汤配全麦面包", "meal": "晚餐", "kcal": 410, "protein": 12, "flavor": "清淡",
     "tags": ["牛奶", "素食"], "ingredients": "南瓜、淡奶油、洋葱、全麦面包"},
    {"name": "蒜蓉粉丝蒸虾", "meal": "晚餐", "kcal": 360, "protein": 26, "flavor": "鲜香",
     "tags": ["海鲜"], "ingredients": "鲜虾、粉丝、蒜蓉、葱花"},
    {"name": "鸡胸肉蔬菜卷", "meal": "晚餐", "kcal": 330, "protein": 30, "flavor": "清淡",
     "tags": [], "ingredients": "鸡胸肉、生菜、彩椒、胡萝卜、全麦饼皮"},
    {"name": "清蒸南瓜豆腐", "meal": "晚餐", "kcal": 360, "protein": 22, "flavor": "清淡",
     "tags": ["素食"], "ingredients": "南瓜、嫩豆腐、毛豆、枸杞"},
]


# =========================================================
# 文件读写
# =========================================================
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


# =========================================================
# AI 推荐引擎
# =========================================================
def calc_metrics(height, weight):
    bmi = weight / ((height / 100) ** 2)
    if bmi >= 24:
        target = weight * 25
    elif bmi < 18.5:
        target = weight * 35
    else:
        target = weight * 30
    target = int(max(1200, min(3000, round(target / 10) * 10)))

    if bmi < 18.5:
        label = "偏瘦"
    elif bmi < 24:
        label = "标准"
    elif bmi < 28:
        label = "偏胖"
    else:
        label = "肥胖"
    return round(bmi, 1), target, label


def filter_pool(meal, restrictions):
    pool = []
    for dish in RECIPES:
        if dish["meal"] != meal:
            continue
        if any(tag in restrictions for tag in dish["tags"]):
            continue
        if "素食" in restrictions and "素食" not in dish["tags"]:
            continue
        pool.append(dish)
    return pool


def pick_pair(pool, target_kcal, flavors, used_names):
    if not pool:
        return []
    if len(pool) == 1:
        return pool[:1]

    candidates = sorted(
        pool,
        key=lambda d: (2 if d["flavor"] in flavors else 0) + random.random(),
        reverse=True
    )[:12]

    best_pair = None
    best_score = -9999.0

    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            first, second = candidates[i], candidates[j]
            score = 0.0
            if first["flavor"] in flavors:
                score += 1.6
            if second["flavor"] in flavors:
                score += 1.6
            score -= abs(first["kcal"] + second["kcal"] - target_kcal) / 90.0
            if first["name"] in used_names:
                score -= 2.0
            if second["name"] in used_names:
                score -= 2.0
            score += random.random() * 1.2
            if score > best_score:
                best_score = score
                best_pair = [first, second]

    return best_pair or candidates[:2]


def generate_plan(height, weight, restrictions, flavors):
    bmi, target, label = calc_metrics(height, weight)
    used_names = set()
    meals = {}
    warnings = []

    for meal in MEALS:
        pool = filter_pool(meal, restrictions)
        if len(pool) < 2:
            warnings.append(f"{meal}符合条件的菜品不足，已放宽部分限制，请自行确认忌口。")
            pool = [dish for dish in RECIPES if dish["meal"] == meal]

        meal_target = int(target * MEAL_RATIOS[meal])
        picked = pick_pair(pool, meal_target, flavors, used_names)
        for dish in picked:
            used_names.add(dish["name"])
        meals[meal] = picked

    total_kcal = sum(d["kcal"] for dishes in meals.values() for d in dishes)
    total_protein = sum(d["protein"] for dishes in meals.values() for d in dishes)

    restriction_text = "、".join(restrictions) if restrictions else "无"
    flavor_text = "、".join(flavors) if flavors else "不限"
    advice = (
        f"你的 BMI 为 {bmi}（{label}），每日目标热量约 {target} kcal。"
        f"已避开：{restriction_text}；口味优先：{flavor_text}。"
        "三餐按 3:4:3 分配，全天建议饮水 1500-1700 ml。"
    )

    return {
        "bmi": bmi,
        "bmi_label": label,
        "target": target,
        "meals": meals,
        "totals": {"kcal": total_kcal, "protein": total_protein},
        "advice": advice,
        "warnings": warnings,
    }


# =========================================================
# 页面模板
# =========================================================
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
.container { max-width: 1040px; margin: 0 auto; padding: 34px 24px 64px; }
.flash { padding: 10px 14px; border-radius: 10px; margin-bottom: 14px; font-size: 13px; }
.flash.success { background: #e9f2e8; color: #21694b; }
.flash.error { background: #f9eaea; color: #a44040; }
.auth-card { max-width: 430px; margin: 5vh auto 0; background: #fffdf8;
             border: 1px solid #e7e0d1; border-radius: 20px; padding: 32px;
             box-shadow: 0 24px 60px -40px rgba(32,44,27,.45); }
.auth-card h1 { font-family: "Songti SC", serif; margin: 0 0 4px; font-size: 25px; }
.muted { color: #79806e; font-size: 13px; margin: 0 0 20px; }
.form { display: flex; flex-direction: column; gap: 14px; }
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
       border-radius: 11px; font-size: 14px; font-weight: 600; cursor: pointer;
       text-decoration: none; display: inline-block; text-align: center; }
.btn:hover { background: #123a2b; }
.btn.ghost { background: #fffdf8; color: #184434; border: 1px solid #d9d1bf; }
.btn.small { padding: 8px 12px; font-size: 12px; }
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
.stats { display: flex; gap: 14px; margin: 22px 0; flex-wrap: wrap; }
.stats > div { flex: 1; min-width: 120px; background: #faf7ef; border: 1px solid #e7e0d1;
               border-radius: 14px; padding: 16px; }
.stats strong { display: block; font-family: "Songti SC", serif; font-size: 24px; }
.stats span { font-size: 11px; color: #79806e; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; color: #a7ac9c; font-size: 10px; letter-spacing: .06em;
     padding: 8px; border-bottom: 1px solid #e7e0d1; font-weight: 600; }
td { padding: 10px 8px; border-bottom: 1px solid #f1ecdf; color: #3c4636; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 13px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chips .chip { flex-direction: row; align-items: center; gap: 0;
               font-weight: 500; cursor: pointer; }
.chip input { position: absolute; opacity: 0; pointer-events: none; }
.chip span { display: inline-block; padding: 7px 13px; border: 1px solid #d9d1bf;
             border-radius: 999px; background: #fffefb; font-size: 12px;
             color: #3c4636; transition: .15s; }
.chip input:checked + span { background: #184434; border-color: #184434; color: #f4f8ee; }
.result-hero { background: linear-gradient(135deg, #fffdf8, #f0f7ec);
               border: 1px solid #e7e0d1; border-radius: 20px;
               padding: 26px; margin-bottom: 18px; }
.result-hero h1 { font-family: "Songti SC", serif; font-size: 24px; margin: 10px 0 6px; }
.metrics { display: flex; gap: 26px; margin-top: 18px; flex-wrap: wrap; }
.metrics strong { display: block; font-family: "Songti SC", serif; font-size: 22px; }
.metrics span { font-size: 10px; color: #79806e; }
.advice { background: #faf7ef; border-radius: 12px; padding: 12px 14px;
          color: #3c4636 !important; margin: 16px 0 0; font-size: 12px; }
.notice { background: #fbf0da; border: 1px solid #eed9b3; color: #8c621f;
          padding: 10px 14px; border-radius: 10px; font-size: 12px; margin-bottom: 14px; }
.meal-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.meal-card { background: #fffdf8; border: 1px solid #e7e0d1;
             border-radius: 16px; padding: 18px; }
.meal-head { display: flex; justify-content: space-between; align-items: center;
             border-bottom: 1px dashed #e7e0d1; padding-bottom: 9px; margin-bottom: 6px; }
.meal-head h2 { margin: 0; font-size: 16px; }
.meal-head span { font-size: 11px; color: #79806e; }
.dish { display: flex; justify-content: space-between; gap: 10px;
        padding: 9px 0; border-bottom: 1px solid #f5f1e7; }
.dish:last-child { border-bottom: 0; }
.dish strong { display: block; font-size: 12.5px; }
.dish small { font-size: 10px; color: #a7ac9c; }
.dish > span { font-family: "Songti SC", serif; font-size: 13px;
               font-weight: 700; white-space: nowrap; }
.actions { display: flex; gap: 10px; margin-top: 18px; align-items: center; }
.record { border: 1px solid #e7e0d1; border-radius: 12px;
          background: #fffefb; margin-bottom: 10px; overflow: hidden; }
.record summary { cursor: pointer; padding: 12px 14px; display: flex;
                  gap: 12px; align-items: center; font-size: 12px; list-style: none; }
.record summary::-webkit-details-marker { display: none; }
.record summary strong { font-size: 12.5px; }
.record summary span { color: #79806e; }
.record summary em { margin-left: auto; font-style: normal; color: #21694b; font-weight: 600; }
.record-body { padding: 10px 14px 14px; font-size: 11.5px;
               color: #6f7768; border-top: 1px dashed #f1ecdf; line-height: 1.8; }
.meal-line { margin-top: 4px; }
.empty { padding: 40px; text-align: center; color: #a7ac9c;
         border: 1px dashed #d9d1bf; border-radius: 14px;
         font-size: 13px; background: #faf7ef; }
.disclaimer { text-align: center; font-size: 10px; color: #a7ac9c; margin-top: 14px; }
@media (max-width: 760px) {
  .meal-grid { grid-template-columns: 1fr; }
  .grid2 { grid-template-columns: 1fr; }
  .nav { padding: 14px 18px; }
  .nav-right { gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
  .container { padding: 22px 16px 48px; }
}
</style>
</head>
<body>
<header class="nav">
  <a class="brand" href="{{ url_for('dashboard') if session.get('user_id') else url_for('login') }}">食光 AI</a>
  <div class="nav-right">
    {% if session.get('user_id') %}
      {% if session.get('role') == 'user' %}
        <a href="{{ url_for('user_home') }}">今日推荐</a>
        <a href="{{ url_for('history') }}">历史记录</a>
      {% else %}
        <a href="{{ url_for('admin_home') }}">管理后台</a>
        <a href="{{ url_for('admin_records') }}">推荐记录</a>
      {% endif %}
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
  <h1>生成你的今日食谱</h1>
  <p>填写身高、体重、忌口与口味，AI 会按 3:4:3 的热量比例搭配一日三餐。</p>
  <form method="post" action="{{ url_for('recommend') }}" class="form"
        style="margin-top:22px; max-width:760px;">
    <div class="grid2">
      <label>身高（cm）
        <input type="number" name="height" min="120" max="220" step="1" required placeholder="170">
      </label>
      <label>体重（kg）
        <input type="number" name="weight" min="30" max="200" step="0.1" required placeholder="62">
      </label>
    </div>
    <div>
      <span class="form-label">忌口 / 不吃的食材（可多选）</span>
      <div class="chips">
        {% for item in restrictions %}
        <label class="chip">
          <input type="checkbox" name="restrictions" value="{{ item }}">
          <span>{{ item }}</span>
        </label>
        {% endfor %}
      </div>
    </div>
    <div>
      <span class="form-label">想吃的口味（可多选）</span>
      <div class="chips">
        {% for item in flavors %}
        <label class="chip">
          <input type="checkbox" name="flavors" value="{{ item }}">
          <span>{{ item }}</span>
        </label>
        {% endfor %}
      </div>
    </div>
    <button class="btn" type="submit">AI 生成今日食谱</button>
    <p class="muted" style="margin:0;">推荐结果仅供参考，特殊饮食需求请咨询营养师。</p>
  </form>
  {% if count %}
  <p style="margin-top:18px;">
    你已生成 {{ count }} 份食谱，
    <a href="{{ url_for('history') }}" style="color:#1f6b4a;font-weight:600;">查看历史记录</a>
  </p>
  {% endif %}
</section>
"""

RESULT_PAGE = """
{% if warnings %}
<div class="notice">
  {% for w in warnings %}<div>{{ w }}</div>{% endfor %}
</div>
{% endif %}

<section class="result-hero">
  <span class="tag">AI 今日食谱</span>
  <h1>你的三餐搭配已完成</h1>
  <div class="metrics">
    <div><strong>{{ record.bmi }}</strong><span>BMI · {{ record.bmi_label }}</span></div>
    <div><strong>{{ record.target }}</strong><span>目标热量 kcal</span></div>
    <div><strong>{{ record.totals.kcal }}</strong><span>本方案热量</span></div>
    <div><strong>{{ record.totals.protein }}g</strong><span>蛋白质</span></div>
  </div>
  <p class="advice">{{ record.advice }}</p>
</section>

<div class="meal-grid">
  {% for meal, dishes in record.meals.items() %}
  <article class="meal-card">
    <div class="meal-head">
      <h2>{{ meal }}</h2>
      <span>{{ dishes | sum(attribute='kcal') }} kcal</span>
    </div>
    {% for dish in dishes %}
    <div class="dish">
      <div>
        <strong>{{ dish.name }}</strong>
        <small>{{ dish.ingredients }}</small>
      </div>
      <span>{{ dish.kcal }}<small> kcal</small></span>
    </div>
    {% endfor %}
  </article>
  {% endfor %}
</div>

<div class="actions">
  <a class="btn ghost" href="{{ url_for('user_home') }}">重新生成</a>
  <a class="btn" href="{{ url_for('history') }}">查看历史记录</a>
</div>
<p class="disclaimer">营养建议仅作日常参考，特殊疾病或过敏人群请咨询专业营养师。</p>
"""

HISTORY_PAGE = """
<section class="panel">
  <h1>我的历史食谱</h1>
  <p>共生成 {{ records | length }} 份方案，按时间倒序展示。</p>

  {% if records %}
    <div style="margin-top:20px;">
      {% for r in records %}
      <details class="record">
        <summary>
          <strong>{{ r.created_at }}</strong>
          <span>{{ r.target }} kcal 目标 · BMI {{ r.bmi }}</span>
          <em>{{ r.totals.kcal }} kcal</em>
        </summary>
        <div class="record-body">
          <div>身高 {{ r.height }} cm · 体重 {{ r.weight }} kg ·
            忌口：{{ r.restrictions | join('、') or '无' }} ·
            口味：{{ r.flavors | join('、') or '不限' }}
          </div>
          {% for meal, dishes in r.meals.items() %}
          <div class="meal-line">
            <strong>{{ meal }}：</strong>
            {{ dishes | map(attribute='name') | join('、') }}
          </div>
          {% endfor %}
        </div>
      </details>
      {% endfor %}
    </div>
  {% else %}
    <div class="empty" style="margin-top:20px;">
      还没有历史记录，去生成第一份食谱吧。
    </div>
    <div class="actions">
      <a class="btn" href="{{ url_for('user_home') }}">去生成今日食谱</a>
    </div>
  {% endif %}
</section>
"""

ADMIN_PAGE = """
<section class="panel">
  <span class="tag admin">管理员</span>
  <h1>管理后台</h1>
  <p>查看平台用户与所有用户的推荐记录。</p>
  <div class="stats">
    <div><strong>{{ user_count }}</strong><span>注册用户</span></div>
    <div><strong>{{ record_count }}</strong><span>推荐记录</span></div>
    <div><strong>{{ today_count }}</strong><span>今日推荐</span></div>
  </div>
  <a class="btn small" href="{{ url_for('admin_records') }}">查看全部推荐记录</a>

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

ADMIN_RECORDS_PAGE = """
<section class="panel">
  <span class="tag admin">管理员</span>
  <h1>全部推荐记录</h1>
  <p>共 {{ records | length }} 条记录，可按用户查看每日三餐。</p>

  {% if records %}
    <div style="margin-top:20px;">
      {% for r in records %}
      <details class="record">
        <summary>
          <strong>{{ r.name }}</strong>
          <span>@{{ r.username }} · {{ r.created_at }}</span>
          <em>{{ r.totals.kcal }} kcal</em>
        </summary>
        <div class="record-body">
          <div>身高 {{ r.height }} cm · 体重 {{ r.weight }} kg ·
            目标 {{ r.target }} kcal · BMI {{ r.bmi }}（{{ r.bmi_label }}）
          </div>
          <div>忌口：{{ r.restrictions | join('、') or '无' }} ·
            口味：{{ r.flavors | join('、') or '不限' }}
          </div>
          {% for meal, dishes in r.meals.items() %}
          <div class="meal-line">
            <strong>{{ meal }}：</strong>
            {{ dishes | map(attribute='name') | join('、') }}
          </div>
          {% endfor %}
        </div>
      </details>
      {% endfor %}
    </div>
  {% else %}
    <div class="empty" style="margin-top:20px;">暂无用户推荐记录</div>
  {% endif %}
</section>
"""


def page(title, content):
    return render_template_string(BASE, title=title, content=content)


# =========================================================
# 路由
# =========================================================
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
    records = [
        r for r in load_data(HISTORY_FILE)
        if r.get("user_id") == session.get("user_id")
    ]
    content = render_template_string(
        USER_PAGE,
        restrictions=RESTRICTIONS,
        flavors=FLAVORS,
        count=len(records)
    )
    return page("今日推荐", content)


@app.route("/recommend", methods=["POST"])
@login_required("user")
def recommend():
    try:
        height = float(request.form.get("height", ""))
        weight = float(request.form.get("weight", ""))
    except ValueError:
        flash("请填写有效的身高和体重", "error")
        return redirect(url_for("user_home"))

    if not 120 <= height <= 220:
        flash("身高需在 120-220 cm 之间", "error")
        return redirect(url_for("user_home"))
    if not 30 <= weight <= 200:
        flash("体重需在 30-200 kg 之间", "error")
        return redirect(url_for("user_home"))

    height = int(height) if height.is_integer() else round(height, 1)
    weight = int(weight) if weight.is_integer() else round(weight, 1)

    restrictions = request.form.getlist("restrictions")
    flavors = request.form.getlist("flavors")

    plan = generate_plan(height, weight, restrictions, flavors)

    record = {
        "id": str(uuid4()),
        "user_id": session["user_id"],
        "username": session["username"],
        "name": session.get("name") or session["username"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "height": height,
        "weight": weight,
        "bmi": plan["bmi"],
        "bmi_label": plan["bmi_label"],
        "target": plan["target"],
        "restrictions": restrictions,
        "flavors": flavors,
        "meals": plan["meals"],
        "totals": plan["totals"],
        "advice": plan["advice"],
        "warnings": plan["warnings"],
    }

    history = load_data(HISTORY_FILE)
    history.append(record)
    save_data(HISTORY_FILE, history)

    content = render_template_string(
        RESULT_PAGE, record=record, warnings=plan["warnings"]
    )
    return page("推荐结果", content)


@app.route("/history")
@login_required("user")
def history():
    records = [
        r for r in load_data(HISTORY_FILE)
        if r.get("user_id") == session.get("user_id")
    ]
    records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return page("历史记录", render_template_string(HISTORY_PAGE, records=records))


@app.route("/admin")
@login_required("admin")
def admin_home():
    users = load_data(USERS_FILE)
    records = load_data(HISTORY_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = sum(1 for r in records if r.get("created_at", "").startswith(today))
    content = render_template_string(
        ADMIN_PAGE,
        users=users,
        user_count=len(users),
        record_count=len(records),
        today_count=today_count,
    )
    return page("管理后台", content)


@app.route("/admin/records")
@login_required("admin")
def admin_records():
    records = load_data(HISTORY_FILE)
    records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return page("推荐记录", render_template_string(ADMIN_RECORDS_PAGE, records=records))


init_files()
seed_demo_users()

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        threading.Timer(
            1.2, lambda: webbrowser.open("http://127.0.0.1:5000")
        ).start()
        app.run(host="127.0.0.1", port=5000, debug=False)
    else:
        app.run(debug=True)
