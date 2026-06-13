#!/usr/bin/env bash
# Open a file picker and send the chosen file to the peer via LocalDrop.
# Designed to be bound to a Hyprland keybinding.
#
# Requires zenity:  sudo pacman -S zenity

LOCALDROP_DIR="$HOME/projects/localdrop"

FILE=$(zenity --file-selection --title="Send with LocalDrop" 2>/dev/null) || exit 0
[ -z "$FILE" ] && exit 0

cd "$LOCALDROP_DIR"
python main.py send "$FILE"
