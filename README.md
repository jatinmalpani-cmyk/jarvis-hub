# Jarvis Hub — one app, Mac + iPhone

No browser automation of Claude/ChatGPT/Gemini's websites (violates their
terms, gets accounts banned) — instead:

- **Ollama** — free, local LLM, the default brain, no key.
- **Gemini / ChatGPT** — official APIs, used only when you explicitly say
  "ask gemini…" / "ask chatgpt…". One key each, entered once in the app's
  Setup menu, stored only on your Mac.
- **AppleScript** — Apple's built-in automation for Mail.app/Calendar.app,
  using accounts already signed into those apps.
- **Shortcuts** — Apple's native automation, talks to Siri, no jailbreak.
- **Matter** (via Apple Home) and **Z-Wave** (via Zwave-JS-UI) for smart home.

You build it into one double-clickable app **once**, then never touch a
terminal again.

## 1. Install Ollama and pull a model (one-time, in Terminal)

```bash
brew install ollama
ollama serve &
ollama pull llama3.1        # or llama3.2:3b if your Mac is older/slower
```

## 2. Build Jarvis.dmg — two ways

### Option A: cloud build (no Terminal at all)

GitHub gives away free Mac build machines. This lets the actual `.app`
compiling happen on a real Mac in the cloud, so you never touch Terminal:

