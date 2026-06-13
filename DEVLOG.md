# LocalDrop — Development Log

This file documents the development process, the decisions taken along the way,
and why. It is meant to be read alongside `localdrop_project_guidelines.md`
(the original specification).

## 2026-06-13 — Initial implementation (v1)

### Goal
Implement the simplest working version from the guidelines: bidirectional
clipboard sync + file transfer between Linux (Wayland) and macOS, controlled by
one `config.toml`, with no external services.

### Environment notes
- Target Linux box: CachyOS / Hyprland / Wayland, Python 3.13.
- `wl-clipboard` and `notify-send` already installed.
- Python's system install is externally managed (PEP 668), so installing pip
  packages would require a virtualenv or `--break-system-packages`.

### Key decisions

1. **Standard library HTTP server instead of FastAPI/uvicorn.**
   The guidelines *recommend* FastAPI but also list "minimal dependencies" as a
   top priority. Using `http.server` + `urllib` means **zero** third-party
   packages, no virtualenv, and it runs out of the box on the externally-managed
   Arch Python. Simpler to read, too. FastAPI can be revisited later if needed.

2. **`/file` uses a raw request body + `X-LocalDrop-Filename` header, not a
   multipart form.**
   Python 3.13 **removed the `cgi` module**, which is what you'd normally use to
   parse `multipart/form-data` without a dependency. Sending the file as the raw
   body with the name in a header is dramatically simpler and keeps the
   dependency count at zero. This is a small, documented deviation from the
   spec's §10.3.

3. **Split into a few small modules instead of one `main.py`.**
   The spec prefers a single file but allows a split "if it grows". At the user's
   request the code is organised into focused modules — `config.py`,
   `clipboard.py`, `transfer.py`, `notify.py`, with `main.py` as the CLI entry —
   while staying minimal (each file does one thing).

4. **No separate `security.py`.**
   v1 security is just "is the shared token correct?". A dedicated module would be
   nearly empty, so the token check lives inline in `transfer.py`. Real
   encryption/HTTPS is explicitly out of scope for v1 (spec §15).

5. **`config.example.toml` committed; `config.toml` is git-ignored.**
   The real config contains the shared token. To keep the public repo safe, the
   repo ships only the template; users copy it to `config.toml` (ignored by git).

### Loop protection
Implemented exactly as described in spec §11. Shared state lives in
`clipboard.py` (`last_local`, `last_remote`) behind a `threading.Lock`, because
the HTTP handler thread and the watcher thread both touch it. When a remote
value arrives it is recorded via `set_remote()` *before* the clipboard is
written, so the watcher recognises it and does not echo it back.

### File layout
```
main.py        CLI dispatch (daemon | send | ping)
config.py      load + validate config.toml, expand ~ paths
clipboard.py   read/write clipboard, watcher loop, loop-guard state
transfer.py    HTTP server (routes + token check) and client send/ping
notify.py      optional desktop notifications
```

### Verification performed
- `python main.py ping` with the peer offline → clean "Peer unreachable"
  message, no traceback.
- Daemon up locally:
  - `GET /health` → `{"status":"ok","device":"linux"}`.
  - `POST /clipboard` with a different `source` → local clipboard updates
    (`wl-paste` confirms).
  - Missing/wrong token → `401`.
  - `POST /file` → saved into the download dir; a second send creates a
    `-1`-suffixed copy.
- Full two-machine round-trip (Linux ⇄ Mac) is the real acceptance test
  (spec §19) and is left for the user to run with both devices present.

### Still open / future work (spec §21)
mDNS discovery, Hyprland Rofi menu, macOS menu-bar app, iPhone Shortcuts,
QR pairing, Tailscale mode, HTTPS, end-to-end encryption, image-clipboard
support.
