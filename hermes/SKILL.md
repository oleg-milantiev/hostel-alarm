---
name: beeware-briefcase
description: "Use when building Android APKs with BeeWare Briefcase, or when developing Toga apps."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [beeware, briefcase, toga, android, apk, build, toga-app]
    category: software-development
---

# BeeWare Briefcase — Android APK builds and Toga app development

Use when building Android APKs with BeeWare/Briefcase, when the user mentions BeeWare, Toga, or briefcase, or when developing a Toga GUI app for Android.

## Procedure

### 1. Install briefcase
```
python -m pip install briefcase
```
(In the Hermes venv: `C:/Users/mo/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe -m pip install briefcase`)

### 2. Create project (non-interactive)
```
cd /path/to/parent
cd /c/Users/mo && briefcase new --no-input \
  -Q gui_framework=Toga \
  -Q app_name=MyApp \
  -Q formal_name="My App" \
  -Q bundle_org=com.example \
  -Q project_url=https://example.com \
  -Q author_email=dev@example.com
```
Then `cd MyApp`.

### 3. Add dependencies to pyproject.toml
- **Python dependencies**: add to the top-level `requires` list:
  ```toml
  requires = [
      "toga-android",
  ]
  ```
- **Resource files** (audio, images, etc.): add a `resource-files` key:
  ```toml
  resource-files = [
      "src/MyApp/alarm.wav",
  ]
  ```
  > **WARNING**: `resource-files` does NOT reliably bundle files into the APK on Chaquopy builds. Files listed here may not appear in `assets/` inside the APK. Verify with `unzip -l <apk> | grep <filename>`. If the file is missing, it was not bundled. For audio, generate programmatically (see Pitfalls below).

### 4. Write the Toga app (app.py)
- Inherit from `toga.App`.
- **Layout**: use `toga.Box` with `style=Pack(direction=COLUMN)` or `direction=ROW`.
- **Widgets**: `toga.Button`, `toga.Label` — avoid `Slider` and `NumberInput` on Android (may crash).
- **Network calls**: use `urllib.request` (pure Python). **Never use `requests`** — it has C-extensions that fail on Android via Chaquopy.
- **Async background work**: use `self.loop.call_later()` or `self.loop.create_task()` — never block the main thread.
- **UI updates from async**: call widget updates directly inside the async task; Toga handles thread dispatch.
- **MUST define `main()` at module level** — `__main__.py` does `from MyApp.app import main`. Every app.py must end with:
  ```python
  def main():
      return MyApp()
  ```
- **Import alignment constants explicitly**: `from toga.style.pack import COLUMN, ROW, CENTER` — `CENTER` is not available by default.

Example structure:
```python
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER

class MyApp(toga.App):
    def startup(self):
        main_box = toga.Box(
            children=[
                toga.Label("Hello", style=Pack(font_size=20)),
                toga.Button("Click", on_press=self.on_click),
            ],
            style=Pack(direction=COLUMN, alignment=CENTER, padding=20),
        )
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    def on_click(self, widget):
        pass

def main():
    return MyApp()
```

### 5. Build APK
```
yes | briefcase build android --debug
```
The `yes |` auto-accepts SDK license prompts.

### 6. APK output
`build/<AppName>/android/gradle/app/build/outputs/apk/debug/app-debug.apk`

### 7. Install on device
```bash
adb install -r <path-to-apk>
```
If adb doesn't see the device: check USB cable (must support data, not charge-only), ensure "Allow USB debugging" was tapped on the phone, and switch USB mode from "Charge" to "File Transfer" in the notification shade.

## Pitfalls

