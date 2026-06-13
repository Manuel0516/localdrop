# LocalDrop Project Guidelines

## 1. Project Goal

Create a very simple local-network program for syncing clipboard content and sending files between a Linux computer and a MacBook.

The project should prioritize:

- Extremely simple code.
- Clean and readable structure.
- Minimal dependencies.
- One configuration file.
- Bidirectional clipboard sync between Linux and macOS.
- Optional file transfer.
- Optional encryption.
- Automatic startup on Linux when the user session starts.

The first target platform is:

- Linux: CachyOS with Hyprland, Wayland.
- macOS: MacBook.
- Phone support can be added later through iPhone Shortcuts.

The project should be designed so that an AI or developer can implement it directly from this specification.

---

## 2. Project Name

Suggested name:

```text
localdrop
```

Alternative names are acceptable, but the codebase should remain small and direct.

---

## 3. Core Concept

Both Linux and macOS should run the same Python program.

Each device acts as both:

1. A small HTTP server that receives clipboard/file data.
2. A client that sends clipboard/file data to the peer device.

Architecture:

```text
Linux daemon  ←→  Mac daemon
```

There should be no central cloud server, no accounts, no database, and no external service.

The system should work over the local network first.

---

## 4. Required Features

### 4.1 Bidirectional Clipboard Sync

The program should:

1. Read the local clipboard regularly.
2. Detect when the clipboard changes.
3. Send the new clipboard content to the peer device.
4. Receive clipboard content from the peer device.
5. Set the local clipboard to the received content.
6. Avoid infinite clipboard loops.

Example flow:

```text
User copies text on Linux
↓
Linux detects clipboard change
↓
Linux sends text to Mac
↓
Mac receives text
↓
Mac sets macOS clipboard
```

And the reverse direction should also work:

```text
User copies text on Mac
↓
Mac detects clipboard change
↓
Mac sends text to Linux
↓
Linux receives text
↓
Linux sets Wayland clipboard
```

---

### 4.2 File Transfer

The program should support basic file transfer.

Minimum behavior:

1. User runs a command to send a file to the peer.
2. Peer receives the file.
3. Peer saves it to a configured download directory.
4. Peer shows a notification if possible.

Example:

```bash
localdrop send ~/Pictures/photo.png
```

The peer should save the file to:

```text
~/Downloads/LocalDrop/
```

unless another directory is configured.

---

### 4.3 Optional Encryption

The config file must allow encryption to be enabled or disabled.

The first implementation can use a simple model:

```toml
[security]
encryption = false
shared_token = "change-this-token"
```

Initial behavior:

- If `encryption = false`, use plain HTTP with token authentication.
- If `encryption = true`, use HTTPS if implemented.

Important:

For version 1, do not over-engineer encryption. Keep the implementation simple.

Acceptable first version:

- Always require a shared token.
- Send the token in a header.
- Reject requests with missing or incorrect token.
- Add real HTTPS/encryption later.

Suggested header:

```text
X-LocalDrop-Token: <shared_token>
```

---

### 4.4 Automatic Startup on Linux

The Linux daemon should be able to run automatically using a user-level `systemd` service.

The project should include a sample service file:

```ini
[Unit]
Description=LocalDrop clipboard and file sync

[Service]
ExecStart=/usr/bin/python /home/manuel/projects/localdrop/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
```

The user should enable it with:

```bash
systemctl --user enable --now localdrop.service
```

The service should run when the Linux user session starts.

---

### 4.5 macOS Startup

macOS automatic startup can be added with `launchd`, but it is not required for the first implementation.

A later version should include a sample `launchd` plist.

---

## 5. Non-Goals

Do not implement these in the first version:

- User accounts.
- Cloud sync.
- GUI.
- Database.
- Complex device discovery.
- Bluetooth discovery.
- Wi-Fi Direct.
- Full AirDrop protocol compatibility.
- Complex end-to-end encryption.
- Mobile app.

Keep the program simple.

---

## 6. Configuration

All configuration must live in a single file:

```text
config.toml
```

Example Linux config:

```toml
[device]
name = "linux"
platform = "linux"

[server]
host = "0.0.0.0"
port = 8765

[peer]
name = "macbook"
host = "192.168.1.20"
port = 8765

[clipboard]
enabled = true
poll_interval = 0.7

[files]
enabled = true
download_dir = "~/Downloads/LocalDrop"

[security]
encryption = false
shared_token = "change-this-token"

[notifications]
enabled = true
```

Example macOS config:

