# 食光 AI · 每日饮食推荐系统

基于 Flask 的 AI 每日饮食推荐系统。普通用户填写身高、体重、忌口与口味后，
生成一日三餐食谱；管理员可查看所有用户的推荐记录。

## 功能

- 注册 / 登录，区分普通用户与管理员
- 普通用户：填写身高、体重、忌口、口味，生成一日三餐
- AI 推荐：BMI 计算、目标热量、忌口过滤、口味匹配、三餐 3:4:3 分配
- 历史记录：普通用户查看自己的历史食谱
- 管理后台：查看全部用户、推荐记录与今日推荐数
- 数据本地保存：users.json 保存账号，history.json 保存推荐记录

## 演示账号

- 普通用户：`demo / demo123`
- 管理员：`admin / admin123`

## 源码运行

```bash
pip install -r requirements.txt
python app.py
```

浏览器打开 http://127.0.0.1:5000

## 打包 exe

双击 `build.bat`，或在命令行执行：

```bash
pip install -r requirements.txt
pyinstaller --noconfirm --onedir --windowed --name ShiGuangAI --collect-all webview --hidden-import=webview.platforms.edgechromium desktop.py
```

生成结果在 `dist/ShiGuangAI/`。双击 `ShiGuangAI.exe` 会直接弹出独立软件窗口，
不打开浏览器、没有地址栏。`users.json` 与 `history.json` 保存在 exe 同级目录。

## 项目结构

```
app.py            Flask 主程序（页面、路由、AI 推荐引擎）
desktop.py        桌面窗口启动器（pywebview）
users.json        账号数据
history.json      推荐记录
requirements.txt  依赖
build.bat         Windows 打包脚本
```

## 提交记录

1. 初始化项目，搭建页面框架
2. 新增注册登录，区分两类账号
3. 接入AI，完成饮食推荐核心功能

> 推荐结果仅作日常参考，特殊疾病或过敏人群请咨询专业营养师。
