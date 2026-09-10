#!/bin/sh
# Download the official Raspberry Pi Ltd mechanical drawings into tmp/rpi.
#
# datasheets.raspberrypi.com now 301-redirects to pip.raspberrypi.com with a
# zero-length body, so -L is required or every file comes down empty.
#
# DXF is available for the Pi 3B, 3B+ and 4B only; the Pi 3A+ and Pi 5 are PDF.
set -eu
cd "$(dirname "$0")/.."
mkdir -p tmp/rpi
base=https://datasheets.raspberrypi.com
for u in \
  rpi3/raspberry-pi-3-b-mechanical-drawing.pdf \
  rpi3/raspberry-pi-3-b-mechanical-drawing.dxf \
  rpi3/raspberry-pi-3-b-plus-mechanical-drawing.pdf \
  rpi3/raspberry-pi-3-b-plus-mechanical-drawing.dxf \
  rpi3/raspberry-pi-3-a-plus-mechanical-drawing.pdf \
  rpi4/raspberry-pi-4-mechanical-drawing.pdf \
  rpi4/raspberry-pi-4-mechanical-drawing.dxf \
  rpi5/raspberry-pi-5-mechanical-drawing.pdf ; do
  f=tmp/rpi/$(basename "$u")
  curl -sSL -o "$f" "$base/$u"
  printf '%-52s %8s bytes\n' "$(basename "$u")" "$(wc -c < "$f")"
done
