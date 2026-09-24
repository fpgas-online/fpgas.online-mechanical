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
# The High Quality Camera's own drawing is fetched as well, and beside it the
# CS/M12 mount document, which is where the 1/4-20 UNC on the tripod boss is
# written down -- the drawing itself never names the thread.  Neither has a
# sheet yet: see raspberry_pi_camera/README.md for what they give and what
# they do not.  There is no official drawing at all for the OV5647 Camera
# Module 1; what there is instead is fetched at the end.
set -eu
cd "$(dirname "$0")/.."
mkdir -p tmp/rpi
for u in \
  https://datasheets.raspberrypi.com/camera/camera-module-2-mechanical-drawing.pdf \
  https://datasheets.raspberrypi.com/camera/camera-module-3-standard-mechanical-drawing.pdf \
  https://datasheets.raspberrypi.com/camera/camera-module-3-wide-mechanical-drawing.pdf \
  https://pip.raspberrypi.com/documents/RP-008200-DS \
  https://pip.raspberrypi.com/documents/RP-008201-DS ; do
  case "$u" in
    *RP-008200-DS) f=tmp/rpi/hq-camera-cs-mechanical-drawing.pdf ;;
    *RP-008201-DS) f=tmp/rpi/hq-camera-m12-mechanical-drawing.pdf ;;
    *) f=tmp/rpi/$(basename "$u") ;;
  esac
  curl -sSL -o "$f" "$u"
  printf '%-52s %8s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"
done

# The Camera Module v1.3, the OV5647 board, has no Raspberry Pi drawing, so
# raspberry_pi_camera/v1.py is written by hand from what there is instead;
# raspberry_pi_camera/README.md says what each of these gives.  They are
# cached so that raspberry_pi_camera/verify.py can hold every figure v1.py
# quotes against the page it was quoted from.
#
#   scribd-page1-original.jpg  Gert van Loo's hand-measured sheet of
#                              21 May 2013, the page image Scribd serves
#   scribd-page1.jsonp         the same page's text layer, where its
#                              printed figures can be read as text
#   forum-t44466.html          the forum thread he posted it in
#   rpispy-diagram.pdf         Raspberry Pi Spy's caliper-measured diagram
#   rpispy-article.html        and the article it came with
#   rpispy-photo.jpg           the article's photograph of the board
#   uctronics-B0033.pdf        Arducam's drawing of their B0033, a clone
#   camera.html                Raspberry Pi's camera documentation
#
# Where a live page could change or vanish, a Wayback Machine capture is
# fetched instead, pinned to one date.  Two of these come down gzipped
# whatever the request asks for -- the Scribd text layer, and the Wayback
# Machine's copy of the documentation -- so anything that arrives as a gzip
# stream is unpacked where it lands.
mkdir -p tmp/rpi/cm1
WB=https://web.archive.org/web
while read -r f u; do
  curl -sSL -o "tmp/rpi/cm1/$f" "$u"
done <<URLS
scribd-page1-original.jpg https://imgv2-2-f.scribdassets.com/img/document/142718448/original/a5bde6fe7d/1
scribd-page1.jsonp https://html.scribdassets.com/6btrecuy0w2fcmuv/pages/1-385ca7c8dd.jsonp
forum-t44466.html $WB/20140401233736id_/http://www.raspberrypi.org/phpBB3/viewtopic.php?f=43&t=44466
rpispy-diagram.pdf https://www.raspberrypi-spy.co.uk/wp-content/uploads/2013/05/Raspberry-Pi-Camera-Module-Diagram.pdf
rpispy-article.html https://www.raspberrypi-spy.co.uk/2013/05/pi-camera-module-mechanical-dimensions/
rpispy-photo.jpg https://www.raspberrypi-spy.co.uk/wp-content/uploads/2013/05/pi_camera_module_14.jpg
uctronics-B0033.pdf $WB/20201026093909id_/https://www.uctronics.com/download/Amazon/B0033.pdf
camera.html $WB/20260919113406id_/https://www.raspberrypi.com/documentation/accessories/camera.html
URLS
for f in tmp/rpi/cm1/*; do
  case "$(head -c 2 "$f" | od -An -tx1)" in
    *1f*8b*) mv "$f" "$f.gz" && gunzip -f "$f.gz" ;;
  esac
  printf '%-52s %8s bytes\n' "cm1/$(basename "$f")" "$(wc -c < "$f")"
done
