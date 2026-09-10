#!/usr/bin/env python3
"""Design the Tiny Tapeout generic mounting plate and write its data module.

The plate carries one hole pattern that accepts *any* Tiny Tapeout demo board
revision on standoffs, while holding the Pmod host headers in a single fixed
place.  That is possible because of one invariant: every revision from TT01
through v3.3 spaces its Pmod hosts 22.86 mm apart, the pitch the Digilent Pmod
Interface Specification mandates for host ports on a board edge.

The design frame has its origin at the pin-field centre of the leftmost Pmod
host position, X along the board's front edge and Y into the board.  Each board
revision is then placed by the offset that puts its Pmod hosts on that grid,
and its mounting holes fall wherever they fall.

Holes that land close together are dealt with by separation:

* under 1.0 mm apart, they become one hole at the midpoint; the residual error
  is small compared with an M3 clearance hole;
* between 1.0 mm and the minimum drillable spacing, they become one obround
  slot spanning both positions;
* beyond that, they stay as separate holes.

Run: uv run --no-project python scripts/design_mounting_plate.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.tinytapeout_boards import BOARDS  # noqa: E402

PMOD_PITCH = 22.86
M3_DIA = 3.00              # nominal M3 shank
HOLE_DIA = 3.40            # close clearance for M3
SLOT_WIDTH = 3.40
MIN_WEB = 1.50             # least material left between two holes

#: Two positions may share one hole only if the hole's own clearance swallows
#: the offset.  A 3.40 mm hole gives an M3 shank 0.20 mm of radial play, so the
#: two positions may be at most 0.40 mm apart; drilled at their midpoint each
#: is then 0.20 mm off centre, exactly using up the play.  A larger threshold
#: produces a plate whose holes the fasteners do not actually fit: at 1.00 mm
#: it merged two positions 0.613 mm apart and left the screw 0.107 mm short.
MERGE_BELOW = HOLE_DIA - M3_DIA
PLATE_HOLE_DIA = 4.30      # M4 clearance, for fixing the plate down
PLATE_HOLE_CLEAR = 6.0     # keep plate fixings this far from any board hole

#: Each entry is one mechanically distinct board revision, in shuttle order,
#: with the shuttles it covers.  Revisions with identical geometry share a row.
#: Group name, the revision whose geometry is used, every revision the group
#: covers, and the shuttles those revisions shipped on.  A group's revisions
#: share their mounting holes and Pmod host positions exactly, which is all the
#: plate cares about; they may still differ elsewhere.  v2.1.2, for instance,
#: moved its USB-C connector 0.9 mm relative to v2.0.1 and v2.1.0.
REVISIONS = [
    ("TT01-03", "tt123-v2.2.6", ("tt123-v2.2.6",), ("TT01", "TT02", "TT03")),
    ("TT04-05", "v1.2.2", ("v1.2.2", "v1.2.3"), ("TT04", "TT05")),
    ("TT06-08", "v2.0.1", ("v2.0.1", "v2.1.0", "v2.1.2"),
     ("TT06", "TT07", "TT08")),
    ("v3.2", "v3.2", ("v3.2",), ()),
    ("v3.3", "v3.3", ("v3.3",), ()),
]

#: The TT01/02/03 board has only two Pmod hosts.  Putting its first host on the
#: middle of the three plate positions rather than the left makes the plate
#: 5.15 mm narrower, because that board is the widest and sits furthest right.
TWO_PMOD_START_SLOT = 1

def pmod_body_box() -> tuple[float, float, float, float]:
    """The Pmod connector body, relative to its pin-field centre.

    Read from the board data and checked to be identical on every revision,
    rather than written down here: every revision uses the same footprint, and
    that is the fact the whole plate rests on.  Returned as
    (dx0, dx1, dy0, dy1) in millimetres from the pin-field centre.
    """
    boxes = set()
    for board in BOARDS.values():
        for p in board.pmods:
            if p.body_x1 <= p.body_x0:
                continue
            boxes.add((round(p.body_x0 - p.cx, 3), round(p.body_x1 - p.cx, 3),
                       round(p.body_y0 - p.cy, 3), round(p.body_y1 - p.cy, 3)))
    if len(boxes) != 1:
        raise SystemExit(
            "the Pmod connector body is not the same on every revision: "
            f"{sorted(boxes)}. The plate's front edge is placed from it, so "
            "the design assumption no longer holds")
    return boxes.pop()


#: Distance from a Pmod host's pin-field centre to the front face of its
#: connector body.  A reliable datum for where the plate's front edge can go.
PMOD_BODY = pmod_body_box()
PMOD_BODY_OVERHANG = -PMOD_BODY[2]

#: How far the connector bodies should overhang the plate's front edge, so a
#: peripheral module plugs into clear air.
FRONT_CLEARANCE = 2.78

#: The plate is sized to leave a clear border outside every board footprint on
#: three sides, wide enough to take the plate's own M4 fixings.  The front edge
#: cannot be pushed out that way: it is pinned by the Pmod connector overhang,
#: so there is no fixing along the front.
PLATE_WIDTH = 135.0
PLATE_HEIGHT = 101.0
PLATE_CORNER_R = 4.0
#: Centres the board footprints across the plate: they span 113.515 mm, leaving
#: 10.745 mm each side.
DATUM_X = 38.75
DATUM_Y = PMOD_BODY_OVERHANG - FRONT_CLEARANCE      # 9.0


def placements() -> list[dict]:
    out = []
    for name, key, revisions, shuttles in REVISIONS:
        board = BOARDS[key]
        pmods = sorted(board.pmods, key=lambda p: p.cx)
        slot = TWO_PMOD_START_SLOT if len(pmods) == 2 else 0
        ox = slot * PMOD_PITCH - pmods[0].cx
        oy = -pmods[0].cy
        # Every revision in the group must really share the geometry the plate
        # registers against, or the group is a lie.
        for other in revisions:
            ob = BOARDS[other]
            same_holes = sorted((h.x, h.y, h.dia) for h in ob.holes) == \
                sorted((h.x, h.y, h.dia) for h in board.holes)
            same_pmods = sorted((p.cx, p.cy) for p in ob.pmods) == \
                sorted((p.cx, p.cy) for p in board.pmods)
            if not (same_holes and same_pmods):
                raise SystemExit(
                    f"{name}: revision {other} does not share {key}'s mounting "
                    f"holes and Pmod positions; it needs its own group.")
        out.append(dict(name=name, key=key, revisions=revisions,
                        shuttles=shuttles, board=board,
                        ox=ox, oy=oy, first_slot=slot, pmods=len(pmods)))
    return out


def cluster(points: list[dict], threshold: float) -> list[list[dict]]:
    """Single-link clustering of hole positions."""
    groups: list[list[dict]] = []
    for p in points:
        joined = [g for g in groups
                  if any(math.dist((p["x"], p["y"]), (q["x"], q["y"])) < threshold
                         for q in g)]
        if not joined:
            groups.append([p])
            continue
        merged = [p]
        for g in joined:
            merged += g
            groups.remove(g)
        groups.append(merged)
    return groups


def build():
    place = placements()
    points = []
    for pl in place:
        for h in pl["board"].holes:
            points.append(dict(rev=pl["name"], label=h.label,
                               x=pl["ox"] + h.x, y=pl["oy"] + h.y, dia=h.dia))

    min_sep = HOLE_DIA + MIN_WEB
    groups = cluster(points, min_sep)

    holes, slots = [], []
    for g in sorted(groups, key=lambda g: (round(g[0]["x"], 1), g[0]["y"])):
        # The merge and slot rules below only make sense for a pair.  Three
        # revisions landing in one cluster needs a human decision, not an
        # averaged centroid or a slot through the two outermost of them.
        if len(g) > 2:
            raise SystemExit(
                "three or more revisions want a fastener within "
                f"{min_sep:.2f} mm here: "
                + ", ".join(f"{p['rev']} {p['label']}" for p in g)
                + ". Decide by hand how to serve them.")
        used = sorted({(p["rev"], p["label"]) for p in g})
        span = max((math.dist((a["x"], a["y"]), (b["x"], b["y"]))
                    for a in g for b in g), default=0.0)
        if span < MERGE_BELOW:
            holes.append(dict(x=sum(p["x"] for p in g) / len(g),
                              y=sum(p["y"] for p in g) / len(g),
                              dia=HOLE_DIA, used=used, spread=span))
        else:
            # Longest pair in the group defines the slot axis.
            a, b = max(((a, b) for a in g for b in g),
                       key=lambda ab: math.dist((ab[0]["x"], ab[0]["y"]),
                                                (ab[1]["x"], ab[1]["y"])))
            slots.append(dict(x0=a["x"], y0=a["y"], x1=b["x"], y1=b["y"],
                              width=SLOT_WIDTH, used=used, spread=span))

    # Numbered in board-version order, not left to right.  A user of the plate
    # arrives knowing which revision they have and wants that revision's four
    # holes; numbering them spatially scattered each revision's set across the
    # whole range, so H1, H3, H9 and H10 was one board's pattern.  A hole two
    # revisions share is numbered with the earlier of them.
    order = {pl["name"]: i for i, pl in enumerate(place)}

    def by_version(entry, xkey="x", ykey="y"):
        return (min(order[rev] for rev, _ in entry["used"]),
                round(entry[xkey], 1), round(entry[ykey], 1))

    holes.sort(key=by_version)
    slots.sort(key=lambda e: by_version(e, "x0", "y0"))
    return place, holes, slots


def usb_c_positions(place) -> dict:
    """Where each revision's USB-C connector lands in plate coordinates.

    A chassis has to open for it, and it moves further between revisions than
    anything else on these boards: TT01-03 puts it on the front edge beside
    the Pmod hosts, every later revision puts it at the back.
    """
    out = {}
    for pl in place:
        for f in pl["board"].features:
            if f.kind != "usb_power":
                continue
            # ox/oy are design-frame offsets, whose origin is the leftmost
            # Pmod pin-field centre; the datum shift puts them in plate
            # coordinates, which is what every other number in this module is.
            out[pl["name"]] = (round(pl["ox"] + f.x0 + DATUM_X, 3),
                               round(pl["oy"] + f.y0 + DATUM_Y, 3),
                               round(pl["ox"] + f.x1 + DATUM_X, 3),
                               round(pl["oy"] + f.y1 + DATUM_Y, 3))
    missing = [pl["name"] for pl in place if pl["name"] not in out]
    if missing:
        raise SystemExit(
            f"no USB-C feature found for {', '.join(missing)}; the plate "
            "marks that connector for every revision it serves")
    return out


def check_fasteners(place, holes, slots) -> None:
    """Every board's fastener must actually fit the feature meant to serve it.

    Merging two positions into one hole and slotting two that are further apart
    are both fine, but only if what comes out still passes an M3 shank at each
    board's own hole position.  This is the check the merge threshold exists to
    satisfy, so it is worth making rather than assuming.
    """
    worst = None
    for pl in place:
        for h in pl["board"].holes:
            x, y = pl["ox"] + h.x + DATUM_X, pl["oy"] + h.y + DATUM_Y
            best = -math.inf
            for hole in holes:
                best = max(best, (hole["dia"] - M3_DIA) / 2
                           - math.dist((x, y), (hole["x"] + DATUM_X,
                                                hole["y"] + DATUM_Y)))
            for s in slots:
                best = max(best, (s["width"] - M3_DIA) / 2
                           - _point_seg((x, y),
                                        (s["x0"] + DATUM_X, s["y0"] + DATUM_Y),
                                        (s["x1"] + DATUM_X, s["y1"] + DATUM_Y)))
            if worst is None or best < worst[0]:
                worst = (best, pl["name"], h.label)
            if best < 0:
                raise SystemExit(
                    f"{pl['name']} {h.label} at ({x:.3f},{y:.3f}) has no "
                    f"feature an M3 fastener fits: clearance {best:+.3f} mm. "
                    f"Lower MERGE_BELOW or widen the feature.")
    print(f"tightest M3 clearance {worst[0]:+.3f} mm, at "
          f"{worst[1]} {worst[2]}")


def plate_fixings(place, holes, slots):
    """M4 fixings for the plate itself, in the border outside every board.

    They cannot go along the front edge: that edge is pinned by the Pmod
    connector overhang and the border there is only a few millimetres.
    """
    bx0 = min(pl["ox"] for pl in place) + DATUM_X
    bx1 = max(pl["ox"] + pl["board"].outline.width for pl in place) + DATUM_X
    by1 = max(pl["oy"] + pl["board"].outline.height for pl in place) + DATUM_Y

    left = bx0 / 2
    right = (bx1 + PLATE_WIDTH) / 2
    back = (by1 + PLATE_HEIGHT) / 2
    out = [(round(left, 3), 22.0), (round(left, 3), 74.0),
           (round(right, 3), 22.0), (round(right, 3), 74.0),
           (42.0, round(back, 3)), (93.0, round(back, 3))]

    for x, y in out:
        near = min(
            [math.dist((x, y), (h["x"] + DATUM_X, h["y"] + DATUM_Y)) for h in holes]
            + [_point_seg((x, y), (s["x0"] + DATUM_X, s["y0"] + DATUM_Y),
                          (s["x1"] + DATUM_X, s["y1"] + DATUM_Y)) for s in slots])
        if near < PLATE_HOLE_CLEAR:
            raise SystemExit(
                f"plate fixing at ({x}, {y}) is only {near:.2f} mm from a board "
                f"hole; needs {PLATE_HOLE_CLEAR}")
        edge = min(x, y, PLATE_WIDTH - x, PLATE_HEIGHT - y)
        if edge < PLATE_HOLE_DIA:
            raise SystemExit(
                f"plate fixing at ({x}, {y}) is only {edge:.2f} mm from the "
                f"plate edge")
    return out


def _point_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (ax + t * dx, ay + t * dy))


TEMPLATE = '''"""Tiny Tapeout generic mounting plate.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python scripts/design_mounting_plate.py

