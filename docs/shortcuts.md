# LocalDrop — Shortcuts & Integration Guide

## Where to install the project

Put the project in the same place on both devices:

```
~/projects/localdrop/
```

This path is what the systemd service file and all the scripts below assume.
If you clone it elsewhere, update those paths accordingly.

```bash
# On both Linux and macOS
mkdir -p ~/projects
git clone https://github.com/Manuel0516/localdrop ~/projects/localdrop
cd ~/projects/localdrop
cp examples/config.example.toml config.toml
# edit config.toml for each device
```

---

## Linux / Hyprland integration — send files to the Mac

LocalDrop includes a small Linux helper script:

```bash
~/projects/localdrop/scripts/localdrop-send.sh
```

It opens a file picker and sends the chosen file to the peer. You can trigger it
either with a Hyprland keybind or as a Caelestia launcher action.

### 1. Install zenity (file picker)

```bash
sudo pacman -S zenity
```

### Option A — Hyprland keybind

Add a keybind that runs the helper script.

For a regular Hyprland config, add this to `~/.config/hypr/hyprland.conf`:

```ini
bind = $mainMod SHIFT, D, exec, ~/projects/localdrop/scripts/localdrop-send.sh
```

If you use the Caelestia dotfiles, put custom Hyprland binds in
`~/.config/caelestia/hypr-user.conf` instead:

```ini
bind = $mainMod SHIFT, D, exec, ~/projects/localdrop/scripts/localdrop-send.sh
```

Change the key combo to whatever you prefer (`SUPER SHIFT D` in this example).

Reload Hyprland config:

```
SUPER + SHIFT + R   (default Hyprland reload bind)
```

Now pressing `SUPER + SHIFT + D` opens a file picker. Selecting a file sends it
straight to the Mac.

### Option B — Caelestia launcher action

Caelestia launcher actions live in `~/.config/caelestia/shell.json`.

The file usually contains only your overrides, so you may not see
`launcher.actions` there yet. If you add `launcher.actions`, Caelestia replaces
the default action list with the list you provide. To keep the built-in actions,
copy the default actions and add LocalDrop at the end.

If your `shell.json` is otherwise empty, you can use this full file:

```json
{
  "launcher": {
    "actions": [
      {
        "name": "Calculator",
        "icon": "calculate",
        "description": "Do simple math equations (powered by Qalc)",
        "command": ["autocomplete", "calc"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Scheme",
        "icon": "palette",
        "description": "Change the current colour scheme",
        "command": ["autocomplete", "scheme"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Wallpaper",
        "icon": "image",
        "description": "Change the current wallpaper",
        "command": ["autocomplete", "wallpaper"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Variant",
        "icon": "colors",
        "description": "Change the current scheme variant",
        "command": ["autocomplete", "variant"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Random",
        "icon": "casino",
        "description": "Switch to a random wallpaper",
        "command": ["caelestia", "wallpaper", "-r"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Light",
        "icon": "light_mode",
        "description": "Change the scheme to light mode",
        "command": ["setMode", "light"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Dark",
        "icon": "dark_mode",
        "description": "Change the scheme to dark mode",
        "command": ["setMode", "dark"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Shutdown",
        "icon": "power_settings_new",
        "description": "Shutdown the system",
        "command": ["systemctl", "poweroff"],
        "enabled": true,
        "dangerous": true
      },
      {
        "name": "Reboot",
        "icon": "cached",
        "description": "Reboot the system",
        "command": ["systemctl", "reboot"],
        "enabled": true,
        "dangerous": true
      },
      {
        "name": "Logout",
        "icon": "exit_to_app",
        "description": "Log out of the current session",
        "command": ["loginctl", "terminate-user", ""],
        "enabled": true,
        "dangerous": true
      },
      {
        "name": "Lock",
        "icon": "lock",
        "description": "Lock the current session",
        "command": ["loginctl", "lock-session"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Sleep",
        "icon": "bedtime",
        "description": "Suspend then hibernate",
        "command": ["systemctl", "suspend-then-hibernate"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Settings",
        "icon": "settings",
        "description": "Configure the shell",
        "command": ["caelestia", "shell", "nexus", "open"],
        "enabled": true,
        "dangerous": false
      },
      {
        "name": "Send File",
        "icon": "send",
        "description": "Send a file with LocalDrop",
        "command": ["bash", "-lc", "~/projects/localdrop/scripts/localdrop-send.sh"],
        "enabled": true,
        "dangerous": false
      }
    ]
  }
}
```

If your `shell.json` already has other settings, merge this into the existing
top-level object. If it already has a `"launcher"` block, add only the
`"actions"` key inside that block so your other launcher settings stay intact.

Restart Caelestia after editing:

```bash
qs -c caelestia kill
caelestia shell -d
```

Open the launcher with `SUPER`, then type `>` and search for `Send File`.

---

## macOS shortcut — send files to Linux

Two options: a Finder right-click action (recommended), or a keyboard shortcut.