```toml
[device]
name = "macbook"
platform = "macos"

[server]
host = "0.0.0.0"
port = 8765

[peer]
name = "linux"
host = "192.168.1.10"
port = 8765

[clipboard]
enabled = true
poll_interval = 0.7

[files]
enabled = true
download_dir = "~/Downloads/LocalDrop"

[security]
encryption = false
shared_token = "change-this-token"

[notifications]
enabled = true
```

The two configs should be almost identical except for:

- `device.name`
- `device.platform`
- `peer.name`
- `peer.host`

---

## 7. Suggested Project Structure

The first version should be as small as possible.

Preferred version 1 structure:

```text
localdrop/
├── main.py
├── config.toml
├── requirements.txt
├── localdrop.service.example
└── README.md
```

Avoid splitting into many files until necessary.

If the code becomes too long, then use:

```text
localdrop/
├── main.py
├── config.py
├── clipboard.py
├── transfer.py
├── security.py
├── config.toml
├── requirements.txt
├── localdrop.service.example
└── README.md
```

But prefer the one-file version first.

---

## 8. Dependencies

Keep dependencies minimal.

Recommended Python dependencies:

```text
fastapi
uvicorn
requests
tomli; python_version < "3.11"
```

If using Python 3.11+, use the built-in:

```python
import tomllib
```

Avoid large frameworks.

Do not use Django, Flask with plugins, databases, Electron, or complex GUI frameworks.

---

## 9. Clipboard Commands

### 9.1 Linux / Wayland / Hyprland

Use:

```bash
wl-copy
wl-paste
```

Install with:

```bash
sudo pacman -S wl-clipboard
```

Read clipboard:

```bash
wl-paste
```

Write clipboard:

```bash
printf '%s' "text" | wl-copy
```

### 9.2 macOS

Use built-in commands:

```bash
pbpaste
pbcopy
```

Read clipboard:

```bash
pbpaste
```

Write clipboard:

```bash
printf '%s' "text" | pbcopy
```

---

## 10. HTTP API

Keep the API very small.

### 10.1 Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "device": "linux"
}
```

---

### 10.2 Receive Clipboard

```http
POST /clipboard
```

Headers:

```text
X-LocalDrop-Token: <shared_token>
```

Body:

```json
{
  "source": "macbook",
  "text": "copied text"
}
```

Response:

```json
{
  "status": "ok"
}
```

Behavior:

1. Validate token.
2. Ignore if `source` is same as local device name.
3. Set local clipboard to `text`.
4. Store this text as the last remote clipboard value.
5. Do not send it back immediately.

---

### 10.3 Receive File

```http
POST /file
```

Headers:

```text
X-LocalDrop-Token: <shared_token>
```

Body:

Multipart form upload:

```text
file=<uploaded file>
source=<source device name>
```

Behavior:

1. Validate token.
2. Save file to configured download directory.
3. Avoid overwriting existing files by adding a suffix.
4. Show notification if enabled.

---

## 11. Clipboard Loop Protection

The program must avoid infinite loops.

Simple strategy:

Maintain:

```python
last_local_clipboard = ""
last_remote_clipboard = ""
```

Loop:

```python
current = read_clipboard()

if current == last_remote_clipboard:
    last_local_clipboard = current
    continue

if current != last_local_clipboard:
    send_to_peer(current)
    last_local_clipboard = current
