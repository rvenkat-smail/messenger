from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import time

# Association timeout (seconds)
ASSOC_TIMEOUT = 60

# client_id -> last_activity_time
associations = {}


class SimpleHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        # ---------- ASSOCIATE ----------
        if self.path == "/associate":

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                frame = json.loads(body.decode())
                client_id = frame["client_id"]
                msg_type = frame["type"]
                message = frame["message"]
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            if msg_type != "MANAGEMENT" or message != "ASSOCIATE":
                self.send_response(400)
                self.end_headers()
                return

            now = time.time()
            last = associations.get(client_id)

            if last is not None and (now - last) < ASSOC_TIMEOUT:
                response = {
                    "type": "MANAGEMENT",
                    "message": "ASSOCIATIONFAILED",
                    "client_id": client_id
                }
                data = json.dumps(response).encode()
                self.send_response(403)
            else:
                associations[client_id] = now
                response = {
                    "type": "MANAGEMENT",
                    "message": "ASSOCIATIONSUCCESS",
                    "client_id": client_id
                }
                data = json.dumps(response).encode()
                self.send_response(200)

            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # ---------- FRAME (existing logic) ----------
        if self.path == "/frame":

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                frame = json.loads(body.decode())
                frame_id = frame["id"]
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            response_frame = {
                "id": frame_id + 1
            }

            response_data = json.dumps(response_frame).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data)
            return

        # ---------- UNKNOWN POST ----------
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Server is running on Render")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Server running on port {port}")
    server.serve_forever()