- **`main()` function is REQUIRED in app.py** — `__main__.py` does `from MyApp.app import main`. Missing it causes `ImportError: cannot import name 'main'` and the app crashes on launch. Always add `def main(): return MyApp()` at the bottom of app.py.
- **`requests` does NOT work on Android** — Chaquopy cannot load C-extensions. Use `urllib.request` (pure Python) for all HTTP calls.
- **`resource-files` in pyproject.toml does NOT reliably bundle files into the APK** — Files listed here may not appear in `assets/` inside the APK. Verify with `unzip -l <apk> | grep <filename>`. If the file is missing, it was not bundled. For audio, generate programmatically instead.
- **Audio on Android via Chaquopy** — `toga.Audio` with `self.resources` does not work. `android.content.res.AssetManager` also fails because resources are not in the APK assets. **Solution**: use Chaquopy's `java.jclass()` to access Android Java classes directly from Python. **ToneGenerator** is the simplest approach — no WAV file needed, no PCM samples. Example:
```python
from java import jclass
ToneGenerator = jclass("android.media.ToneGenerator")
AudioManager = jclass("android.media.AudioManager")
tone = ToneGenerator(AudioManager.STREAM_ALARM, 100)
tone.startTone(ToneGenerator.TONE_PROP_BEEP, 1000)  # 1s beep
tone.stopTone()
tone.release()
```
For siren: alternate between two tones in a loop using `threading.Timer`. `ToneGenerator.TONE_PROP_BEEP` and `ToneGenerator.TONE_CDMA_ALERT_CALL_GUARD` produce different tones — alternate them for siren effect. Duration: each `startTone(tone_type, duration_ms)` call. To stop: `tone.stopTone()` then `tone.release()`. **Never use `jnius`** — Chaquopy provides `java.jclass()` natively, jnius is not supported. **Important**: create ToneGenerator once and reuse it; do not create a new instance per alarm. Store as `self._tone` and check `if self._tone is None` before creating.
- **`Slider` and `NumberInput` may crash on Android** — use `+`/`-` buttons with a `Label` instead.
- **Don't block the main thread** — Toga runs on the UI thread. Use `self.loop.create_task()` or `self.loop.call_later()` for network calls, file I/O, or polling.
- **UI updates from `threading.Timer` background threads** — `threading.Timer` runs in a separate Python thread, NOT the event loop. Toga does NOT auto-dispatch UI updates from these threads. You MUST use `self.loop.call_later(0, callback, *args)` to marshal updates to the main thread. Calling widget properties directly from `threading.Timer` causes `CalledFromWrongThreadException` or silent crashes. This is different from `self.loop.create_task()` which runs in the event loop and can update widgets directly.
- **Never use `self.app.invoke()`** — Toga has no `invoke` method on app instances. The correct pattern is `self.loop.call_later(0, callback, *args)`.
- **JAVA_HOME must be Java 17** — Briefcase rejects Java 19+ and will download its own JDK 17. Set `JAVA_HOME` to a Java 17 path or let Briefcase handle it.
- **ANDROID_HOME must contain `cmdline-tools/`** — Briefcase checks for `$ANDROID_HOME/cmdline-tools/19.0/bin/sdkmanager.bat` (Windows) or `sdkmanager` (Unix). If the structure doesn't match, Briefcase downloads its own SDK instance.
- **SDK licenses block builds** — The Android SDK requires accepting 8 licenses before any package install. Always pipe `yes |` to the build command, or accept them interactively first.
- **On Windows, sdkmanager is a `.bat` file** — Don't call it as a bare Unix command; use the `.bat` extension or let Briefcase manage it.
- **Briefcase may ignore existing SDK** — If the cmdline-tools directory structure doesn't match the expected layout (e.g., `cmdline-tools/latest/` vs `cmdline-tools/19.0/`), Briefcase falls back to downloading its own. This is safe but slower.
- **USB debugging on Windows** — If `adb devices` shows nothing: (1) cable may be charge-only — try a different one; (2) phone must show "Allow USB debugging" prompt — tap Allow; (3) notification shade USB mode must be "File Transfer", not "Charge"; (4) Windows may need ADB drivers installed.
- **Version bump required for APK updates** — When updating an APK, change the `version` in pyproject.toml (e.g., `0.0.1` → `0.0.2`). Without a version bump, `adb install -r` may install a cached/stale APK.

## Testing on Android Emulator

When the physical device is unavailable or for automated testing, use the Android emulator.

### 1. Create AVD (one-time)
```bash
# List available system images
ls $ANDROID_HOME/system-images/

# Create AVD from a system image
$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager.bat create avd \
  -n HostelAlarm \
  -k "system-images;android-33;google_apis;x86_64" \
  --device "Nexus 6" \
  -f
```

### 2. Start emulator (headless)
```bash
# Start without GUI window (for automated testing)
$ANDROID_HOME/emulator/emulator.exe -avd HostelAlarm \
  -no-snapshot \
  -no-window \
  -no-audio \
  -gpu swiftshader_indirect
```

Wait for boot:
```bash
$ANDROID_HOME/platform-tools/adb.exe wait-for-device
# Poll until boot complete
$ANDROID_HOME/platform-tools/adb.exe shell getprop sys.boot_completed
# Returns "1" when ready
```

