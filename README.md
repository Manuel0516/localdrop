# LocalDrop

Simple clipboard sync and file transfer between a Linux machine and a MacBook,
over your local network. No cloud, no accounts, no database — just two small
Python daemons talking to each other.

- **Bidirectional clipboard sync** (Linux ⇄ macOS)
- **Send files** to the other device with one command
- **Zero third-party dependencies** — pure Python standard library
- **One config file** controls everything
- **Auto-start on Linux** with a user systemd service
- **Auto-start on macOS** with a LaunchAgent

> Intended for trusted local networks only. Authentication is a single shared
> token over plain HTTP. Do not expose it to the public internet.

## How it works

Both devices run the same program. Each one is at the same time:

1. A tiny HTTP server that receives clipboard text and files.
2. A client that pushes local clipboard changes and files to the peer.

```
Linux daemon  ⇄  Mac daemon
```

## Requirements

- Python **3.11+** (uses the built-in `tomllib`)
- **Linux:** `wl-clipboard` and `libnotify`
  ```bash
  sudo pacman -S python wl-clipboard libnotify
  ```
- **macOS:** nothing extra — `pbcopy`/`pbpaste`/`osascript` are built in.

No `pip install` is needed.

## Setup

Install in `~/projects/localdrop` on **both** devices — the scripts and
systemd service assume this path:

```bash
mkdir -p ~/projects
git clone https://github.com/Manuel0516/localdrop ~/projects/localdrop
cd ~/projects/localdrop
cp examples/config.example.toml config.toml
```

Then edit `config.toml`. The two configs are nearly identical — only these
differ:

| field             | Linux            | macOS              |
| ----------------- | ---------------- | ------------------ |
| `device.name`     | `linux`          | `macbook`          |
| `device.platform` | `linux`          | `macos`            |
| `peer.name`       | `macbook`        | `linux`            |
| `peer.host`       | Mac's IP         | Linux's IP         |

Set the **same** `shared_token` on both machines.

## Usage

```bash
python main.py daemon      # run the server + clipboard watcher
python main.py ping        # check the peer is reachable
python main.py send FILE   # send a file to the peer
```

Example:

```bash
python main.py send ~/Pictures/photo.png
```

Received files land in `download_dir` (default `~/Downloads/LocalDrop/`).
Existing names are kept by adding a `-1`, `-2`, … suffix.

## Auto-start on Linux (systemd)

```bash
mkdir -p ~/.config/systemd/user
cp examples/localdrop.service.example ~/.config/systemd/user/localdrop.service
# edit the paths inside the service file to match where you cloned localdrop
systemctl --user daemon-reload
systemctl --user enable --now localdrop.service
journalctl --user -u localdrop.service -f   # follow logs
```

## Auto-start on macOS (launchd, optional)

LocalDrop needs Python 3.11+ because it uses the standard-library `tomllib`
module. On macOS, `/usr/bin/python3` may be Apple's older Python and can fail
with `ModuleNotFoundError: No module named 'tomllib'`. Use the full path to a
newer Python instead, for example Homebrew's `/opt/homebrew/bin/python3`.

```bash
which python3
python3 --version
```

Copy the example, edit the Python path and project paths, then install it:

```bash
cp examples/com.localdrop.plist.example com.localdrop.plist
# edit com.localdrop.plist:
# - ProgramArguments[0] should be your Python 3.11+ path
# - /Users/YOURNAME/projects/localdrop should match your clone path

mkdir -p ~/Library/LaunchAgents
cp com.localdrop.plist ~/Library/LaunchAgents/com.localdrop.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.localdrop.plist
```

After editing the plist, reload it:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.localdrop.plist
cp com.localdrop.plist ~/Library/LaunchAgents/com.localdrop.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.localdrop.plist
```

Check that it is running:

```bash
launchctl print gui/$(id -u)/com.localdrop
```

## HTTP API

| Method | Path         | Auth header                   | Body                              |
| ------ | ------------ | ----------------------------- | --------------------------------- |
| GET    | `/health`    | —                             | —                                 |
| POST   | `/clipboard` | `X-LocalDrop-Token: <token>`  | JSON `{"source": "...", "text": "..."}` |
| POST   | `/file`      | `X-LocalDrop-Token: <token>` + `X-LocalDrop-Filename: <name>` | raw file bytes |

> **Note:** `/file` takes the raw request body plus a filename header rather than
> a multipart form. This keeps the code tiny and dependency-free (Python 3.13
> removed the `cgi` module). See `DEVLOG.md` for the reasoning.

## Shortcuts & integrations

See **[docs/shortcuts.md](docs/shortcuts.md)** for step-by-step guides:

- **Hyprland keybinding** — open a file picker and send to Mac with one key press
- **macOS Finder Quick Action** — right-click any file → Send with LocalDrop
- **iPhone Shortcuts** — send clipboard or files to Linux from the Share Sheet
  *(Linux → iPhone is not supported in v1)*

## Project layout

```
main.py                    CLI entry: daemon | send | ping
src/
  config.py                load/validate config.toml
  clipboard.py             read/write clipboard + watcher loop
  transfer.py              HTTP server + client (send/ping)
  notify.py                optional desktop notifications
scripts/
  localdrop-send.sh        Linux/Hyprland file picker helper
  localdrop-send-mac.sh    macOS file picker helper
docs/
  shortcuts.md             Hyprland, macOS, and iPhone integration guide
examples/
  config.example.toml      config template (copy to config.toml)
  localdrop.service.example     Linux systemd user unit
  com.localdrop.plist.example   macOS launchd agent
```

## Troubleshooting

### Mac cannot reach the Linux server (connection refused / timeout)

**Firewall:** Linux may be blocking port 8765. If you use `ufw`:

```bash
sudo ufw allow 8765/tcp
```

**Multiple network interfaces:** If Linux has both ethernet and WiFi, make sure
`server.host = "0.0.0.0"` in Linux's `config.toml` (not a specific IP), and
that the Mac's `peer.host` points to the correct Linux IP. You can find Linux's
IPs with:

```bash
ip addr show | grep "inet "
```

**Daemon not running:** Confirm the daemon is up and listening:

```bash
ss -ltn | grep 8765
```

### Linux cannot reach the Mac server

macOS does not have a built-in firewall rule blocking this, but check that the
Mac's daemon is actually running (`python main.py daemon`) and that Linux's
`peer.host` is set to the Mac's current IP (can change on DHCP networks).

### macOS LaunchAgent fails with `Bootstrap failed: 5`

This usually means launchd could not start the job, but the message is generic.
For LocalDrop, first check the Python path in the plist. If it points to
`/usr/bin/python3`, it may be too old for `tomllib`. Replace it with the path
from `which python3`, as long as that Python is 3.11 or newer.

Also make sure you reload the job after changing the plist; copying the file
alone does not update an already-loaded LaunchAgent.

## License

MIT — see [LICENSE](LICENSE).
