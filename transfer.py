"""HTTP server and client.

Each device runs a small HTTP server (to receive clipboard text and files) and
acts as a client (to send them to the peer). Authentication is a single shared
token sent in the ``X-LocalDrop-Token`` header -- no real cryptography in v1, so
keep this on a trusted local network only.
"""

import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import clipboard
from notify import notify

TOKEN_HEADER = "X-LocalDrop-Token"
FILENAME_HEADER = "X-LocalDrop-Filename"


# --------------------------------------------------------------------------- #
# Server side
# --------------------------------------------------------------------------- #

def make_handler(config):
    """Build a request handler class bound to this device's config."""
    token = config["security"]["shared_token"]
    device_name = config["device"]["name"]

    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _check_token(self):
            if self.headers.get(TOKEN_HEADER) != token:
                self._send_json(401, {"error": "invalid token"})
                return False
            return True

        def _read_body(self):
            length = int(self.headers.get("Content-Length", 0))
            return self.rfile.read(length)

        def log_message(self, *args):
            # Stay quiet -- the default handler logs every request to stderr.
            pass

        def do_GET(self):
            if self.path == "/health":
                self._send_json(200, {"status": "ok", "device": device_name})
            else:
                self._send_json(404, {"error": "not found"})

        def do_POST(self):
            if not self._check_token():
                return
            if self.path == "/clipboard":
                self._handle_clipboard()
            elif self.path == "/file":
                self._handle_file()
            else:
                self._send_json(404, {"error": "not found"})

        def _handle_clipboard(self):
            data = json.loads(self._read_body() or b"{}")
            source = data.get("source", "")
            text = data.get("text", "")

            # Ignore anything we somehow sent to ourselves.
            if source == device_name:
                self._send_json(200, {"status": "ignored"})
                return

            # Record it as remote first (loop guard), then set the clipboard.
            clipboard.set_remote(text)
            clipboard.write_clipboard(config, text)
            self._send_json(200, {"status": "ok"})

        def _handle_file(self):
            raw_name = self.headers.get(FILENAME_HEADER, "file")
            # Use only the base name so a peer can't write outside the dir.
            filename = os.path.basename(raw_name) or "file"
            content = self._read_body()

            download_dir = config["files"]["download_dir"]
            os.makedirs(download_dir, exist_ok=True)
            path = _unique_path(os.path.join(download_dir, filename))

            with open(path, "wb") as f:
                f.write(content)

            notify(config, "LocalDrop", f"Received file: {os.path.basename(path)}")
            self._send_json(200, {"status": "ok", "saved": os.path.basename(path)})

    return Handler


def _unique_path(path):
    """Return ``path``, adding a -1, -2, ... suffix if it already exists."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}-{i}{ext}"):
        i += 1
    return f"{base}-{i}{ext}"


def serve(config):
    """Run the HTTP server forever (blocking)."""
    host = config["server"]["host"]
    port = config["server"]["port"]
    server = ThreadingHTTPServer((host, port), make_handler(config))
    print(f"[server] listening on {host}:{port}")
    server.serve_forever()


# --------------------------------------------------------------------------- #
# Client side
# --------------------------------------------------------------------------- #

def _peer_url(config, path):
    peer = config["peer"]
    return f"http://{peer['host']}:{peer['port']}{path}"


def _request(config, path, data=None, extra_headers=None, method="POST"):
    headers = {TOKEN_HEADER: config["security"]["shared_token"]}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(
        _peer_url(config, path), data=data, headers=headers, method=method
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read() or b"{}")


def send_clipboard(config, text):
    """Send clipboard text to the peer's /clipboard endpoint."""
    payload = json.dumps({"source": config["device"]["name"], "text": text}).encode()
    return _request(
        config, "/clipboard", data=payload,
        extra_headers={"Content-Type": "application/json"},
    )


def send_file(config, path):
    """Send a file to the peer's /file endpoint (raw body + filename header)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No such file: {path}")
    with open(path, "rb") as f:
        data = f.read()
    return _request(
        config, "/file", data=data,
        extra_headers={
            FILENAME_HEADER: os.path.basename(path),
            "Content-Type": "application/octet-stream",
        },
    )


def ping(config):
    """Call the peer's /health endpoint and return its response."""
    return _request(config, "/health", method="GET")
