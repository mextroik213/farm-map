# -*- coding: utf-8 -*-
"""
Локальный сервер-помощник для карты фермы.
Принимает POST на /update — запускает update_site.ps1.
"""

import http.server
import socketserver
import subprocess
import json
import os
import time
import threading

PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
UPDATE_SCRIPT = os.path.join(ROOT, "update_site.ps1")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # CORS — чтобы сайт с file:// мог стучаться
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path == "/ping":
            self._json(200, {"ok": True, "status": "ready"})
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/update":
            self._json(*self._run_update())
            return
        self.send_error(404)

    def _run_update(self):
        if not os.path.exists(UPDATE_SCRIPT):
            return 500, {"ok": False, "error": "update_site.ps1 не найден"}

        t0 = time.time()
        try:
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass",
                 "-File", UPDATE_SCRIPT],
                capture_output=True, text=True, timeout=300,
                cwd=ROOT
            )
        except subprocess.TimeoutExpired:
            return 500, {"ok": False, "error": "Таймаут: скрипт работает дольше 5 минут"}
        except Exception as e:
            return 500, {"ok": False, "error": str(e)}

        elapsed = round(time.time() - t0, 2)
        log = (result.stdout or "") + "\n" + (result.stderr or "")
        log = log.strip()

        if result.returncode != 0:
            return 500, {"ok": False, "error": f"Скрипт завершился с кодом {result.returncode}", "log": log, "elapsed": elapsed}

        return 200, {"ok": True, "log": log, "elapsed": elapsed}

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args, **kwargs):
        # Не засоряем консоль
        pass


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    print("=" * 60)
    print("  Сервер обновления карты фермы")
    print("=" * 60)
    print(f"  Слушает: http://localhost:{PORT}")
    print(f"  Скрипт:  {UPDATE_SCRIPT}")
    print("")
    print("  Не закрывайте это окно, пока работаете с картой.")
    print("  Ctrl+C — остановить сервер.")
    print("=" * 60)
    print("")

    with ReusableTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nОстановлено.")


if __name__ == "__main__":
    main()