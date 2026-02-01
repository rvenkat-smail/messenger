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

        # Only handle ASSOCIATE
        if self.path != "/associate":
            self.send_response(200)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            frame = json.loads(body.decode())
            client_id = frame["client_id"]
            msg_type = frame["type"]
            message = frame["message"]
        except Exception:
            # Even malformed frames get 200 OK (application decides meaning)
            self.send_response(200)
            self.end_headers()
            return

        # Only MANAGEMENT / ASSOCIATE is meaningful
        if msg_type == "MANAGEMENT" and message == "ASSOCIATE":
            # Renew or create association
            associations[client_id] = time.time()

            response = {
                "type": "MANAGEMENT",
                "message": "ASSOCIATION_SUCCESS",
                "client_id": client_id
            }
            data = json.dumps(response).encode()
        else:
            # Unknown application message, still 200 OK
            response = {
                "type": "MANAGEMENT",
                "message": "IGNORED",
                "client_id": client_id
            }
            data = json.dumps(response).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Messenger server running (ASSOCIATE only)")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Server running on port {port}")
    server.serve_forever()

