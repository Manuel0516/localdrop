#!/usr/bin/env python3
"""LocalDrop -- simple clipboard sync and file transfer over the local network.

Usage:
    python main.py daemon        # run the server + clipboard watcher
    python main.py send FILE     # send a file to the peer
    python main.py ping          # check that the peer is reachable
"""

import sys
import threading
import urllib.error

import clipboard
import transfer
from config import load_config

USAGE = "Usage: python main.py [daemon | send FILE | ping]"


def run_daemon(config):
    """Start the HTTP server and (optionally) the clipboard watcher."""
    if config.get("clipboard", {}).get("enabled", True):
        watcher = threading.Thread(
            target=clipboard.watch_clipboard, args=(config,), daemon=True
        )
        watcher.start()
        print("[daemon] clipboard watcher started")

    # serve() blocks forever; Ctrl-C exits cleanly.
    try:
        transfer.serve(config)
    except KeyboardInterrupt:
        print("\n[daemon] stopped")


def run_send(config, path):
    """Send a single file to the peer."""
    try:
        result = transfer.send_file(config, path)
        print(f"Sent: {result.get('saved', path)}")
    except FileNotFoundError as e:
        sys.exit(str(e))
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach peer: {e.reason}")


def run_ping(config):
    """Check whether the peer is reachable."""
    try:
        result = transfer.ping(config)
        print(f"Peer ok: {result}")
    except urllib.error.URLError as e:
        sys.exit(f"Peer unreachable: {e.reason}")


def main():
    if len(sys.argv) < 2:
        sys.exit(USAGE)

    command = sys.argv[1]
    config = load_config()

    if command == "daemon":
        run_daemon(config)
    elif command == "send":
        if len(sys.argv) < 3:
            sys.exit("Usage: python main.py send FILE")
        run_send(config, sys.argv[2])
    elif command == "ping":
        run_ping(config)
    else:
        sys.exit(USAGE)


if __name__ == "__main__":
    main()
