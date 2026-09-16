#!/bin/sh
# Download the official Raspberry Pi Ltd camera mechanical drawings into tmp/rpi.
#
# Beside the Raspberry Pi board drawings, because they come from the same
# company and the same redirect: datasheets.raspberrypi.com 301s to
# pip-assets.raspberrypi.com with a zero-length body, so -L is required or
# every file comes down empty.
#
# All PDF.  There is no DXF and no STEP for the Camera Module 2; Raspberry Pi
# publish a STEP model for the Camera Module 3 only, and it is not used here --
# both Camera Module 3 drawings are true 1:1 vector plots and give more than
# the assembly does.
#
# The High Quality Camera's own drawing is fetched as well.  It has no sheet
# yet: see raspberry_pi_camera/README.md for what it gives and what it does
# not.  There is no official drawing at all for the OV5647 Camera Module 1.
set -eu
cd "$(dirname "$0")/.."
mkdir -p tmp/rpi
for u in \
  https://datasheets.raspberrypi.com/camera/camera-module-2-mechanical-drawing.pdf \
  https://datasheets.raspberrypi.com/camera/camera-module-3-standard-mechanical-drawing.pdf \
  https://datasheets.raspberrypi.com/camera/camera-module-3-wide-mechanical-drawing.pdf \
  https://pip.raspberrypi.com/documents/RP-008200-DS ; do
  case "$u" in
    *RP-008200-DS) f=tmp/rpi/hq-camera-cs-mechanical-drawing.pdf ;;
    *) f=tmp/rpi/$(basename "$u") ;;
  esac
  curl -sSL -o "$f" "$u"
  printf '%-52s %8s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"
done