### 3. Network access from emulator
- Host machine is `10.0.2.2` from inside the emulator
- For services on other LAN machines, set up a TCP proxy on the host:
  ```python
  # proxy.py — simple TCP forwarder
  import socket, threading
  def forward(src, dst):
      while True:
          data = src.recv(4096)
          if not data: break
          dst.sendall(data)
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  server.bind(("0.0.0.0", 8888))
  server.listen(5)
  while True:
      client, _ = server.accept()
      remote = socket.create_connection(("192.168.2.198", 88))
      threading.Thread(target=forward, args=(client, remote), daemon=True).start()
      threading.Thread(target=forward, args=(remote, client), daemon=True).start()
  ```
  Then forward emulator port to host:
  ```bash
  adb -s emulator-5554 forward tcp:88 tcp:8888
  ```
  App URL becomes `http://10.0.2.2:88/...`

### 4. Build, install, launch
```bash
# Build
briefcase build android --debug

# Install
adb -s emulator-5554 install -r build/HostelAlarm/android/gradle/app/build/outputs/apk/debug/app-debug.apk

# Launch
adb -s emulator-5554 shell am start -n com.example.HostelAlarm/org.beeware.android.MainActivity
```

### 5. Interact with UI
```bash
# Screenshot
adb -s emulator-5554 exec-out screencap -p > screenshot.png

# Tap coordinates (find via UI hierarchy dump)
adb -s emulator-5554 shell input tap 718 637

# Dump UI hierarchy to find element bounds
adb -s emulator-5554 shell uiautomator dump /sdcard/ui.xml
adb -s emulator-5554 pull /sdcard/ui.xml ./ui.xml
# Parse XML for clickable elements and their bounds
```

### 6. Read logs
```bash
# Filter by app tag
adb -s emulator-5554 logcat -d -s HostelAlarm

# All Python output
adb -s emulator-5554 logcat -d | grep -i "HostelAlarm\|python\|chaquopy"
```

### 7. Automated test workflow
```
1. Build APK → briefcase build android --debug
2. Install → adb -s emulator-5554 install -r <apk>
3. Launch → adb -s emulator-5554 shell am start -n com.example.HostelAlarm/org.beeware.android.MainActivity
4. Wait → sleep 2
5. Screenshot → screencap -p > screenshot.png
6. Analyze UI → parse ui.xml for element bounds
7. Tap → input tap <x> <y>
8. Wait → sleep <interval>
9. Screenshot → verify state changed
10. Logs → logcat -d -s HostelAlarm
11. Iterate → fix issues, rebuild, reinstall
```

### 10. Stop emulator
```bash
adb -s emulator-5554 emu kill
```

### 11. Mock server for testing (no real API needed)
When the real API is unavailable or you need deterministic tests, run a mock server on the host:

```python
# mock_zabbix.py — always returns stars_count_0 = 40
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"stars_count_0": 40}).encode())
    def log_message(self, format, *args): pass  # suppress logs

server = HTTPServer(("0.0.0.0", 9999), MockHandler)
server.serve_forever()
```

Start on host: `python mock_zabbix.py`
App URL: `http://10.0.2.2:9999/REST/zabbix/?key=mock`

### 12. UI update pattern that works on Android
**Direct UI updates from `threading.Timer` DO work on Toga/Android** — Toga auto-dispatches widget property changes. Do NOT use `self.loop.call_later()` or `self.app.invoke()` from background threads (both fail silently).

```python
# WRONG — these don't work from threading.Timer:
self.loop.call_later(0, self._update_ui, stars, tick)
self.app.invoke(self._update_ui, stars, tick)

# CORRECT — direct assignment works:
self.stars_label.text = f"Stars Count: {stars}"
self.tick_label.text = f"Ticks: {tick}"
self.status_label.text = f"Polling every 5s... (tick {tick})"
```

### 13. AlarmManager must be initialized in __init__
```python
def __init__(self):
    super().__init__()
    self._alarm_manager = AlarmManager()  # MUST initialize before use
```

## References

- BeeWare docs: https://docs.beeWare.org/
- Briefcase templates: https://github.com/beeware/briefcase-template
- Android Gradle template: https://github.com/beeware/briefcase-android-gradle-template
- Toga widget reference: https://docs.beeware.org/en/latest/api/toga/widgets.html
