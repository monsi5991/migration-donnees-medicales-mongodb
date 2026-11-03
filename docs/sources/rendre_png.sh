#!/bin/bash
# render.sh <dossier_svg> : convertit chaque .svg en .png (x2) avec Chrome headless
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for f in "$1"/*.svg; do
  w=$(grep -o 'width="[0-9]*"' "$f" | head -1 | grep -o '[0-9]*')
  h=$(grep -o 'height="[0-9]*"' "$f" | head -1 | grep -o '[0-9]*')
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size=$w,$h --screenshot="${f%.svg}.png" "file://$f" >/dev/null 2>&1
  echo "$(basename "${f%.svg}.png") ${w}x${h}"
done