### Option A — Finder Quick Action (right-click any file)

1. Open **Automator** → **New Document** → choose **Quick Action**.
2. At the top, set:
   - *Workflow receives current* → **Files or Folders**
   - *in* → **Finder**
3. In the search bar, find **Run Shell Script** and drag it into the workflow.
4. Set *Pass input* to **as arguments**.
5. Paste this script:

   ```bash
   cd ~/projects/localdrop
   for f in "$@"; do
       python3 main.py send "$f"
   done
   ```

6. Save as **Send with LocalDrop**.

You can now right-click any file in Finder → **Quick Actions** → **Send with LocalDrop**.

### Option B — Keyboard shortcut (file picker dialog)

1. Make the script executable (already done if cloned fresh):
   ```bash
   chmod +x ~/projects/localdrop/scripts/localdrop-send-mac.sh
   ```

2. Open **Automator** → **New Document** → **Application**.
3. Add a **Run Shell Script** action.
4. Paste:
   ```bash
   ~/projects/localdrop/scripts/localdrop-send-mac.sh
   ```
5. Save the app somewhere, e.g. `~/Applications/LocalDropSend.app`.

6. Open **System Settings** → **Keyboard** → **Keyboard Shortcuts** →
   **App Shortcuts** → click **+**, choose *All Applications*, type the
   menu title you'll never use, and point it to the app. Alternatively, use
   a tool like **Raycast** or **Alfred** to trigger the app by name.

---

## iPhone Shortcuts — send clipboard or files to Linux

> **Note:** This is one-way only. iPhone and Linux can both send **to** Linux,
> but Linux cannot send files or clipboard back **to** the iPhone. That
> direction is not supported in v1.

You need to know your **Linux IP** and **shared_token** from `config.toml`.

---

### Shortcut 1 — Send clipboard to Linux

This sends whatever is in the iPhone clipboard to the Linux machine.

**Steps in the Shortcuts app:**

1. Open **Shortcuts** → tap **+** to create a new shortcut.
2. Tap **Add Action** → search for **Get Clipboard** → add it.
3. Tap **Add Action** → search for **Get Contents of URL** → add it.
4. Configure the URL action:
   - **URL:** `http://192.168.1.110:8765/clipboard`
     *(replace with your Linux IP)*
   - **Method:** POST
   - **Headers:** tap Add Header twice:
     - `X-LocalDrop-Token` → `your-shared-token`
     - `Content-Type` → `application/json`
   - **Request Body:** JSON → tap Add Field twice:
     - `source` → Text → `iphone`
     - `text` → tap the field → choose **Clipboard** (the variable from step 2)
5. Name it **Send Clipboard to Linux** and save.

You can add it to your Home Screen or run it from the Shortcuts widget.

---

### Shortcut 2 — Send a file to Linux (Share Sheet)

This adds a **"Send to Linux"** option to the iOS Share Sheet, so you can send
any file from Files, Photos, or Safari directly to Linux — similar to AirDrop.

**Steps in the Shortcuts app:**

1. Create a new shortcut → tap the **ⓘ** (info) button at the top.
   - Enable **Show in Share Sheet**.
   - Under *Receive* → select **Files**, **Images**, and **Media**.
   - Tap Done.
2. Tap **Add Action** → search for **Get Name** → add it.
   - Set it to get the name of **Shortcut Input**.
3. Tap **Add Action** → search for **Get Contents of URL** → add it.
4. Configure the URL action:
   - **URL:** `http://192.168.1.110:8765/file`
   - **Method:** POST
   - **Headers:** tap Add Header twice:
     - `X-LocalDrop-Token` → `your-shared-token`
     - `X-LocalDrop-Filename` → tap the field → choose **Name** (from step 2)
   - **Request Body:** File → tap the field → choose **Shortcut Input**
5. Name it **Send to Linux** and save.

To use it: share any file → tap **Send to Linux** in the Share Sheet.
The file is saved to `~/Downloads/LocalDrop/` on Linux and triggers a
desktop notification.

---

### Shortcut 3 — Send clipboard to Linux (quick access from Lock Screen / Action Button)

This is the same as Shortcut 1 but optimised for the quickest access:

- Add it to the **Lock Screen widget** or assign it to the **Action Button**
  (iPhone 15 Pro+) in Settings → Action Button → Shortcut.
- This lets you copy something on iPhone, press the Action Button, and it lands
  on the Linux clipboard instantly.

---

## Summary of what is and isn't supported

| Direction              | Clipboard | File transfer |
| ---------------------- | --------- | ------------- |
| Linux → Mac            | ✅        | ✅            |
| Mac → Linux            | ✅        | ✅            |
| iPhone → Linux         | ✅        | ✅ (Share Sheet shortcut) |
| iPhone → Mac           | ✅        | ✅ (Share Sheet shortcut) |
| Linux → iPhone         | ❌        | ❌ (not supported in v1) |
| Mac → iPhone           | ❌        | ❌ (not supported in v1) |
