#!/bin/bash
# build.sh — run this ONCE. Produces Jarvis.dmg: a double-click installer
# with the standard "drag to Applications" experience.
#
# Usage:
#   chmod +x build.sh
#   ./build.sh
#
# After this, Jarvis.dmg is the only thing you (or anyone else with a Mac)
# ever needs to download and open again.

set -e

echo "==> Setting up build environment"
python3 -m venv venv
source venv/bin/activate
pip install --quiet -r requirements.txt

echo "==> Building Jarvis.app"
rm -rf build dist
pyinstaller --windowed --onefile --name Jarvis \
  --osx-bundle-identifier com.local.jarvis \
  app.py

echo "==> Packaging Jarvis.dmg"
STAGING=dmg-staging
rm -rf "$STAGING" Jarvis.dmg
mkdir "$STAGING"
cp -R "dist/Jarvis.app" "$STAGING/"
ln -s /Applications "$STAGING/Applications"

hdiutil create -volname "Jarvis" -srcfolder "$STAGING" -ov -format UDZO Jarvis.dmg

rm -rf "$STAGING"

echo ""
echo "==> Done: Jarvis.dmg is ready in this folder."
echo "    Double-click it, drag Jarvis into Applications, eject, done."
echo ""
echo "    First launch only: macOS will warn 'Apple could not verify this"
echo "    app is free of malware' since it isn't Apple-notarized (that"
echo "    requires a paid \$99/yr developer account). To open it anyway:"
echo "    right-click Jarvis.app -> Open -> Open. Only needed once."
