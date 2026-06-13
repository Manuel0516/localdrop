"""Clipboard reading/writing and the change-watcher loop.

Linux (Wayland) uses ``wl-paste`` / ``wl-copy``; macOS uses ``pbpaste`` / ``pbcopy``.

Loop protection (see guidelines section 11): we remember the last value we sent
out (``last_local``) and the last value we received from the peer
(``last_remote``). When we receive a remote value we record it, so the watcher
recognises it and does not bounce it straight back to the peer.
"""

import subprocess
import threading
import time

# Shared loop-protection state. Touched by both the watcher thread and the HTTP
# handler thread, so guard it with a lock.
_lock = threading.Lock()
last_local = ""
last_remote = ""


def read_command(args):
    """Run a command and return its stdout as text."""
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout


def write_command(args, text):
    """Feed ``text`` to a command on stdin and wait for it to finish.

    stdout/stderr go to /dev/null on purpose: wl-copy daemonizes itself to keep
    serving the selection, and if we captured its output the lingering child
    would hold the pipe open and make subprocess.run() block forever.
    """
    try:
        subprocess.run(
            args,
            input=text,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except FileNotFoundError as e:
        raise RuntimeError(f"clipboard command not found: {args[0]}") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"clipboard command failed: {args[0]} exited with {e.returncode}"
        ) from e


def read_clipboard(config):
    """Return the current local clipboard text."""
    platform = config["device"]["platform"]
    if platform == "linux":
        # -n: don't add a trailing newline of our own.
        return read_command(["wl-paste", "-n"])
    if platform == "macos":
        return read_command(["pbpaste"])
    raise RuntimeError(f"Unsupported platform: {platform}")


def write_clipboard(config, text):
    """Set the local clipboard to ``text``."""
    platform = config["device"]["platform"]
    if platform == "linux":
        write_command(["wl-copy"], text)
    elif platform == "macos":
        write_command(["pbcopy"], text)
    else:
        raise RuntimeError(f"Unsupported platform: {platform}")


def set_remote(text):
    """Record clipboard text that just arrived from the peer (loop guard)."""
    global last_remote
    with _lock:
        last_remote = text


def watch_clipboard(config):
    """Poll the local clipboard and send genuine changes to the peer."""
    # Imported here to avoid a circular import (transfer imports this module).
    from transfer import send_clipboard

    global last_local, last_remote
    interval = config.get("clipboard", {}).get("poll_interval", 0.7)

    while True:
        time.sleep(interval)
        current = read_clipboard(config)
        if not current:
            continue

        with _lock:
            # If this is exactly what the peer just sent us, don't echo it back.
            if current == last_remote:
                last_local = current
                continue
            # Unchanged since the last thing we sent -> nothing to do.
            if current == last_local:
                continue
            last_local = current

        # New local clipboard content -> push it to the peer (outside the lock).
        try:
            send_clipboard(config, current)
        except Exception as e:
            # Peer offline / network hiccup: log and retry on the next change.
            print(f"[clipboard] could not send to peer: {e}")
