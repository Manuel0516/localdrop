#!/usr/bin/env bash
# Open a file picker and send the chosen file to the peer via LocalDrop.
# Assign this to a keyboard shortcut via Automator (see docs/shortcuts.md).

LOCALDROP_DIR="$HOME/projects/localdrop"

FILE=$(osascript -e 'POSIX path of (choose file with prompt "Send with LocalDrop:")' 2>/dev/null) || exit 0
[ -z "$FILE" ] && exit 0

cd "$LOCALDROP_DIR"
python3 main.py send "$FILE"
