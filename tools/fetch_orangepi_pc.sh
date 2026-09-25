#!/bin/sh
# Fetch what the Orange Pi PC is measured from, and checked against, into
# tmp/src/orangepi_pc.
#
# Xunlong publish no mechanical drawing for this board -- SCRATCH.md has the
# search -- so the sheet is measured from photographs, and every photograph
# and every third-party model used is fetched here, at the URL and capture
# it was measured from:
#
#   photos/  linux-sunxi's top and bottom views of two boards, a v1.3 and a
#            v1.2, and Xunlong's product page views of a third, a v1.2.
#            linux-sunxi.org answers anything scripted with a Cloudflare
#            block, so theirs come from the Wayback Machine at the capture
#            pinned below; "id_" asks for the file as captured rather than
#            wrapped in the archive's page.  linux-sunxi's v1.2 pair is not
#            measured -- raspberry_pi/measure_orangepi_pc.py says why -- and
#            is fetched so that the reason can be seen.
#   models/  Printables uploads: models of the board itself, and cases.  Printables hands out a download
#            link per file from its GraphQL API, with no login.  Thingiverse,
#            where most Orange Pi PC cases live, puts every download behind a
#            Cloudflare challenge and is not used.
#
# The manual, schematic and H3 datasheet cached beside these came from the
# Google Drive links on Xunlong's service and support page and are not
# refetched here: Drive has no stable direct URL for them.
set -eu
cd "$(dirname "$0")/.."
d=tmp/src/orangepi_pc
mkdir -p "$d/photos" "$d/models"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

get() {  # get <file> <url>
  test -s "$1" || curl -sSL -A "$UA" -o "$1" "$2"
  printf '%-58s %9s bytes\n' "${1#$d/}" "$(wc -c < "$1")"
}

wb=https://web.archive.org/web
sx=https://linux-sunxi.org/images
get "$d/photos/sunxi-v1p3-top.jpg"    "$wb/20260121220613id_/$sx/6/6e/Orange_Pi_PC_v1.3_front.jpg"
get "$d/photos/sunxi-v1p3-bottom.jpg" "$wb/20260121220614id_/$sx/a/a4/Orange_Pi_PC_v1.3_back.jpg"
get "$d/photos/sunxi-v1p2-top.png"    "$wb/20260122092412id_/$sx/f/ff/Xunlong_Orange_Pi_PC_top.PNG"
get "$d/photos/sunxi-v1p2-bottom.png" "$wb/20260122092413id_/$sx/d/da/Xunlong_Orange_Pi_PC_bottom.PNG"
op=http://www.orangepi.org/img/computersAndMmicrocontrollers
get "$d/photos/xunlong-top.png"       "$op/PC40.png"
get "$d/photos/xunlong-bottom.png"    "$op/PC/Rectangle%20641.png"

# printables <model id> <file id> <file>
printables() {
  test -s "$d/models/$3" && { printf '%-58s %9s bytes\n' "models/$3" "$(wc -c < "$d/models/$3")"; return; }
  q='{"query":"mutation D($id: ID!, $p: ID!){ getDownloadLink(id: $id, printId: $p, fileType: stl, source: model_detail){ output{ link } } }","variables":{"id":"'$2'","p":"'$1'"}}'
  link=$(curl -sS -H 'content-type: application/json' -d "$q" \
         https://api.printables.com/graphql/ | sed -n 's/.*"link":"\([^"]*\)".*/\1/p')
  test -n "$link" || { echo "no download link for printables $1 file $2" >&2; exit 1; }
  get "$d/models/$3" "$link"
}
printables 1792599 7480821 landroo-opipc.scad
printables 1792599 7480825 landroo-opipc.stl
printables 1531394 6444582 gachin-pipc.3mf
printables 573200  2428982 lowich-opi-bottom.stl
printables 995302  4166107 maghirang-snapfit-bot.stl
printables 445456  1938875 mexus-bottom.stl
printables 981303  4112955 aristotelov-v2-bot.stl
printables 291652  1311070 n7cat-base-rev2.stl
printables 44992   183998  stanley-bottom-30x30.stl
printables 183980  777165  jargov-base.stl

# Xunlong's own assembly drawing for the Orange Pi PC Plus: not this board,
# its sibling, which a forum answer says is the same size.  Used only as a
# cross-check, never as a source.  A RAR of two AutoCAD 2000 DWGs, from the
# old download host by way of the Wayback Machine.
get "$d/models/xunlong-pc-plus-v1p1-drawing.rar" \
    "$wb/20220325055237id_/http://www.orangepi.org/download/ORANGE_PI-PC-PLUS_V1_1_mechanical_drawing.rar"
