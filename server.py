# -*- coding: utf-8 -*-
"""Отладочный сервер — печатает каждый шаг."""
import http.server, socketserver, subprocess, json, os, sys, time

PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
UPDATE_SCRIPT = os.path.join(ROOT, "update_site.ps1")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        log("OPTIONS (preflight)")
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path == "/ping":
            log("GET /ping")
            self._json(200, {"ok": True, "status": "ready"})
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/update":
            log("POST /update — старт")
            code, obj = self._run_update()
            log(f"POST /update — отвечаю {code}")
            self._json(code, obj)
            return
        self.send_error(404)

    def _run_update(self):
        if not os.path.exists(UPDATE_SCRIPT):
            log("update_site.ps1 не найден!")
            return 500, {"ok": False, "error": "update_site.ps1 не найден"}

        t0 = time.time()
        log("Запускаю PowerShell...")

        ps_cmd = (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "$OutputEncoding = [System.Text.Encoding]::UTF8; "
            f"& '{UPDATE_SCRIPT}'"
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", ps_cmd],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=600,
                cwd=ROOT,
                env=os.environ.copy()
            )
            log(f"PowerShell завершился, returncode={result.returncode}")
        except subprocess.TimeoutExpired:
            log("ТАЙМАУТ — 10 минут без ответа")
            return 500, {"ok": False, "error": "Таймаут: 10 минут без ответа"}
        except Exception as e:
            log(f"Исключение: {e}")
            return 500, {"ok": False, "error": str(e)}

        elapsed = round(time.time() - t0, 2)

        def dec(b):
            if not b: return ""
            for enc in ("utf-8", "cp866", "cp1251"):
                try: return b.decode(enc)
                except UnicodeDecodeError: continue
            return b.decode("utf-8", errors="replace")

        output = (dec(result.stdout) + "\n" + dec(result.stderr)).strip()
        log("--- вывод скрипта ---")
        for line in output.splitlines()[-30:]:
            log(line)
        log("--- конец вывода ---")

        if result.returncode != 0:
            return 500, {"ok": False,
                         "error": f"Скрипт завершился с кодом {result.returncode}",
                         "log": output, "elapsed": elapsed}

        return 200, {"ok": True, "log": output, "elapsed": elapsed}

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        log(f"{self.command} {self.path}")


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    log("=" * 60)
    log("Отладочный сервер карты фермы")
    log(f"Python:  {sys.executable}")
    log(f"ROOT:    {ROOT}")
    log(f"Script:  {UPDATE_SCRIPT}")
    log(f"Exists:  {os.path.exists(UPDATE_SCRIPT)}")
    log(f"PORT:    {PORT}")
    log("=" * 60)
    with ReusableTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            log("Остановлено")


if __name__ == "__main__":
    main()