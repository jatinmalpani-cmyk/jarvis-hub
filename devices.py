"""
devices.py — your device registry. Edit this file to match your own setup.
No keys live here — just names that map to local control paths.
"""

# ---------------------------------------------------------------------------
# MATTER devices (paired into Apple Home, controlled via Shortcuts CLI)
#
# For each device, create a Shortcut in the Shortcuts app named exactly
# "<Shortcut Name> On" and "<Shortcut Name> Off" (or just one for
# non-on/off devices — see README for dimmers/thermostats). Each Shortcut
# should contain a single "Control Home" / "Set State of Accessory" action
# targeting that Matter accessory. That's it — the hub just runs it by name.
#
# key: how you'll refer to the device by voice, e.g. "living room light"
# value: the exact Shortcut name prefix you gave it (no "On"/"Off" suffix)
# ---------------------------------------------------------------------------

MATTER_DEVICES = {
    "living room light": "Living Room Light",
    "office light": "Office Light",
    "kitchen light": "Kitchen Light",
    "front door lock": "Front Door Lock",
    # add more: "voice name": "Exact Shortcut Name Prefix",
}

# ---------------------------------------------------------------------------
# Z-WAVE devices (controlled via a local Zwave-JS-UI REST API)
# Requires: a Z-Wave USB stick + Zwave-JS-UI running locally (see README).
#
# key: voice name
# value: the Zwave-JS-UI node ID (find it in the Zwave-JS-UI web UI at
#         http://localhost:8091 — click the device, the node ID is shown
#         in its header)
# ---------------------------------------------------------------------------

ZWAVE_DEVICES = {
    "garage light": 5,
    "bedroom fan": 8,
    # add more: "voice name": node_id,
}

ZWAVE_JS_UI_URL = "http://localhost:8091"