1. Make a free account at github.com (if you don't have one).
2. Click **New repository** → name it `jarvis-hub` → **Create repository**.
3. On the repo page, click **uploading an existing file**, drag in every
   file and folder from the unzipped `jarvis-hub` folder (including the
   hidden `.github` folder — if your browser file picker hides it, unzip
   with the Archive Utility and check "Show hidden files" in Finder with
   Cmd+Shift+. to select it), then **Commit changes**.
4. Click the **Actions** tab at the top of the repo. A workflow called
   "Build Jarvis.dmg" runs automatically — takes about 2-3 minutes.
5. When it finishes (green checkmark), click into that run, scroll to
   **Artifacts**, and click **Jarvis-dmg** to download it. Unzip that —
   `Jarvis.dmg` is the real installer, built on an actual Mac.

From here it's a normal download: open the dmg, drag Jarvis into
Applications, right-click → Open the first time (Gatekeeper, since it
isn't Apple-notarized), then it's a normal app forever.

### Option B: build it yourself locally (needs Terminal once)

```bash
cd jarvis-hub
chmod +x build.sh
./build.sh
```

Same result as Option A, just done on your own Mac instead of a cloud one.

## 3. Open Jarvis and add your API keys

Double-click **Jarvis.app**. A 🤖 icon appears in your menu bar. Click it:

- **Set Gemini API Key** → paste a key from aistudio.google.com (free tier)
- **Set ChatGPT API Key** → paste a key from platform.openai.com (paid,
  but a few cents per request)
- **Show My Local Address** → gives you the exact URL for step 5 below

Skip either key if you only want one provider, or neither if you're happy
with local Ollama only — it always works with no key at all.

## 4. Keep it running automatically

System Settings → General → Login Items → add **Jarvis** under "Open at
Login." Now it's always running in the background after every restart —
no launching required.

## 5. Find your Mac's local address

Click the menu bar icon → **Show My Local Address**. It'll look like
`http://192.168.1.x:8787/ask`. Your iPhone needs to be on the **same
Wi-Fi network** to reach it (or use Tailscale, also free, for away-from-home).

## 6. Siri Shortcut on iPhone (push-to-talk style)

Open the **Shortcuts** app on iPhone → New Shortcut → add these actions in order:

1. **Dictate Text** (this is your "hold a key and talk" step)
2. **Get Contents of URL**
   - URL: `http://<your-mac-ip>:8787/ask`
   - Method: `POST`
   - Headers: `Content-Type: application/json`
   - Request Body (JSON): `{"text": "Dictated Text"}` — insert the Dictate
     Text output as the value
3. **Get Dictionary Value** → key `reply` (pulls the reply text out of the JSON)
4. **Speak Text** → the dictionary value from step 3

Name the shortcut "Jarvis." Then in Shortcut Details, tap **Add to Home
Screen** or, better, assign it to the **Action Button** (iPhone 15 Pro/16)
or a **Back Tap** gesture (Settings → Accessibility → Touch → Back Tap) —
that's your push-to-talk trigger, held or tapped instead of a key.

You can also just say **"Hey Siri, Jarvis"** once it's set up — Siri will
run the shortcut by name.

## 7. Same Shortcut on Mac

The Shortcuts app on macOS uses the same four actions. Then:
System Settings → Keyboard → Keyboard Shortcuts → App Shortcuts → add one
that runs your "Jarvis" shortcut, bound to whatever key combo you want as
your push-to-talk key on the Mac itself.

## 8. Matter devices (via Apple Home)

1. Pair your Matter devices in the **Home** app on your iPhone/Mac as normal
   (uses your Apple ID — free, local, no extra account).
2. For each device, open **Shortcuts** and make two tiny shortcuts:
   - `"<Device Name> On"` → one action: **Control Home / Set State of
     Accessory** → pick that accessory → On
   - `"<Device Name> Off"` → same, but Off
   e.g. for a living room light: `"Living Room Light On"` and
   `"Living Room Light Off"`.
3. Open `devices.py` and add the device to `MATTER_DEVICES`:
   ```python
   MATTER_DEVICES = {
       "living room light": "Living Room Light",
   }
   ```
   (the key is what you'll say, the value must match your Shortcut name
   exactly, minus " On"/" Off".)
4. Restart Jarvis (menu bar icon → Quit Jarvis, then relaunch). Now "turn
   on the living room light" works end to end: Siri → hub →
   `shortcuts run "Living Room Light On"` → Apple Home → Matter.

## 9. Z-Wave devices (via Zwave-JS-UI)

**Hardware required:** a Z-Wave USB stick (e.g. Zooz ZST10, Aeotec Z-Stick
Gen5+). There's no software-only way to reach Z-Wave radios — Z-Wave isn't
IP-based like Matter.

1. Plug the stick into your Mac.
2. Install and run **Zwave-JS-UI** (free, open source):
   ```bash
   docker run -d --name zwave-js-ui -p 8091:8091 -p 3000:3000 \
     --device=/dev/tty.usbmodem<yours> \
     -v ~/.zwave-js-ui:/usr/src/app/store \
     zwavejs/zwave-js-ui:latest
   ```
   (find your stick's device path with `ls /dev/tty.*` while it's plugged in)
3. Open `http://localhost:8091` in a browser, run through the pairing
   wizard, and include your Z-Wave devices.
4. Click each device to find its **node ID**, then add it to `devices.py`:
   ```python
   ZWAVE_DEVICES = {
       "garage light": 5,
   }
   ```
5. If you turned on authentication in Zwave-JS-UI's settings, put that key
   (self-generated, local only) into `ZWAVE_API_KEY` in `home_control.py`.
6. Restart Jarvis. "Turn off the garage light" now routes straight to
   Zwave-JS-UI's local API — no Matter/Shortcuts involved for this one.

Both device types share one voice pattern: **"turn on/off the &lt;device
name&gt;"** — the hub checks Matter devices first, then Z-Wave, so names
just need to be unique across `devices.py`.

## 10. Asking Gemini or ChatGPT specifically

Once you've added a key (step 3), just say what you want:

- "Ask Gemini to summarize the plot of Dune"
- "ChatGPT, write a haiku about traffic"

Anything without "gemini" or "chatgpt"/"gpt" at the start stays on local
Ollama by default — so your everyday requests never leave your Mac unless
you explicitly ask for a cloud model.

## 11. Extending it

`server.py`'s `route()` function is where you add more local skills — it
currently handles "email" and "calendar" keywords via AppleScript. Add
more `if re.search(...)` branches for reminders, notes, Messages, etc.
(all scriptable locally via AppleScript, no keys needed).
