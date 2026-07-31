"""工作台永久在线服务：Flask + localtunnel"""
from flask import Flask, send_from_directory, jsonify
from pathlib import Path
import subprocess, threading, time

BASE = Path(__file__).parent
app = Flask(__name__)  # 不用static_folder，手动路由

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/manifest.json")
def manifest():
    return send_from_directory(BASE, "manifest.json")

@app.route("/sw.js")
def sw():
    return send_from_directory(BASE, "sw.js")

@app.route("/data/<path:f>")
def data(f):
    return send_from_directory(BASE / "data", f)

@app.route("/api/refresh")
def refresh():
    subprocess.run(["/usr/bin/python3", str(BASE/"data-server/fetch_data.py"), "--once"], capture_output=True, timeout=30)
    return jsonify({"status":"ok"})

def scheduler():
    while True:
        subprocess.run(["/usr/bin/python3", str(BASE/"data-server/fetch_data.py"), "--once"], capture_output=True, timeout=30)
        time.sleep(7200)

threading.Thread(target=scheduler, daemon=True).start()
app.run(host="0.0.0.0", port=5000, debug=False)
