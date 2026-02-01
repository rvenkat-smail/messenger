from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import time

# Constants (assignment-style)
TYPE_MANAGEMENT = 0
TYPE_DATA = 2

MSG_ASSOCIATE = 0
MSG_PUSH = 1

ASSOC_TIMEOUT = 60  # seconds

# client_id -> last_activity_time
associations = {}


class MessengerHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            frame = json.loads(body.decode())
            msg_type = frame["type"]
            msg_code = frame["message"]
            client_id = frame["id"]
        except Exception:
            self._send_json({
                "type": TYPE_MANAGEMENT,
                "message": "MALFORMED_FRAME"
            })
            return

        # ---------------- MANAGEMENT / ASSOCIATE ----------------
        if msg_type == TYPE_MANAGEMENT and msg_code == MSG_ASSOCIATE:
            associations[client_id] = time.time()

            self._send_json({
                "type": TYPE_MANAGEMENT,
                "message": "ASSOCIATION_SUCCESS",
                "id": client_id
            })
            return

        # ---------------- DATA / PUSH ----------------
        if msg_type == TYPE_DATA and msg_code == MSG_PUSH:
            now = time.time()
            last = associations.get(client_id)

            if last is None or (now - last) > ASSOC_TIMEOUT:
                self._send_json({
                    "type": TYPE_DATA,
                    "message": "NOT_ASSOCIATED",
                    "id": client_id
                })
                return

            # PUSH accepted (no buffering yet)
            self._send_json({
                "type": TYPE_DATA,
                "message": "PUSH_ACCEPTED",
                "id": client_id
            })
            return

        # ---------------- UNKNOWN MESSAGE ----------------
        self._send_json({
            "type": msg_type,
            "message": "UNKNOWN_MESSAGE",
            "id": client_id
        })

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Messenger server running")

    # ---------- Helper ----------
    def _send_json(self, payload):
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), MessengerHandler)
    print(f"Messenger server running on port {port}")
    server.serve_forever()

