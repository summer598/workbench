"""
WorkBuddy 工作台 · 永久在线服务
启动Flask静态服务 + ngrok公网隧道 + 定时数据抓取
"""
import os
import sys
import threading
import time
import subprocess
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
from pyngrok import ngrok

BASE_DIR = Path(__file__).parent
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/data/<path:filename>")
def serve_data(filename):
    return send_from_directory(BASE_DIR / "data", filename)

@app.route("/api/refresh")
def refresh():
    """手动触发数据抓取"""
    try:
        subprocess.run([sys.executable, str(BASE_DIR / "data-server" / "fetch_data.py"), "--once"], 
                      capture_output=True, timeout=30)
        return jsonify({"status": "ok", "message": "数据已刷新"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def start_data_scheduler():
    """后台定时抓取数据（每2小时）"""
    def run():
        while True:
            try:
                subprocess.run([sys.executable, str(BASE_DIR / "data-server" / "fetch_data.py"), "--once"],
                              capture_output=True, timeout=30)
                print(f"[{time.strftime('%H:%M:%S')}] 数据已刷新")
            except Exception as e:
                print(f"数据抓取异常: {e}")
            time.sleep(7200)
    t = threading.Thread(target=run, daemon=True)
    t.start()

if __name__ == "__main__":
    # 启动定时抓取
    start_data_scheduler()
    
    # 先抓一次数据
    print("初始化数据...")
    subprocess.run([sys.executable, str(BASE_DIR / "data-server" / "fetch_data.py"), "--once"],
                  capture_output=True, timeout=30)
    
    # 启动Flask
    port = 5000
    print(f"\n启动本地服务 http://localhost:{port}")
    
    # 启动ngrok隧道
    try:
        public_url = ngrok.connect(port, "http")
        print(f"\n{'='*50}")
        print(f"🚀 工作台已上线！")
        print(f"📱 手机访问链接: {public_url}")
        print(f"{'='*50}")
        print(f"\n把这个链接在手机浏览器打开，")
        print(f"然后「添加到主屏幕」即可当APP使用。")
        print(f"\n链接永久有效（只要本服务运行中）。")
    except Exception as e:
        print(f"ngrok启动失败: {e}")
        print("请访问 https://dashboard.ngrok.com 获取authtoken")
        print("然后运行: ngrok authtoken YOUR_TOKEN")
    
    app.run(host="0.0.0.0", port=port, debug=False)
