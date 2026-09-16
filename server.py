"""
Jarvis Hub — a fully local voice/text assistant hub for Mac + iPhone.

No scraping of web chat UIs (against those services' terms and gets
accounts banned). Instead:
- Ollama (localhost) for local, free, no-key reasoning — the default.
- Gemini / ChatGPT via their OFFICIAL APIs when you explicitly ask for
  them ("ask gemini...", "ask chatgpt..."), using a key you add once from
  the app's Setup menu. Keys live only in ~/.jarvis-hub/config.json.
- Mail.app / Calendar.app via AppleScript, using accounts already signed
  into those apps.
- Matter (via Apple Home + Shortcuts) and Z-Wave (via Zwave-JS-UI) for
  smart home control.

Exposes one HTTP endpoint that Siri Shortcuts (iPhone + Mac) call.
"""

import re
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import subprocess

from home_control import control_device, all_device_names
from llm_providers import ask_ollama, ask_gemini, ask_chatgpt

HUB_PORT = 8787

app = FastAPI(title="Jarvis Hub")


class AskRequest(BaseModel):
    text: str


class AskResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# AppleScript helpers (local automation, no keys/APIs — uses your logged-in
# Mail.app and Calendar.app accounts directly)
# ---------------------------------------------------------------------------

def run_applescript(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return f"(AppleScript error: {result.stderr.strip()})"
        return result.stdout.strip()
    except Exception as e:
        return f"(AppleScript failed: {e})"


def get_unread_email(limit: int = 5) -> str:
    script = f'''
    tell application "Mail"
        set theResults to {{}}
        set unreadMsgs to messages of inbox whose read status is false
        set n to 0
        repeat with m in unreadMsgs
            if n >= {limit} then exit repeat
            set end of theResults to (sender of m & " — " & subject of m)
            set n to n + 1
        end repeat
        return theResults as string
    end tell
    '''
    out = run_applescript(script)
    return out if out else "No unread email."


def get_todays_events() -> str:
    script = '''
    tell application "Calendar"
        set todayStart to current date
        set time of todayStart to 0
        set todayEnd to todayStart + 1 * days
        set theResults to {}
        repeat with c in calendars
            set theEvents to (every event of c whose start date is greater than or equal to todayStart and start date is less than todayEnd)
            repeat with e in theEvents
                set end of theResults to (summary of e & " at " & (time string of (start date of e)))
            end repeat
        end repeat
        return theResults as string
    end tell
    '''
    out = run_applescript(script)
    return out if out else "No events today."


def create_calendar_event(title: str, when_natural: str) -> str:
    # Minimal, naive version — expand as needed. `when_natural` should already
    # be resolved to something AppleScript's date parser can handle, e.g.
    # "9/17/2026 3:00 PM".
    script = f'''
    tell application "Calendar"
        tell calendar 1
            make new event with properties {{summary:"{title}", start date:date "{when_natural}", end date:(date "{when_natural}") + 1 * hours}}
        end tell
    end tell
    return "created"
    '''
    return run_applescript(script)


# ---------------------------------------------------------------------------
# Device control routing (Matter + Z-Wave) — handled directly, no LLM
# round-trip needed, since it's a deterministic action not a question.
# ---------------------------------------------------------------------------

def try_device_control(text: str) -> Optional[str]:
    t = text.lower().strip()
    m = re.search(r"\b(turn|switch)\s+(on|off)\s+(?:the\s+)?(.+)", t)
    if not m:
        return None
    action = m.group(2)
    device_phrase = m.group(3).strip()

    # match against known device names (exact, then substring)
    for name in all_device_names():
        if name == device_phrase or name in device_phrase or device_phrase in name:
            return control_device(name, action)
    return f"I don't have a device called '{device_phrase}' registered yet."


# ---------------------------------------------------------------------------
# Intent routing (dead simple keyword rules — swap for something smarter
# later if you want, but this keeps everything local and dependency-free)
# ---------------------------------------------------------------------------

def route(text: str) -> Optional[str]:
    """Returns extra context to hand to the LLM, if this looks like an
    email/calendar request. Returns None for general questions."""
    t = text.lower()
    if re.search(r"\b(email|inbox|unread)\b", t):
        return f"Unread email:\n{get_unread_email()}"
    if re.search(r"\b(calendar|schedule|events? today|what.?s on today)\b", t):
        return f"Today's calendar:\n{get_todays_events()}"
    return None


# ---------------------------------------------------------------------------
# Provider selection — "ask gemini ..." / "ask chatgpt ..." routes to that
# provider's official API; anything else stays local on Ollama (default).
# ---------------------------------------------------------------------------

def choose_provider(text: str):
    t = text.strip()
    m = re.match(r"(?i)^\s*(?:ask|use)?\s*(gemini)\b[,:]?\s*(.*)", t)
    if m and m.group(2):
        return ask_gemini, m.group(2).strip()
    m = re.match(r"(?i)^\s*(?:ask|use)?\s*(chatgpt|gpt)\b[,:]?\s*(.*)", t)
    if m and m.group(2):
        return ask_chatgpt, m.group(2).strip()
    return ask_ollama, text


# ---------------------------------------------------------------------------
# Ollama call
# ---------------------------------------------------------------------------

# (moved to llm_providers.py)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    # Device control commands are handled directly and skip the LLM.
    device_reply = try_device_control(req.text)
    if device_reply is not None:
        return AskResponse(reply=device_reply)

    provider_fn, clean_text = choose_provider(req.text)
    context = route(clean_text)
    reply = provider_fn(clean_text, context)
    return AskResponse(reply=reply)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=HUB_PORT)
