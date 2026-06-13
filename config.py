"""Load and validate the LocalDrop configuration.

Everything is controlled from a single ``config.toml`` next to this file.
"""

import os
import sys
import tomllib

# The config lives in the same directory as the program.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")

# Sections (and the keys inside them) that must exist for the program to run.
REQUIRED = {
    "device": ["name", "platform"],
    "server": ["host", "port"],
    "peer": ["name", "host", "port"],
    "security": ["shared_token"],
}


def load_config():
    """Read config.toml, expand paths, and check required fields.

    Exits with a clear message instead of a traceback on common mistakes.
    """
    if not os.path.exists(CONFIG_PATH):
        sys.exit(
            f"Config not found: {CONFIG_PATH}\n"
            "Copy config.example.toml to config.toml and edit it."
        )

    with open(CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)

    # Validate required sections/keys up front so failures are easy to read.
    for section, keys in REQUIRED.items():
        if section not in config:
            sys.exit(f"Config error: missing [{section}] section.")
        for key in keys:
            if key not in config[section]:
                sys.exit(f"Config error: missing '{key}' in [{section}].")

    platform = config["device"]["platform"]
    if platform not in ("linux", "macos"):
        sys.exit(f"Config error: device.platform must be 'linux' or 'macos', got '{platform}'.")

    # Expand ~ in the download directory so the rest of the code can ignore it.
    download_dir = config.get("files", {}).get("download_dir", "~/Downloads/LocalDrop")
    config.setdefault("files", {})["download_dir"] = os.path.expanduser(download_dir)

    return config