```

When receiving remote clipboard:

```python
last_remote_clipboard = received_text
set_clipboard(received_text)
```

This is enough for version 1.

---

## 12. Program Modes

The script should support a daemon mode and simple commands.

### 12.1 Run Daemon

```bash
python main.py daemon
```

This should:

1. Load config.
2. Start HTTP server.
3. Start clipboard watcher thread if enabled.
4. Keep running.

### 12.2 Send File

```bash
python main.py send ~/path/to/file.pdf
```

This should:

1. Load config.
2. Send the file to the configured peer.
3. Print success or error.

### 12.3 Test Peer

```bash
python main.py ping
```

This should call:

```http
GET http://peer-host:peer-port/health
```

and print the result.

---

## 13. Notifications

### 13.1 Linux

Use:

```bash
notify-send "LocalDrop" "Received file: photo.png"
```

### 13.2 macOS

Use:

```bash
osascript -e 'display notification "Received file" with title "LocalDrop"'
```

Notifications should be optional through config:

```toml
[notifications]
enabled = true
```

---

## 14. Error Handling

Keep error handling simple but clear.

The program should handle:

- Peer offline.
- Wrong token.
- Clipboard command missing.
- File path does not exist.
- Download directory does not exist.
- Port already in use.

Behavior:

- Print clear errors.
- Do not crash the daemon for normal network failures.
- Retry clipboard sending on the next change, not continuously.

---

## 15. Security Model

This tool is intended for trusted local networks.

Minimum security:

- Shared token required for all POST endpoints.
- Ignore requests without the correct token.
- Do not expose the server to the public internet.

Optional later security:

- HTTPS with self-signed certificates.
- Tailscale-only mode.
- End-to-end encryption.
- Pairing with QR code.

For version 1, do not implement complex cryptography unless explicitly requested.

---

## 16. iPhone Support Later

Phone support should be added after Mac ↔ Linux works.

The simplest phone integration is iPhone Shortcuts.

Possible shortcuts:

1. Send clipboard to Linux.
2. Send selected file to Linux.
3. Send selected photo to Linux.
4. Send URL to Linux.

The shortcut should make an HTTP POST request to:

```text
http://linux-ip:8765/clipboard
```

or:

```text
http://linux-ip:8765/file
```

with the shared token header.

Do not build a mobile app initially.

---

## 17. Implementation Order

Implement in this order:

### Step 1: Config loader

- Load `config.toml`.
- Expand `~` in paths.
- Validate required fields.

### Step 2: Clipboard helpers

Implement:

```python
read_clipboard()
write_clipboard(text)
```

Support:

- Linux with `wl-paste` and `wl-copy`.
- macOS with `pbpaste` and `pbcopy`.

### Step 3: HTTP server

Implement:

- `GET /health`
- `POST /clipboard`
- `POST /file`

### Step 4: Clipboard watcher

Implement polling loop:

```python
while True:
    check clipboard
    send changes
    sleep(poll_interval)
```

### Step 5: File sending command

Implement:

```bash
python main.py send file.txt
```

### Step 6: Systemd service

Add Linux service example.

### Step 7: macOS launchd file

Optional later.

### Step 8: iPhone Shortcuts

Optional later.

---

## 18. Coding Style Requirements

The code must be extremely simple.

Rules:

1. Prefer plain functions over classes.
2. Use clear variable names.
3. Avoid clever abstractions.
4. Avoid nested logic where possible.
5. Keep functions short.
6. Add comments only where useful.
7. No unnecessary type gymnastics.
8. No database.
9. No background task framework.
10. No complex dependency injection.

Preferred style:

```python
def read_clipboard(config):
    if config["device"]["platform"] == "linux":
        return run_command(["wl-paste"])
    if config["device"]["platform"] == "macos":
        return run_command(["pbpaste"])
    raise RuntimeError("Unsupported platform")
```

Avoid style like:

```python
class ClipboardProviderFactory(AbstractClipboardManager):
    ...
```

This project should be understandable by reading `main.py` from top to bottom.

---

## 19. Acceptance Criteria for Version 1

The project is successful when:

1. Linux and Mac can both run the daemon.
2. Copying text on Linux updates the Mac clipboard.
3. Copying text on Mac updates the Linux clipboard.
4. Clipboard loops do not happen.
5. A file can be sent from Linux to Mac.
6. A file can be sent from Mac to Linux.
7. Configuration is controlled from one `config.toml` file.
8. Linux can start the daemon automatically with systemd.
9. The code remains simple and readable.

---

## 20. Example Commands

Install Linux dependencies:

```bash
sudo pacman -S python python-pip wl-clipboard libnotify
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run daemon:

```bash
python main.py daemon
```

Ping peer:

```bash
python main.py ping
```

Send file:

```bash
python main.py send ~/Downloads/test.pdf
```

Enable Linux startup:

```bash
mkdir -p ~/.config/systemd/user
cp localdrop.service.example ~/.config/systemd/user/localdrop.service
systemctl --user daemon-reload
systemctl --user enable --now localdrop.service
```

Check logs:

```bash
journalctl --user -u localdrop.service -f
```

---

## 21. Future Features

Only add these after version 1 works:

- Device discovery with mDNS/Bonjour.
- Rofi menu for Hyprland.
- macOS menu bar app.
- iPhone Shortcuts guide.
- QR-code pairing.
- Tailscale mode.
- HTTPS certificates.
- End-to-end encryption.
- Clipboard history.
- Image clipboard support.
- File drag-and-drop.

---

## 22. Final Instruction for the Implementing AI

Implement the simplest working version first.

Do not over-engineer.

Start with one file: `main.py`.

Use `config.toml` for all configuration.

Make Mac ↔ Linux clipboard sync work before adding anything else.

After clipboard sync works, add file transfer.

Keep the code clean enough that a beginner can understand it.