One plate that accepts any Tiny Tapeout demo board revision on standoffs while
holding the Pmod host headers in a single fixed place.  See the module
docstring of the generating script for how the pattern is derived.

Plate coordinates: origin at the lower-left corner of the plate, X right, Y up,
viewed from the side the board mounts on.
"""

from __future__ import annotations

from .schema import BoardSpec, Hole, Outline, Slot, Source

#: Pmod host pin-field centres, in plate coordinates.  These are the whole
#: point of the plate: they do not move when the board revision changes.
PMOD_SLOT_X = {pmod_x}
PMOD_ROW_Y = {pmod_y}
PMOD_PITCH = {pitch}

#: The Pmod connector body relative to its pin-field centre, as
#: (dx0, dx1, dy0, dy1).  Identical on every revision; the generator checks it
#: rather than assuming it.  dy0 is negative because the body overhangs the
#: edge its host faces, and that overhang is what fixes the plate's front edge.
PMOD_BODY = {pmod_body}

#: Where each revision's USB-C connector lands, in plate coordinates, as
#: (x0, y0, x1, y1).  Marked on the plate because a chassis has to open for it
#: and it moves further between revisions than anything else on the board.
USB_C = {usb_c}

#: Offset from the design frame (origin at the leftmost Pmod pin-field centre)
#: to plate coordinates.
DATUM_X = {datum_x}
DATUM_Y = {datum_y}

#: How to place each board revision: add these to a board coordinate to get a
#: plate coordinate.
PLACEMENTS = {{
{placements}
}}

PLATE = BoardSpec(
    key="tt-generic-mounting-plate",
    title="TT Generic Mounting Plate",
    subtitle="Accepts every demo board revision, Pmod hosts fixed in place",
    family="mountingplate",
    outline=Outline(width={w}, height={h}, corner_radius={r}, thickness=3.0),
    holes=(
{holes}
    ),
    slots=(
{slots}
    ),
    sources=(
        Source(label="Derived from",
               ref="data/tinytapeout_boards.py",
               note="Board outlines, mounting holes and Pmod host positions "
                    "for every Tiny Tapeout demo board revision, extracted "
                    "from the upstream KiCad files."),
        Source(label="Pmod host pitch",
               ref="https://digilent.com/reference/_media/reference/pmod/"
                   "pmod-interface-specification-1_2_0.pdf",
               note="Digilent mandate .90 in (22.86 mm) between adjacent host "
                    "ports on a board edge, which is why one plate can serve "
                    "every revision."),
    ),
    notes=(
        "Fit the board on standoffs. A board uses only the holes and slots "
        "its USED BY row names.",
        "Board holes and slots are {dia} mm, a close clearance fit on M3. "
        "Plate fixings are {pdia} mm, a clearance fit on M4. A slot spans two "
        "revisions whose holes are too close together to drill separately.",
        "The Pmod host connector bodies overhang the plate's front edge by "
        "{fc} mm, so a peripheral module plugs into clear air.",
        "Cut file: tt-generic-mounting-plate.dxf, four layers. Sizes here are "
        "finished sizes; allow for your cutter's kerf.",
    ),
)
'''


def main() -> None:
    place, holes, slots = build()
    check_fasteners(place, holes, slots)
    fixings = plate_fixings(place, holes, slots)

    print("Board placements (add to board coordinates to get plate coordinates):")
    for pl in place:
        ox, oy = pl["ox"] + DATUM_X, pl["oy"] + DATUM_Y
        b = pl["board"].outline
        print(f"  {pl['name']:9s} {pl['pmods']} Pmods, first on position "
              f"{pl['first_slot'] + 1}  offset ({ox:7.3f},{oy:6.3f})  "
              f"occupies x {ox:7.3f}..{ox + b.width:7.3f}  "
              f"y {oy:6.3f}..{oy + b.height:6.3f}")
    print()
    print(f"Plate {PLATE_WIDTH} x {PLATE_HEIGHT} mm, corner radius {PLATE_CORNER_R}")
    print(f"Pmod host pin-field centres at plate y = {DATUM_Y}, "
          f"x = {DATUM_X}, {DATUM_X + PMOD_PITCH}, {DATUM_X + 2 * PMOD_PITCH}")
    print()
    print(f"{len(holes)} holes and {len(slots)} slots for the boards, "
          f"{len(fixings)} plate fixings:")
    for h in holes:
        used = ", ".join(f"{r} {l}" for r, l in h["used"])
        print(f"  hole  ({h['x'] + DATUM_X:7.3f},{h['y'] + DATUM_Y:6.3f}) "
              f"dia {h['dia']:.2f}  spread {h['spread']:.3f}  <- {used}")
    for s in slots:
        used = ", ".join(f"{r} {l}" for r, l in s["used"])
        print(f"  slot  ({s['x0'] + DATUM_X:7.3f},{s['y0'] + DATUM_Y:6.3f}) to "
              f"({s['x1'] + DATUM_X:7.3f},{s['y1'] + DATUM_Y:6.3f}) "
              f"w {s['width']:.2f}  <- {used}")
    for x, y in fixings:
        print(f"  fixing({x:7.3f},{y:6.3f}) dia {PLATE_HOLE_DIA:.2f}")

    # Emit the data module.
    def hole_src():
        out = []
        for h in holes:
            used = "+".join(f"{r}:{l}" for r, l in h["used"])
            note = (f"Serves {len(h['used'])} revision positions spread "
                    f"{h['spread']:.3f} mm; drilled at their midpoint."
                    if h["spread"] else "")
            out.append(f'        Hole(x={h["x"] + DATUM_X:.3f}, '
                       f'y={h["y"] + DATUM_Y:.3f}, dia={h["dia"]:.2f}, '
                       f'label={used!r}, kind="board", tol=None),'
                       + (f"  # {note}" if note else ""))
        for x, y in fixings:
            out.append(f'        Hole(x={x:.3f}, y={y:.3f}, '
                       f'dia={PLATE_HOLE_DIA:.2f}, label="PLATE", kind="plate"),')
        return "\n".join(out)

    def slot_src():
        out = []
        for s in slots:
            used = "+".join(f"{r}:{l}" for r, l in s["used"])
            out.append(f'        Slot(x0={s["x0"] + DATUM_X:.3f}, '
                       f'y0={s["y0"] + DATUM_Y:.3f}, '
                       f'x1={s["x1"] + DATUM_X:.3f}, y1={s["y1"] + DATUM_Y:.3f}, '
                       f'width={s["width"]:.2f}, label={used!r},\n'
                       f'             note="Two revisions want a fastener '
                       f'{s["spread"]:.3f} mm apart here, too close to drill '
                       f'as separate holes."),')
        return "\n".join(out)

    def place_src():
        out = []
        for pl in place:
            out.append(f'    {pl["name"]!r}: dict(revision={pl["key"]!r}, '
                       f'revisions={pl["revisions"]!r},\n'
                       f'        shuttles={pl["shuttles"]!r}, '
                       f'dx={pl["ox"] + DATUM_X:.3f}, '
                       f'dy={pl["oy"] + DATUM_Y:.3f}, '
                       f'first_pmod_position={pl["first_slot"] + 1}, '
                       f'pmod_count={pl["pmods"]}),')
        return "\n".join(out)

    text = TEMPLATE.format(
        pmod_x=repr(tuple(round(DATUM_X + i * PMOD_PITCH, 3) for i in range(3))),
        pmod_y=DATUM_Y, pitch=PMOD_PITCH, pmod_body=repr(PMOD_BODY),
        usb_c="{\n" + "".join(
            f"    {k!r}: {v!r},\n" for k, v in usb_c_positions(place).items()
        ) + "}",
        datum_x=DATUM_X, datum_y=DATUM_Y,
        placements=place_src(), holes=hole_src(), slots=slot_src(),
        w=PLATE_WIDTH, h=PLATE_HEIGHT, r=PLATE_CORNER_R,
        dia=HOLE_DIA, fc=FRONT_CLEARANCE, pdia=PLATE_HOLE_DIA)
    (ROOT / "data" / "mounting_plate.py").write_text(text)
    print("\nwrote data/mounting_plate.py")


if __name__ == "__main__":
    main()
