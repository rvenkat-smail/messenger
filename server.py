from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import time

# ---------- Protocol constants ----------

TYPE_MANAGEMENT = 0
TYPE_CONTROL = 1
TYPE_DATA = 2

MSG_ASSOCIATE = 0
MSG_GET = 0
MSG_PUSH = 1
MSG_GETRESPONSE = 0

ASSOC_TIMEOUT = 300          # 5 minutes
MAX_PAYLOAD_LEN = 254
MAX_BUFFER_SIZE = 5

# ---------- Server state ----------

# client_id -> last_activity_time
associations = {}

# receiver_id -> list of messages
# each message: { "from": sender_id, "payload": payload }
buffers = {}


class MessengerHandler(BaseHTTPRequestHandler):

    # --- ADD THIS HERE ---
    def log_message(self, format, *args):
        return
    # --------------------

    def do_POST(self):

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            frame = json.loads(body.decode())
        except Exception:
            return

        # -------- LOG incoming application frame --------
        print("[IN ]", frame)

        try:
            msg_type = frame["type"]
            msg_code = frame["message"]
            client_id = frame["id"]
        except Exception:
            response = {
                "type": TYPE_MANAGEMENT,
                "message": "MALFORMED_FRAME"
            }
            self._send_and_log(response)
            return

        now = time.time()

        # ---------- MANAGEMENT / ASSOCIATE ----------
        if msg_type == TYPE_MANAGEMENT and msg_code == MSG_ASSOCIATE:
            associations[client_id] = now

            response = {
                "type": TYPE_MANAGEMENT,
                "message": "ASSOCIATION_SUCCESS",
                "id": client_id
            }
            self._send_and_log(response)
            return

        # ---------- DATA / PUSH ----------
        if msg_type == TYPE_DATA and msg_code == MSG_PUSH:

            last = associations.get(client_id)
            if last is None or (now - last) > ASSOC_TIMEOUT:
                response = {
                    "type": TYPE_DATA,
                    "message": "NOT_ASSOCIATED",
                    "id": client_id
                }
                self._send_and_log(response)
                return

            try:
                receiver_id = frame["id2"]
                payload = frame["payload"]
                length = frame["length"]
            except Exception:
                response = {
                    "type": TYPE_DATA,
                    "message": "MALFORMED_FRAME",
                    "id": client_id
                }
                self._send_and_log(response)
                return

            if length > MAX_PAYLOAD_LEN or len(payload) != length:
                response = {
                    "type": TYPE_DATA,
                    "message": "INVALID_LENGTH",
                    "id": client_id
                }
                self._send_and_log(response)
                return

            if receiver_id not in buffers:
                buffers[receiver_id] = []

            if len(buffers[receiver_id]) >= MAX_BUFFER_SIZE:
                response = {
                    "type": TYPE_DATA,
                    "message": "BUFFER_FULL",
                    "id": client_id
                }
                self._send_and_log(response)
                return

            buffers[receiver_id].append({
                "from": client_id,
                "payload": payload
            })

            response = {
                "type": TYPE_DATA,
                "message": "PUSH_SUCCESS",
                "id": client_id
            }
            self._send_and_log(response)
            return

        # ---------- CONTROL / GET ----------
        if msg_type == TYPE_CONTROL and msg_code == MSG_GET:

            last = associations.get(client_id)
            if last is None or (now - last) > ASSOC_TIMEOUT:
                response = {
                    "type": TYPE_CONTROL,
                    "message": "NOT_ASSOCIATED",
                    "id": client_id
                }
                self._send_and_log(response)
                return

            if client_id not in buffers or len(buffers[client_id]) == 0:
                response = {
                    "type": TYPE_CONTROL,
                    "message": "BUFFER_EMPTY",
                    "id": client_id
                }
                self._send_and_log(response)
                return

            msg = buffers[client_id].pop(0)
            payload = msg["payload"]
            sender_id = msg["from"]

            response = {
                "type": TYPE_DATA,
                "message": MSG_GETRESPONSE,
                "id": client_id,
                "id2": sender_id,
                "length": len(payload),
                "payload": payload
            }
            self._send_and_log(response)
            return

        # ---------- UNKNOWN ----------
        response = {
            "type": msg_type,
            "message": "UNKNOWN_MESSAGE",
            "id": client_id
        }
        self._send_and_log(response)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Messenger server running")

    # ---------- Helper ----------
    def _send_and_log(self, response):
        # -------- LOG outgoing application frame --------
        print("[OUT]", response)

        data = json.dumps(response).encode()
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

