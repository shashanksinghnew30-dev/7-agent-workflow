"""
Lightweight, Multi-Threaded HTTP & SSE Web Server for the 7-Agent AI Workflow.
Uses standard library http.server with Server-Sent Events (SSE) support.
Zero external dependencies required.
"""

from __future__ import annotations
import os
import json
import time
import queue
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Optional, Dict

from core.event_bus import EventBus
from core.orchestrator import WorkflowOrchestrator
from core.models import WorkflowState


STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))


class WorkflowHTTPHandler(BaseHTTPRequestHandler):
    # Class-level references set by launch_web_server
    event_bus: EventBus = None
    orchestrator: WorkflowOrchestrator = None
    active_states: Dict[str, WorkflowState] = {}
    base_output_dir: str = "output"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Root & Static Files
        if path in ["/", "/index.html"]:
            self._serve_file(os.path.join(STATIC_DIR, "index.html"), "text/html")
        elif path.startswith("/static/"):
            rel_file = path[len("/static/"):]
            full_path = os.path.join(STATIC_DIR, rel_file)
            mime = "text/plain"
            if full_path.endswith(".css"):
                mime = "text/css"
            elif full_path.endswith(".js"):
                mime = "application/javascript"
            elif full_path.endswith(".html"):
                mime = "text/html"
            self._serve_file(full_path, mime)

        # 2. Server-Sent Events (SSE) Stream
        elif path == "/api/stream":
            self._handle_sse_stream()

        # 3. Download Project ZIP
        elif path.startswith("/api/download/"):
            slug = path[len("/api/download/"):]
            self._handle_zip_download(slug)

        # 4. State API
        elif path.startswith("/api/state/"):
            sid = path[len("/api/state/"):]
            state = self.active_states.get(sid)
            if state:
                self._send_json(200, state.to_dict())
            else:
                self._send_json(404, {"error": "Session not found"})
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/run":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                data = json.loads(body) if body else {}
            except Exception:
                data = {}

            prompt = data.get("prompt", "Build a high-performance thread-safe LRU Cache with TTL")
            demo_loopback = bool(data.get("demo_loopback", False))

            # Run in worker thread so HTTP request returns immediately
            session_id = f"sess_{int(time.time()*1000)%1000000}"

            def worker():
                try:
                    orc = WorkflowOrchestrator(
                        event_bus=self.event_bus,
                        base_output_dir=self.base_output_dir,
                        demo_qa_loopback=demo_loopback
                    )
                    st = orc.execute(user_prompt=prompt, session_id=session_id)
                    self.active_states[session_id] = st
                except Exception as ex:
                    print(f"[WebRunner Error] {ex}")

            t = threading.Thread(target=worker, daemon=True)
            t.start()

            self._send_json(200, {"status": "started", "session_id": session_id})
        else:
            self.send_error(404, "Endpoint not found")

    def _serve_file(self, full_path: str, content_type: str):
        if not os.path.exists(full_path):
            self.send_error(404, "File not found")
            return
        try:
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Internal file read error: {e}")

    def _handle_sse_stream(self):
        client_id = f"client_{id(self)}_{time.time()}"
        client_q = self.event_bus.register_client_queue(client_id)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            while True:
                try:
                    event = client_q.get(timeout=25.0)
                    payload = json.dumps(event.to_dict())
                    sse_message = f"data: {payload}\n\n"
                    self.wfile.write(sse_message.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # Keep-alive heartbeat comment
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.event_bus.unregister_client_queue(client_id)

    def _handle_zip_download(self, slug: str):
        # Look for zip matching project slug in base_output_dir
        target_dir = os.path.abspath(os.path.join(self.base_output_dir, slug))
        zip_file = os.path.join(target_dir, f"{slug}.zip")

        if not os.path.exists(zip_file):
            # Try searching subdirectories for matching zip
            found = None
            if os.path.exists(self.base_output_dir):
                for root, _, files in os.walk(self.base_output_dir):
                    for f in files:
                        if f.endswith(".zip") and (slug in f or slug in root):
                            found = os.path.join(root, f)
                            break
                    if found:
                        break
            zip_file = found

        if not zip_file or not os.path.exists(zip_file):
            self.send_error(404, f"ZIP Archive for '{slug}' not found.")
            return

        try:
            with open(zip_file, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(zip_file)}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, f"Error downloading ZIP: {e}")

    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress noisy HTTP request stdout logs
        return


def start_web_server(host: str = "127.0.0.1", port: int = 8080, event_bus: Optional[EventBus] = None, base_output_dir: str = "output"):
    bus = event_bus or EventBus()
    WorkflowHTTPHandler.event_bus = bus
    WorkflowHTTPHandler.base_output_dir = base_output_dir

    server = ThreadingHTTPServer((host, port), WorkflowHTTPHandler)
    print(f"\n[Browser UI Server Running] Accessible at http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web server.")
        server.server_close()
