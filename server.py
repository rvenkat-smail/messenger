from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json

class SimpleHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path != "/frame":
            self.send_response(404)
            self.end_headers()
            return

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

