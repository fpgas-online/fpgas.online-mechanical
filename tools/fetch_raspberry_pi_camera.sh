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
# Each is a Wayback Machine capture pinned to one date, so a quote checked
# today is checked against the same bytes tomorrow -- except the Scribd page
# image, of which the Wayback Machine has no capture.  That one is live, and
# measure_cm1.py refuses it by its SHA-256 if Scribd ever serves another.
#
# Two of these come down gzipped whatever the request asks for -- the Scribd
# text layer, and the Wayback Machine's copy of the documentation -- so
# anything that arrives as a gzip stream is unpacked where it lands.
mkdir -p tmp/rpi/cm1
WB=https://web.archive.org/web
while read -r f u; do
  curl -sSL -o "tmp/rpi/cm1/$f" "$u"
done <<URLS
scribd-page1-original.jpg https://imgv2-2-f.scribdassets.com/img/document/142718448/original/a5bde6fe7d/1
scribd-page1.jsonp $WB/20230728040627id_/https://html.scribdassets.com/6btrecuy0w2fcmuv/pages/1-385ca7c8dd.jsonp
forum-t44466.html $WB/20140401233736id_/http://www.raspberrypi.org/phpBB3/viewtopic.php?f=43&t=44466
rpispy-diagram.pdf $WB/20201026183139id_/https://www.raspberrypi-spy.co.uk/wp-content/uploads/2013/05/Raspberry-Pi-Camera-Module-Diagram.pdf
rpispy-article.html $WB/20201026175350id_/https://www.raspberrypi-spy.co.uk/2013/05/pi-camera-module-mechanical-dimensions/
rpispy-photo.jpg $WB/20201026175332id_/https://www.raspberrypi-spy.co.uk/wp-content/uploads/2013/05/pi_camera_module_14.jpg
uctronics-B0033.pdf $WB/20201026093909id_/https://www.uctronics.com/download/Amazon/B0033.pdf
camera.html $WB/20260919113406id_/https://www.raspberrypi.com/documentation/accessories/camera.html
URLS
for f in tmp/rpi/cm1/*; do
  case "$(head -c 2 "$f" | od -An -tx1)" in
    *1f*8b*) mv "$f" "$f.gz" && gunzip -f "$f.gz" ;;
  esac
  printf '%-52s %8s bytes\n' "cm1/$(basename "$f")" "$(wc -c < "$f")"
done

# The optical figures for the camera position sheets, the RPICAM-OVER-*,
# which no mechanical drawing carries: field of view, focal length, sensor
# size and focus range.
#
# Raspberry Pi Ltd's own camera documentation is the source for the OV5647
# Camera Module 1 figures, and it is fetched from the Internet Archive: a
# direct request to raspberrypi.com is answered 403 from here, and a pinned
# snapshot is what makes the quotes on the sheets reproducible anyway.
#
# Arducam's OV5647 documentation is the source for the wide and the autofocus
# variants, which Raspberry Pi never made: their product catalogue table names
# a horizontal and a vertical field of view and a focus type per SKU, which is
# the only place either is written down by the company that sells the part.
mkdir -p tmp/src/rpi-camera-optics
fetch_optics() {
  curl -sSL -A "Mozilla/5.0 (X11; Linux x86_64) mechanical-drawings/1.0" \
       -o "tmp/src/rpi-camera-optics/$2" "$1"
  printf '%-52s %8s bytes\n' "$2" "$(wc -c < "tmp/src/rpi-camera-optics/$2")"
}
fetch_optics \
  'https://web.archive.org/web/20241230011811/https://www.raspberrypi.com/documentation/accessories/camera.html' \
  raspberry-pi-camera-documentation.html
fetch_optics \
  'https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/5MP-OV5647/' \
  arducam-5mp-ov5647.html
fetch_optics \
  'https://docs.arducam.com/Raspberry-Pi-Camera/Motorized-Focus-Camera/Motorized-Focus-Camera/' \
  arducam-motorized-focus-camera.html
fetch_optics \
  'https://docs.arducam.com/Raspberry-Pi-Camera/Motorized-Focus-Camera/Quick-Start-Guide/OV5647-Motorized-Focus-Camera/' \
  arducam-ov5647-motorized-focus-camera.html

# The lens options and their focus, one page per claim the sheets make about
# them.  Every page that the Internet Archive holds is fetched from a pinned
# capture: arducam.com and uctronics.com answer a plain request with a
# Cloudflare challenge, and a capture is what keeps a quote checkable after
# the vendor edits the page.  The one page it does not hold, YXF's M6 lens,
# is fetched live.
#
# OmniVision's own OV5647 datasheet, for the image area and the active array
# the lenses are measured against.
fetch_optics \
  'https://web.archive.org/web/20260723044623/https://cdn.sparkfun.com/datasheets/Dev/RaspberryPi/ov5647_full.pdf' \
  ov5647-datasheet.pdf
# Arducam's 120 degree module, the B006604: its product page gives the angle
# as a DIAGONAL, which the catalogue table above does not.
fetch_optics \
  'https://web.archive.org/web/20250530094438/https://www.arducam.com/b006604-arducam-for-raspberry-pi-zero-camera-module-wide-angle-120-1-4-inch-5mp-ov5647-spy-camera-with-flex-cable-for-pi-zero-and-pi-compute-module.html' \
  arducam-b006604.html
# The motorised-focus OV5647: the B0121, discontinued, whose page names the
# B0176 as its successor, and the B0176 on UCTRONICS, Arducam's own store.
fetch_optics \
  'https://web.archive.org/web/20241103134041/https://www.arducam.com/product/5mp-ov5647-motorized-focus-camera-sensor-raspberry-pi/' \
  arducam-b0121-motorized-focus.html
fetch_optics \
  'https://web.archive.org/web/20251209063424/https://www.uctronics.com/arducam-auto-focus-camera-module-5mp-for-raspberry-pi.html' \
  uctronics-arducam-b0176.html
# Two lens makers' figures for real ~120 degree lenses on this sensor, with
# the distortion in: Commonlands work each lens's field of view out on the
# OV5647's active area from their own distortion data, and YXF publish a
# datasheet row for an M6 lens made for OV5647 modules.
fetch_optics \
  'https://web.archive.org/web/20260817210431/https://commonlands.com/pages/image-sensors/ov5647' \
  commonlands-ov5647.html
fetch_optics \
  'https://www.yxfcamera.com/products/Lenses/m6-lens-5mp-ov5647-raspberry-pi-camera-lens.html' \
  yxf-m6-lens.html
# Waveshare's RPi Camera (G), the Camera Module v1 sized fisheye, and The Pi
# Hut's listing of it, which is where its horizontal figure is printed.
fetch_optics \
  'https://web.archive.org/web/20191211152844/https://www.waveshare.com/RPi-Camera-G.htm' \
  waveshare-rpi-camera-g.html
fetch_optics \
  'https://web.archive.org/web/20190224065515/https://www.waveshare.com/wiki/RPi_Camera_(G)' \
  waveshare-rpi-camera-g-wiki.html
fetch_optics \
  'https://web.archive.org/web/20250810012231/https://thepihut.com/products/raspberry-pi-camera-board-fisheye-160-lens-5mp' \
  pihut-fisheye-160.html
