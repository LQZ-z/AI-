# 食光 AI · 桌面窗口启动器
# 使用 pywebview 打开独立窗口，不经过浏览器

import socket
import threading
import time

import webview

from app import app, init_files, seed_demo_users


def free_port():
    """获取一个空闲端口，避免 5000 被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_server(port, timeout=10):
    """等待本地服务启动完成"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def main():
    init_files()
    seed_demo_users()

    port = free_port()
    threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1",
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True,
        ),
        daemon=True,
    ).start()

    wait_server(port)

    webview.create_window(
        "食光 AI · 每日饮食推荐系统",
        f"http://127.0.0.1:{port}",
        width=1180,
        height=820,
        min_size=(900, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
