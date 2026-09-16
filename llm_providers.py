"""
llm_providers.py — talks to local Ollama, and optionally Gemini / ChatGPT
via their OFFICIAL APIs (the only supported way to reach them
programmatically — see README for why we don't scrape the web chat UIs).

API keys are stored in a local JSON file on your Mac
(~/.jarvis-hub/config.json) and are only ever sent to Google's / OpenAI's
own API endpoints — nothing else reads this file.
"""

import json
import os
from pathlib import Path
from typing import Optional

import requests

CONFIG_DIR = Path.home() / ".jarvis-hub"
CONFIG_PATH = CONFIG_DIR / "config.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

GEMINI_MODEL = "gemini-2.0-flash"   # check aistudio.google.com for current model names
OPENAI_MODEL = "gpt-4o-mini"        # cheap + fast; change if you prefer another

SYSTEM_PROMPT = (
    "You are Jarvis, a concise local voice assistant. Answer briefly and "
    "clearly, in a form that sounds good read aloud by Siri. Avoid "
    "markdown, bullet points, or long lists — speak in plain sentences."
)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text())
    except Exception:
        return {}


def save_config_value(key: str, value: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    cfg[key] = value
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def _build_prompt(user_text: str, context: Optional[str]) -> str:
    prompt = SYSTEM_PROMPT
    if context:
        prompt += f"\n\nRelevant local data:\n{context}"
    prompt += f"\n\nUser: {user_text}"
    return prompt


# ---------------------------------------------------------------------------
# Ollama (local, always available, no key)
# ---------------------------------------------------------------------------

def ask_ollama(user_text: str, context: Optional[str] = None) -> str:
    prompt = _build_prompt(user_text, context) + "\nJarvis:"
    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip() or "No response from the local model."


# ---------------------------------------------------------------------------
# Gemini (official API — free tier available at aistudio.google.com)
# ---------------------------------------------------------------------------

def ask_gemini(user_text: str, context: Optional[str] = None) -> str:
    cfg = load_config()
    key = cfg.get("gemini_api_key")
    if not key:
        return "Gemini isn't set up yet — add your API key from the Setup menu."

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={key}"
    )
    prompt = _build_prompt(user_text, context)
    try:
        resp = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Gemini request failed: {e}"


# ---------------------------------------------------------------------------
# ChatGPT (official OpenAI API — no free tier, but very cheap per request)
# ---------------------------------------------------------------------------

def ask_chatgpt(user_text: str, context: Optional[str] = None) -> str:
    cfg = load_config()
    key = cfg.get("openai_api_key")
    if not key:
        return "ChatGPT isn't set up yet — add your API key from the Setup menu."

    prompt = _build_prompt(user_text, context)
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ChatGPT request failed: {e}"
