"""
app.py — the menu bar wrapper. This is what turns the hub into "one app":
double-click it (or launch the built .app), it sits in your menu bar,
runs the server in the background, and gives you a Setup window for API
keys — no terminal involved after the one-time build step in README.md.
"""

import threading

import rumps
import uvicorn

from server import app as fastapi_app, HUB_PORT
from llm_providers import save_config_value, load_config


def _run_server():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=HUB_PORT, log_level="warning")


class JarvisMenuBarApp(rumps.App):
    def __init__(self):
        super().__init__("🤖 Jarvis", quit_button="Quit Jarvis")
        self.menu = [
            "Status: starting…",
            None,
            "Set Gemini API Key",
            "Set ChatGPT API Key",
            None,
            "Show My Local Address",
        ]
        self._server_thread = threading.Thread(target=_run_server, daemon=True)
        self._server_thread.start()
        self.menu["Status: starting…"].title = "Status: running ✅"

    @rumps.clicked("Set Gemini API Key")
    def set_gemini_key(self, _):
        cfg = load_config()
        current = cfg.get("gemini_api_key", "")
        resp = rumps.Window(
            title="Gemini API Key",
            message="Paste your key from aistudio.google.com — stored only in "
                    "~/.jarvis-hub/config.json on this Mac.",
            default_text=current,
            ok="Save", cancel="Cancel",
        ).run()
        if resp.clicked and resp.text.strip():
            save_config_value("gemini_api_key", resp.text.strip())
            rumps.notification("Jarvis", "", "Gemini key saved.")

    @rumps.clicked("Set ChatGPT API Key")
    def set_chatgpt_key(self, _):
        cfg = load_config()
        current = cfg.get("openai_api_key", "")
        resp = rumps.Window(
            title="ChatGPT API Key",
            message="Paste your OpenAI API key — stored only in "
                    "~/.jarvis-hub/config.json on this Mac.",
            default_text=current,
            ok="Save", cancel="Cancel",
        ).run()
        if resp.clicked and resp.text.strip():
            save_config_value("openai_api_key", resp.text.strip())
            rumps.notification("Jarvis", "", "ChatGPT key saved.")

    @rumps.clicked("Show My Local Address")
    def show_address(self, _):
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            ip = "unknown — check Wi-Fi settings"
        rumps.alert(
            title="Jarvis address",
            message=f"http://{ip}:{HUB_PORT}/ask\n\nUse this in your Shortcut's "
                     f"'Get Contents of URL' action.",
        )


if __name__ == "__main__":
    JarvisMenuBarApp().run()
