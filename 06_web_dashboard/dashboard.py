from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import os
from pathlib import Path

PORT = 8080

# 프로젝트 루트로 이동
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

print(f"Dashboard running at http://127.0.0.1:{PORT}/06_web_dashboard/")
webbrowser.open(f"http://127.0.0.1:{PORT}/06_web_dashboard/")

HTTPServer(("127.0.0.1", PORT), SimpleHTTPRequestHandler).serve_forever()
