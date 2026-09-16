"""
home_control.py — Matter + Z-Wave control, both fully local.

Matter: devices are paired in Apple Home (your Apple ID, free, local) and
controlled by running a Shortcut whose name matches the device. No keys.

Z-Wave: devices are controlled through Zwave-JS-UI's local REST API. If you
set an API key in Zwave-JS-UI's own settings, that key lives only on your
Mac and is never sent anywhere external — it's not a cloud/vendor key.
"""

import subprocess
from typing import Optional

import requests

from devices import MATTER_DEVICES, ZWAVE_DEVICES, ZWAVE_JS_UI_URL

ZWAVE_API_KEY: Optional[str] = None  # set this if you enabled auth in Zwave-JS-UI settings


# ---------------------------------------------------------------------------
# Matter (via Apple Home + Shortcuts)
# ---------------------------------------------------------------------------

def run_shortcut(name: str) -> bool:
    try:
        result = subprocess.run(
            ["shortcuts", "run", name],
            capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0
    except Exception:
        return False


def control_matter(device_key: str, action: str) -> str:
    """action: 'on' or 'off'"""
    shortcut_prefix = MATTER_DEVICES.get(device_key)
    if not shortcut_prefix:
        return f"I don't have a Matter device registered as '{device_key}'."
    shortcut_name = f"{shortcut_prefix} {'On' if action == 'on' else 'Off'}"
    ok = run_shortcut(shortcut_name)
    if ok:
        return f"Turned {action} the {device_key}."
    return f"Couldn't run the '{shortcut_name}' shortcut — check it exists in Shortcuts."


# ---------------------------------------------------------------------------
# Z-Wave (via Zwave-JS-UI local REST API)
# ---------------------------------------------------------------------------

def _zwave_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if ZWAVE_API_KEY:
        headers["Authorization"] = f"Bearer {ZWAVE_API_KEY}"
    return headers


def control_zwave(device_key: str, action: str) -> str:
    """action: 'on' or 'off'. Adjust the payload shape below to match your
    Zwave-JS-UI version's API — check http://localhost:8091/api/docs for
    the exact schema; this targets the common Binary Switch command class."""
    node_id = ZWAVE_DEVICES.get(device_key)
    if node_id is None:
        return f"I don't have a Z-Wave device registered as '{device_key}'."

    payload = {
        "nodeId": node_id,
        "commandClass": 37,       # COMMAND_CLASS_SWITCH_BINARY
        "endpoint": 0,
        "property": "targetValue",
        "value": action == "on",
    }
    try:
        resp = requests.post(
            f"{ZWAVE_JS_UI_URL}/api/setValue",
            json=payload, headers=_zwave_headers(), timeout=10
        )
        if resp.status_code == 200:
            return f"Turned {action} the {device_key}."
        return f"Zwave-JS-UI returned an error ({resp.status_code}) controlling {device_key}."
    except Exception as e:
        return f"Couldn't reach Zwave-JS-UI: {e}"


# ---------------------------------------------------------------------------
# Unified lookup — tries Matter first, then Z-Wave
# ---------------------------------------------------------------------------

def control_device(device_key: str, action: str) -> str:
    if device_key in MATTER_DEVICES:
        return control_matter(device_key, action)
    if device_key in ZWAVE_DEVICES:
        return control_zwave(device_key, action)
    return f"I don't recognize '{device_key}' as a registered device."


def all_device_names():
    return list(MATTER_DEVICES.keys()) + list(ZWAVE_DEVICES.keys())
