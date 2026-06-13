"""Optional desktop notifications.

Linux uses ``notify-send``; macOS uses ``osascript``. Notifications are best
effort: if the tool is missing or fails, we just stay quiet.
"""

import subprocess


def notify(config, title, message):
    """Show a desktop notification if enabled in config."""
    if not config.get("notifications", {}).get("enabled", False):
        return

    platform = config["device"]["platform"]
    try:
        if platform == "linux":
            subprocess.run(["notify-send", title, message], check=False)
        elif platform == "macos":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=False)
    except FileNotFoundError:
        # Notification tool not installed -- not worth crashing over.
        pass
