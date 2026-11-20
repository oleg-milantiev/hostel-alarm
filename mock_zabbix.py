"""Mock Zabbix server — always returns stars_count_0 = 40"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler


class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = {"stars_count_0": 40}
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[Mock] {args[0]}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9999), MockHandler)
    print("Mock Zabbix running on http://127.0.0.1:9999/")
    server.serve_forever()
