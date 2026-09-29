#!/usr/bin/env python3
"""Design the two base plates and write their data module.

Each plate carries a Raspberry Pi and an FPGA board joined by the direct
Raspmod (``ACC-HAT-DRMOD``): the adapter sits on the Pi's 40-pin header and
its three right-angle plugs go sideways into the FPGA board's Pmod hosts.
What a plate has to get right is the HEIGHT of each board, so that the
plug rows meet the host rows, and the POSITION of each, so that the plugs
meet the hosts.  Both are worked out here from the data modules -- the
adapter's board file, the Pi's drawings, the TT mounting plate, the Arty's
drawing and STEP model -- and from the connectors' own datasheets, and
nothing on either sheet is typed in.

The stack, from the Pi's top face up
------------------------------------
The Pi's header body is 2.54 tall.  The adapter's socket, 3.8 tall, sits on
it, so the adapter's underside is 6.34 above the Pi and its top face 7.94.
A right-angle 2x6 header on that face has its pin rows 1.27 and 3.81 above
it; a right-angle 2x6 host socket has its rows 4.53 and 7.07 above ITS
board.  So the host board's top face has to be 7.94 + 1.27 - 4.53 = 4.68
above the Pi's, and the plate's standoffs are chosen to put it there.

* ``BP-TT``: the TT mounting plate lies flat on the base plate, held by
  its own six M4 fixings, and every demoboard revision stands on it on the
  8 mm standoffs the plate specifies.  The Pi's standoff is what makes the
  Pi's top face 4.68 below the demoboard's.
* ``BP-ARTY``: the Arty has no mounting holes and stands on four rubber
  feet, and on those feet it is too LOW: the Pi would have to go below the
  plate.  So it stands in four corner cups, one under each foot, whose
  height is what puts the Arty's top face 4.68 above the Pi's on the
  shortest standoff there is.  Two Pi positions, for plugs into JA-JC or
  JB-JD.

The plan
--------
The adapter's plug centres go over the host centres.  The adapter's edge is
1.14 in front of its plug bodies' faces, which butt the socket faces when
pushed home; the demoboard's socket faces stand 2.78 in front of the TT
plate's front edge, the Arty's are flush with its edge.  The Pi then sits
where the adapter's socket puts it, pin 1 on pin 1, which is a half turn:
the Pi's SD-card end is under the adapter's pin-1 end.

Run: uv run --no-project --with pdfplumber --with cadquery python base_plates/design.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from accessories.raspmod_direct import PI_PIN1, PI_PIN2, RASPMOD_DIRECT  # noqa: E402
from fpga.boards import BOARDS as FPGA  # noqa: E402
from raspberry_pi.boards import BOARDS as RPI  # noqa: E402
from raspberry_pi_camera.optics import plate_board_plane  # noqa: E402
from tinytapeout.boards import BOARDS as TT  # noqa: E402
from tinytapeout.mounting_plate.plate import (PLACEMENTS, PLATE,  # noqa: E402
                                              PMOD_BODY, PMOD_ROW_Y,
                                              PMOD_SLOT_X, STANDOFF_HEIGHT)
from tools.layout import drawing_name  # noqa: E402

OUT = ROOT / "base_plates" / "plates.py"

# ---------------------------------------------------------------------------
# The connectors, from their datasheets
# ---------------------------------------------------------------------------

#: The demoboard's Pmod host socket, which its board file names: a
#: right-angle 2x6 socket standing its 5.0 body on 3.3 legs, 8.5 deep.  The
#: rows are taken to be centred in the body, 2.54 apart.
HOST_SOCKET_LEGS = 3.3
HOST_SOCKET_BODY = 5.0
HOST_SOCKET_DEPTH = 8.5
HOST_SOCKET_SRC = ("Wurth 613012243121",
                   "https://www.we-online.com/components/products/datasheet/613012243121.pdf",
                   "angled 2x6 socket, the demoboard's: legs 3.3, body 5.0, "
                   "8.5 deep")
HOST_ROWS = tuple(round(HOST_SOCKET_LEGS + HOST_SOCKET_BODY / 2 + d, 2)
                  for d in (-1.27, 1.27))
#: The adapter's plug: a right-angle 2x6 pin header with its 5.08 body on
#: the board, rows 1.27 and 3.81 up, the body's back 1.5 from the near leg
#: and 2.54 deep, 6.0 mm pins.
PLUG_ROWS = (1.27, 3.81)
PLUG_BODY = 5.08
PLUG_LEG_TO_BODY = 1.5
PLUG_BODY_DEPTH = 2.54
PLUG_PINS = 6.0
PLUG_SRC = ("Wurth 61301221021",
            "https://www.we-online.com/components/products/datasheet/61301221021.pdf",
            "angled 2x6 pin header: near leg 1.5 from the body, pins 6 long")
#: The socket that puts the adapter on the Pi.
SOCKET_H = 3.8
SOCKET_SRC = ("Kaweei CS25582-40G-M36-0A, Adafruit 2187",
              "https://www.adafruit.com/product/2187",
              "2x20 SMT socket, 3.8 tall")
#: The Pi's own header: 2.54 body, 8.5 to the pin tips, on every model.
PI_HEADER_BODY = 2.54
PI_HEADER_H = 8.5
PI_HEADER_SRC = ("Raspberry Pi 4 and 3B+ mechanical drawings",
                 "https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf",
                 "the 40-pin header: 2.54 body, 8.5 to the pin tips")

#: The socket's body sits on the Pi's header body, so this is where the
#: adapter's underside is above the Pi's top face; and where its top is.
ADAPTER_T = RASPMOD_DIRECT.outline.thickness
ADAPTER_UNDER = round(PI_HEADER_BODY + SOCKET_H, 2)
ADAPTER_TOP = round(ADAPTER_UNDER + ADAPTER_T, 2)
#: A host board's top face above the Pi's, for the rows to meet.
HOST_ABOVE_PI = round(ADAPTER_TOP + PLUG_ROWS[0] - HOST_ROWS[0], 2)
#: The adapter's edge to its plugs' faces: the near leg row is 2.86 from
#: the edge on the board, the body's back 1.5 behind it and 2.54 deep.
PLUG_NEAR_ROW = round(min(p.cy - 1.27 for p in RASPMOD_DIRECT.pmods
                          if p.role == "plug"), 2)
EDGE_TO_PLUG_FACE = round(PLUG_LEG_TO_BODY + PLUG_BODY_DEPTH - PLUG_NEAR_ROW, 2)

# ---------------------------------------------------------------------------
# The boards, from their sources
# ---------------------------------------------------------------------------

#: Standard sizes, M2.5 female-female for the Pi, M3 for the demoboard.
PI_STANDOFFS = (3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0)
WASHER = 0.5
#: Plate: 3 mm, like the TT plate, aluminium or acrylic.
PLATE_T = 3.0
MARGIN = 8.0
#: Holes: clearance for the Pi's M2.5, the cups' M3; the TT plate's M4 go
#: into tapped holes, the TT plate being what the base plate is chassis to.
PI_HOLE = 2.75
CUP_HOLE = 3.4
M4_TAP_DRILL = 3.3
#: A cup, printed: a ledge under the foot with two walls outside the
#: board's corner.  12 wide so the top ones clear the outer Pmod sockets,
#: and 2 mm walls standing 2 mm over the board's top face.
CUP_W = 11.0
CUP_WALL = 2.0
CUP_WALL_OVER = 2.0
#: The hole printed in a cup for its M3 screw, which cuts its own thread.
CUP_SCREW_HOLE = 2.5


def shifted(to_a, to_pi, dx: float, dy: float):
    """The two maps of ``pi_map`` with the host board's origin moved to (dx, dy)."""
    def a(xa, ya):
        x, y = to_a(xa, ya)
        return (round(x + dx, 2), round(y + dy, 2))

    def p(X, Y):
        x, y = to_pi(X, Y)
        return (round(x + dx, 2), round(y + dy, 2))
    return a, p


def pi_thickness() -> tuple[float, str]:
    """The Pi's PCB thickness, measured off the Pi 5 drawing's side view.

    Raspberry Pi Ltd state no thickness; the Pi 5 drawing is 1:1 and its
    side elevation is vector art, so the two long horizontal lines that are
    the board's faces can be measured, once the plot scale is recovered
    from the plan the way ``raspberry_pi/extract.py`` recovers it.
    """
    import pdfplumber
    from tools.dump_rpi_pdf import find_origin, points_mm
    pdf = ROOT / "tmp" / "rpi" / "raspberry-pi-5-mechanical-drawing.pdf"
    if not pdf.exists():
        raise SystemExit(f"missing {pdf.relative_to(ROOT)}; run make fetch")
    page = pdfplumber.open(str(pdf)).pages[0]
    ox, oy, scale = find_origin(page)
    ys = set()
    for obj in page.lines + page.curves + page.rects:
        pts = points_mm(page, obj)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if abs(y1 - y2) < 0.02 and abs(x1 - x2) * scale > 30 and y1 < oy - 40:
                ys.add(round((y1 - oy) * scale, 3))
    ys = sorted(ys)
    pairs = [(a, b) for a in ys for b in ys if 1.0 < b - a < 2.0]
    if len(pairs) != 1:
        raise SystemExit(f"the Pi 5 side view gives {len(pairs)} face pairs, not one: {ys}")
    t = round(pairs[0][1] - pairs[0][0], 2)
    return t, (f"two horizontal lines {t} mm apart in the side elevation of the "
               f"Pi 5 drawing, at plot scale {scale:.4f}")


def arty_from_step() -> dict:
    """The Arty's thickness and feet, read off Digilent's rev C STEP."""
    from tools import step_model
    stp = ROOT / "tmp" / "src" / "arty_a7" / "arty_revc_cad" / "ARTY For Web" / "Arty Rev C.stp"
    if not stp.exists():
        raise SystemExit(f"missing {stp.relative_to(ROOT)}; run make fetch")
    m = step_model.load(str(stp))
    board = m.largest()
    lo, hi = m.slab(board)
    feet = m.named("Ruber_Feet")
    if len(feet) != 4:
        raise SystemExit(f"the Arty STEP has {len(feet)} feet, not 4")
    heights = {round(f.z1 - f.z0, 2) for f in feet}
    dias = {round(f.x1 - f.x0, 2) for f in feet}
    if len(heights) != 1 or len(dias) != 1:
        raise SystemExit(f"the Arty's feet differ: heights {heights}, diameters {dias}")
    if any(abs(f.z1 - lo) > 0.01 for f in feet):
        raise SystemExit("the Arty's feet do not sit on the slab's underside")
    # Their centres, from the board's lower-left corner, checked against the
    # 5.0 mm from each corner Digilent's drawing gives.
    centres = sorted((round((f.x0 + f.x1) / 2 - board.x0, 2),
                      round((f.y0 + f.y1) / 2 - board.y0, 2)) for f in feet)
    return dict(thickness=round(hi - lo, 3), feet_h=heights.pop(), feet_dia=dias.pop(),
                feet=centres, width=round(board.x1 - board.x0, 2),
                height=round(board.y1 - board.y0, 2))


def dxf_feet(arty: dict) -> list[tuple[float, float]]:
    """The feet 5.0 from each corner of the DXF outline, the STEP agreeing.

    The STEP's centres are from its own slab's corner, and that slab is a
    fifth of a millimetre off the DXF's size, so each is checked against
    the nearest corner rather than copied.
    """
    a = FPGA["arty-a7"]
    feet = [(x, y) for x in (5.0, a.outline.width - 5.0) for y in (5.0, a.outline.height - 5.0)]
    for sx, sy in arty["feet"]:
        ex = min(sx, arty["width"] - sx)
        ey = min(sy, arty["height"] - sy)
        if abs(ex - 5.0) > 0.3 or abs(ey - 5.0) > 0.3:
            raise SystemExit(f"a STEP foot sits {ex:.2f} and {ey:.2f} from its slab's "
                             f"edges, not 5.0 (slab {arty['width']} x {arty['height']})")
    return feet


def pi_header_pins(pi) -> tuple[tuple[float, float], tuple[float, float]]:
    """Pins 1 and 2 of the Pi's header, from the header box its drawing gives.

    The box is 20 pitches long and its centre line is the hole line; pin 1
    is the first pin of the inner row, pin 2 above it on the outer row.
    """
    f = next(f for f in pi.features if f.key == "gpio40")
    if abs((f.x1 - f.x0) - 20 * 2.54) > 0.05:
        raise SystemExit(f"{pi.key}: the header box is {f.x1 - f.x0:.2f} long, not 50.8")
    cy = (f.y0 + f.y1) / 2
    return (round(f.x0 + 1.27, 2), round(cy - 1.27, 2)), (round(f.x0 + 1.27, 2), round(cy + 1.27, 2))


def pi_map(pi, host_x0: float, edge_y: float, x_sign: int):
    """Adapter and Pi coordinates to the plate's, for one placement.

    *host_x0* is where the adapter's own x = 0 lands on the plate, and
    *x_sign* which way its x runs there; *edge_y* is where its plug edge
    lands, its y running away from that edge.  The Pi follows from the
    adapter's socket pin 1 sitting on the Pi's pin 1 and pin 2 on pin 2,
    which fixes it as a half turn of the adapter.
    """
    p1, p2 = pi_header_pins(pi)
    a1, a2 = PI_PIN1, PI_PIN2
    # The adapter's pin 2 is below its pin 1 (smaller y); the Pi's pin 2 is
    # above (larger y): the Pi's y runs against the adapter's, and so does
    # its x, which is the half turn.
    if not (a2[1] < a1[1] and p2[1] > p1[1]):
        raise SystemExit("the header pin 1 / pin 2 relation is not what the half turn assumes")

    def to_plate_from_adapter(xa, ya):
        # y: the plug edge (ya = 0) is at edge_y and ya runs away from the
        # host, which is -y on the TT plate (host to the north) and +y on
        # the Arty plate (host to the south).  The caller says which by the
        # sign of x: seen from above, a right-handed frame whose x runs
        # west has its y running south, and one whose x runs east, north.
        return (host_x0 + x_sign * xa, edge_y + x_sign * ya)

    def to_plate_from_pi(X, Y):
        xa = a1[0] - (X - p1[0]) * 1.0
        ya = a1[1] - (Y - p1[1]) * 1.0
        return to_plate_from_adapter(xa, ya)
    return to_plate_from_adapter, to_plate_from_pi


def stack(pi_t: float, host_top: float, pi_standoff: float) -> dict:
    """Every height above the plate for a Pi on *pi_standoff*, as a dict."""
    pi_top = pi_standoff + pi_t
    z = dict(pi_under=pi_standoff, pi_top=pi_top,
             header_top=pi_top + PI_HEADER_BODY, pins_top=pi_top + PI_HEADER_H,
             socket_top=pi_top + ADAPTER_UNDER, adapter_top=pi_top + ADAPTER_TOP)
    z["plug_rows"] = tuple(round(z["adapter_top"] + r, 2) for r in PLUG_ROWS)
    z["host_rows"] = tuple(round(host_top + r, 2) for r in HOST_ROWS)
    z["residual"] = round(z["plug_rows"][0] - z["host_rows"][0], 2)
    return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in z.items()}


def choose_pi_standoff(pi_t: float, host_top: float) -> tuple[float, str]:
    """The bought stack that puts the Pi nearest where it has to be."""
    want = host_top - HOST_ABOVE_PI - pi_t
    options = [(s, "") for s in PI_STANDOFFS] + [(s + WASHER, "+ washer") for s in PI_STANDOFFS]
    best = min(options, key=lambda o: abs(o[0] - want))
    return best[0], best[1]


def pi_tall_parts(pi) -> list[tuple[str, float, float, float, float, float]]:
    """What stands on the Pi taller than the adapter's underside, and where.

    The USB and Ethernet connectors, with the heights the Pi 4 drawing
    labels them (16.0 and 13.5); the Pi 5 drawing labels none, and its
    connectors are the same parts.  And the PoE header of the 3B+ and 4B,
    a 2x2 pin header at the place both drawings put it, as tall as the
    40-pin header.  The 40-pin header itself is what the adapter sits on.
    """
    out = []
    for f in pi.features:
        if f.kind == "usb_a":
            out.append((f.label, f.x0, f.y0, f.x1, f.y1, 16.0))
        elif f.kind == "ethernet":
            out.append((f.label, f.x0, f.y0, f.x1, f.y1, 13.5))
    # The parts inside the adapter's footprint, read off the drawings once,
    # in accessories/pi_under.py, which the adapter's own sheet draws.
    from accessories.pi_under import parts_on
    for p in parts_on(pi.key):
        out.append((p.label, p.x0, p.y0, p.x1, p.y1, p.z))
    return out


def adapter_over_pi() -> tuple[float, float, float, float]:
    """The adapter's footprint in the Pi's own frame: the strip over the Pi."""
    p1, _ = pi_header_pins(RPI["rpi5"])
    a1 = PI_PIN1
    o = RASPMOD_DIRECT.outline
    xs = [p1[0] + (a1[0] - x) for x in (0.0, o.width)]
    ys = [p1[1] + (a1[1] - y) for y in (0.0, o.height)]
    return (round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2))


def which_pis_fit() -> tuple[list[str], list[tuple[str, str]]]:
    x0, y0, x1, y1 = adapter_over_pi()
    fits, excluded = [], []
    for key in ("rpi3b", "rpi4b", "rpi5"):
        pi = RPI[key]
        clash = []
        for label, fx0, fy0, fx1, fy1, z in pi_tall_parts(pi):
            if z > ADAPTER_UNDER and fx0 < x1 and fx1 > x0 and fy0 < y1 and fy1 > y0:
                clash.append(f"{label} ({z:g} mm)")
        # The 3B+ shares the 3B's sheet, and the 4B's PoE header.
        title = pi.title.replace(" and B+", "")
        if clash:
            excluded.append((title, ", ".join(clash)))
        else:
            fits.append(title)
    excluded.append(("Raspberry Pi 3 Model B+", "PoE header (8.5 mm), where the 4B's is"))
    return fits, excluded


# ---------------------------------------------------------------------------
# The two plates
# ---------------------------------------------------------------------------

def tt_plate(pi_t: float, pi_t_src: str) -> dict:
    pi = RPI["rpi5"]
    board_lo, board_hi = plate_board_plane()
    host_top = PLATE_T + (board_lo + board_hi) / 2        # above the base plate
    s_pi, note = choose_pi_standoff(pi_t, host_top)
    z = stack(pi_t, host_top, s_pi)

    # Where things go.  The TT plate's front edge is the reference: its
    # hosts' socket faces are PMOD_BODY[2] behind their pin fields.
    socket_face = PMOD_ROW_Y + PMOD_BODY[2]           # negative: in front
    edge_y_mp = socket_face - EDGE_TO_PLUG_FACE
    plugs = sorted((p for p in RASPMOD_DIRECT.pmods if p.role == "plug"), key=lambda p: p.cx)
    # The adapter's x runs west here (its plug edge faces the plate, north):
    # its first plug goes over the plate's LAST host.
    host_x0_mp = PMOD_SLOT_X[-1] + plugs[0].cx
    to_a, to_pi = pi_map(pi, host_x0_mp, edge_y_mp, -1)
    pi_x0, pi_y0 = to_pi(0.0, 0.0)
    pi_x1, pi_y1 = to_pi(pi.outline.width, pi.outline.height)
    mpy = round(MARGIN - min(pi_y0, pi_y1), 2)          # the TT plate's origin
    mpy = float(int(mpy) + (1 if mpy % 1 else 0))     # a whole millimetre
    mpx = 0.0
    W = PLATE.outline.width
    H = float(int(mpy + PLATE.outline.height + 0.999))
    to_a, to_pi = shifted(to_a, to_pi, mpx, mpy)

    def mp(x, y):
        return (round(mpx + x, 2), round(mpy + y, 2))

    boxes = []
    holes = []
    # The TT plate and its fixings, which are this plate's holes.
    x0, y0 = mp(0, 0)
    x1, y1 = mp(PLATE.outline.width, PLATE.outline.height)
    boxes.append(("adjacent", drawing_name("mounting-plate", PLATE.key), x0, x1, y0, y1, 0.0, PLATE_T, ()))
    for h in PLATE.holes:
        if h.kind == "plate":
            hx, hy = mp(h.x, h.y)
            holes.append((hx, hy, M4_TAP_DRILL, "MP", "tapped M4, the TT plate's fixing"))
    # Every revision's board, as one slab, and the hosts.
    from raspberry_pi_camera.optics import plate_boards_union
    bx0, by0, bx1, by1 = plate_boards_union()
    (ux0, uy0), (ux1, uy1) = mp(bx0, by0), mp(bx1, by1)
    boxes.append(("adjacent", "Demoboard, every revision", ux0, ux1, uy0, uy1,
                  PLATE_T + STANDOFF_HEIGHT, host_top, ()))
    for x in PMOD_SLOT_X:
        bx0, by0 = mp(x + PMOD_BODY[0], PMOD_ROW_Y + PMOD_BODY[2])
        bx1, by1 = mp(x + PMOD_BODY[1], PMOD_ROW_Y + PMOD_BODY[3])
        boxes.append(("header", "Pmod host socket", bx0, bx1, by0, by1,
                      host_top + HOST_SOCKET_LEGS, host_top + HOST_SOCKET_LEGS + HOST_SOCKET_BODY,
                      z["host_rows"]))
    # The demoboard's standoffs, for the representative revision.
    rev = PLACEMENTS["DB ETR v3.3"]
    for h in TT[rev["revision"]].holes:
        hx, hy = mp(rev["dx"] + h.x, rev["dy"] + h.y)
        boxes.append(("standoff", f"M3 x {STANDOFF_HEIGHT:g}", hx - 2.5, hx + 2.5, hy - 2.5, hy + 2.5,
                      PLATE_T, PLATE_T + STANDOFF_HEIGHT, ()))
    boxes += common_boxes(pi, to_a, to_pi, z, s_pi, holes, "")
    levels = [
        ("TT plate top face", PLATE_T),
        ("Demoboard underside", PLATE_T + STANDOFF_HEIGHT),
        ("Demoboard top face", round(host_top, 2)),
        ("Host socket rows", z["host_rows"]),
        ("Pi underside", z["pi_under"]),
        ("Pi top face", z["pi_top"]),
        ("Adapter underside", z["socket_top"]),
        ("Adapter top face", z["adapter_top"]),
        ("Plug rows", z["plug_rows"]),
    ]
    standoffs = [
        (6, "M4 screw into the plate", drawing_name("mounting-plate", PLATE.key)),
        (4, f"M3 x {STANDOFF_HEIGHT:g} F/F, the TT plate's own", "demoboard"),
        (4, f"M2.5 x {s_pi - (WASHER if note else 0):g} F/F{' over a 0.5 washer' if note else ''}",
         "Raspberry Pi"),
    ]
    return dict(key="tt-pi", title="Base Plate, TT Plate and Raspberry Pi",
                subtitle="A demoboard on the TT plate, a Pi, and the direct Raspmod between them",
                w=W, h=H, holes=holes, boxes=boxes, levels=levels, standoffs=standoffs,
                z=z, s_pi=s_pi, pi_t=pi_t, pi_t_src=pi_t_src, host_top=host_top,
                mp=(mpx, mpy), made=[],
                positions=[("", *to_pi(0.0, 0.0))])


def common_boxes(pi, to_a, to_pi, z, s_pi, holes, position) -> list:
    """The Pi, its standoffs and header, the adapter, its socket and plugs."""
    boxes = []
    (x0, y0), (x1, y1) = to_pi(0, 0), to_pi(pi.outline.width, pi.outline.height)
    lo = lambda a, b: (min(a, b), max(a, b))  # noqa: E731
    px0, px1 = lo(x0, x1)
    py0, py1 = lo(y0, y1)
    kind = "alt" if position == "B" else "adjacent"
    boxes.append((kind, "Raspberry Pi", round(px0, 2), round(px1, 2), round(py0, 2), round(py1, 2),
                  z["pi_under"], z["pi_top"], (), position))
    for h in pi.holes:
        if h.kind != "mount":
            continue
        hx, hy = to_pi(h.x, h.y)
        holes.append((round(hx, 2), round(hy, 2), PI_HOLE, f"PI{position}",
                      f"M2.5 clearance, the Pi's {h.label}"))
        boxes.append(("standoff" if kind == "adjacent" else "alt", f"M2.5 x {s_pi:g}",
                      round(hx - 2.5, 2), round(hx + 2.5, 2), round(hy - 2.5, 2), round(hy + 2.5, 2),
                      0.0, z["pi_under"], (), position))
    g = next(f for f in pi.features if f.key == "gpio40")
    (gx0, gy0), (gx1, gy1) = to_pi(g.x0, g.y0), to_pi(g.x1, g.y1)
    gx0, gx1 = lo(gx0, gx1)
    gy0, gy1 = lo(gy0, gy1)
    boxes.append(("header" if kind == "adjacent" else "alt", "Pi 40-pin header",
                  round(gx0, 2), round(gx1, 2), round(gy0, 2), round(gy1, 2),
                  z["pi_top"], z["pins_top"], (), position))
    # The adapter, its socket under it, its plugs on it.
    o = RASPMOD_DIRECT.outline
    (ax0, ay0), (ax1, ay1) = to_a(0, 0), to_a(o.width, o.height)
    ax0, ax1 = lo(ax0, ax1)
    ay0, ay1 = lo(ay0, ay1)
    name = drawing_name("accessories", "raspmod-direct")
    boxes.append((kind, name, round(ax0, 2), round(ax1, 2), round(ay0, 2), round(ay1, 2),
                  z["socket_top"], z["adapter_top"], (), position))
    s = next(f for f in RASPMOD_DIRECT.features if f.key == "socket")
    (sx0, sy0), (sx1, sy1) = to_a(s.x0, s.y0), to_a(s.x1, s.y1)
    sx0, sx1 = lo(sx0, sx1)
    sy0, sy1 = lo(sy0, sy1)
    boxes.append(("header" if kind == "adjacent" else "alt", "Adapter socket, on the Pi's header",
                  round(sx0, 2), round(sx1, 2), round(sy0, 2), round(sy1, 2),
                  z["header_top"], z["socket_top"], (), position))
    for p in RASPMOD_DIRECT.pmods:
        if p.role != "plug":
            continue
        # The body sits behind the near leg row; the pins run on past the edge.
        body_y0 = p.cy - 1.27 - PLUG_LEG_TO_BODY - PLUG_BODY_DEPTH
        body_y1 = p.cy - 1.27 - PLUG_LEG_TO_BODY
        (bx0, by0), (bx1, by1) = to_a(p.cx - 7.62 - 0.5, body_y0), to_a(p.cx + 7.62 + 0.5, body_y1)
        bx0, bx1 = lo(bx0, bx1)
        by0, by1 = lo(by0, by1)
        boxes.append(("header" if kind == "adjacent" else "alt", f"Plug {p.label}",
                      round(bx0, 2), round(bx1, 2), round(by0, 2), round(by1, 2),
                      z["adapter_top"], z["adapter_top"] + PLUG_BODY, z["plug_rows"], position))
        (qx0, qy0), (qx1, qy1) = to_a(p.cx - 6.35, body_y0 - PLUG_PINS), to_a(p.cx + 6.35, body_y0)
        qx0, qx1 = lo(qx0, qx1)
        qy0, qy1 = lo(qy0, qy1)
        boxes.append(("header" if kind == "adjacent" else "alt", f"Plug {p.label} pins",
                      round(qx0, 2), round(qx1, 2), round(qy0, 2), round(qy1, 2),
                      z["plug_rows"][0] - 0.32, z["plug_rows"][1] + 0.32, z["plug_rows"], position))
    return boxes


def arty_plate(pi_t: float, pi_t_src: str, arty: dict) -> dict:
    pi = RPI["rpi5"]
    a = FPGA["arty-a7"]
    hosts = {p.label: p for p in a.pmods}
    # The STEP is Digilent's "for web" model: its slab is 109.22 x 86.36 to
    # the DXF's 109 x 87.  Near enough to trust for a thickness and a foot,
    # not for a position: the feet go 5.0 from each corner of the DXF
    # outline, where its own note puts them, and the STEP's centres are
    # checked to sit within a third of a millimetre of that.
    if abs(arty["width"] - a.outline.width) > 1.0 or abs(arty["height"] - a.outline.height) > 1.0:
        raise SystemExit("the Arty STEP and DXF disagree about the board's size")
    # The shortest Pi standoff, and cups tall enough to bring the Arty's top
    # face HOST_ABOVE_PI over the Pi's.
    s_pi = PI_STANDOFFS[1]
    pi_top = s_pi + pi_t
    arty_top = round(pi_top + HOST_ABOVE_PI, 2)
    cup_h = round(arty_top - arty["thickness"] - arty["feet_h"], 2)
    if cup_h < 2.0:
        raise SystemExit(f"a {cup_h} mm cup is too thin to print")
    z = stack(pi_t, arty_top, s_pi)

    plugs = sorted((p for p in RASPMOD_DIRECT.pmods if p.role == "plug"), key=lambda p: p.cx)
    # The Arty's hosts face away from its board, off its far edge.  It goes
    # on the plate a half turn round, so that they face the front and the
    # Pi sits in front of it as on the TT plate: every base plate has its
    # Pi at the front, y small, and the FPGA board behind.  rot() is the
    # Arty's own frame turned that half turn, still at its own origin.
    aw, ah = a.outline.width, a.outline.height

    def rot(x, y):
        return (aw - x, ah - y)

    # The adapter is then in front of the hosts' faces, plug edge facing
    # north, its x running west: its first plug goes over the host with
    # the largest x, exactly as on the TT plate.
    face_y = rot(0, max(p.body_y1 for p in a.pmods))[1]
    edge_y_a = face_y - EDGE_TO_PLUG_FACE
    positions = {"A": ("JA", "JB", "JC"), "B": ("JB", "JC", "JD")}
    maps = {}
    for pos, names in positions.items():
        host_x0 = rot(hosts[names[0]].cx, 0)[0] + plugs[0].cx
        maps[pos] = pi_map(pi, host_x0, edge_y_a, -1)
        for plug, name in zip(plugs, names):
            landed = host_x0 - plug.cx
            want = rot(hosts[name].cx, 0)[0]
            if abs(landed - want) > 0.2:
                raise SystemExit(f"plug {plug.label} lands {landed - want:+.2f} off {name}")
    # The plate: the Arty, the Pi in both positions, a margin round all of it.
    xs, ys = [0.0, aw], [0.0, ah]
    for to_a, to_pi in maps.values():
        for X, Y in ((0, 0), (pi.outline.width, pi.outline.height)):
            x, y = to_pi(X, Y)
            xs.append(x)
            ys.append(y)
    ax = float(int(MARGIN - min(xs) + 0.999))
    ay = float(int(MARGIN - min(ys) + 0.999))
    W = float(int(ax + max(xs) + MARGIN + 0.999))
    H = float(int(ay + max(ys) + MARGIN + 0.999))

    def ar(x, y):
        """The Arty's own coordinates to the plate's."""
        rx, ry = rot(x, y)
        return (round(ax + rx, 2), round(ay + ry, 2))

    def span(p, q):
        """Two opposite corners in the Arty's frame as a plate box's x0, x1, y0, y1."""
        (px, py), (qx, qy) = ar(*p), ar(*q)
        return min(px, qx), max(px, qx), min(py, qy), max(py, qy)

    boxes, holes = [], []
    x0, x1, y0, y1 = span((0, 0), (aw, ah))
    boxes.append(("adjacent", a.title, x0, x1, y0, y1, arty_top - arty["thickness"], arty_top, ()))
    for p in a.pmods:
        bx0, bx1, by0, by1 = span((p.body_x0, p.body_y0), (p.body_x1, p.body_y1))
        boxes.append(("header", f"Pmod host {p.label}", bx0, bx1, by0, by1,
                      arty_top + HOST_SOCKET_LEGS, arty_top + HOST_SOCKET_LEGS + HOST_SOCKET_BODY,
                      z["host_rows"]))
    made = []
    for fx, fy in arty["feet"]:
        r = arty["feet_dia"] / 2
        cx, cy = ar(fx, fy)
        boxes.append(("adjacent", "Rubber foot", cx - r, cx + r, cy - r, cy + r,
                      cup_h, cup_h + arty["feet_h"], ()))
        # The cup: a ledge under the foot, walls on the corner's outer sides.
        left, bottom = fx < aw / 2, fy < ah / 2
        lx0 = -CUP_WALL if left else aw - CUP_W + CUP_WALL
        ly0 = -CUP_WALL if bottom else ah - CUP_W + CUP_WALL
        lx1, ly1 = lx0 + CUP_W + CUP_WALL, ly0 + CUP_W + CUP_WALL
        cx0, cx1, cy0, cy1 = span((lx0, ly0), (lx1, ly1))
        boxes.append(("made", "Cup", cx0, cx1, cy0, cy1, 0.0, cup_h, ()))
        wall_top = round(arty_top + CUP_WALL_OVER, 2)
        wx = (lx0, lx0 + CUP_WALL) if left else (lx1 - CUP_WALL, lx1)
        wy = (ly0, ly0 + CUP_WALL) if bottom else (ly1 - CUP_WALL, ly1)
        wx0, wx1, _, _ = span((wx[0], 0), (wx[1], 0))
        boxes.append(("made", "Cup wall", wx0, wx1, cy0, cy1, cup_h, wall_top, ()))
        _, _, wy0, wy1 = span((0, wy[0]), (0, wy[1]))
        boxes.append(("made", "Cup wall", cx0, cx1, wy0, wy1, cup_h, wall_top, ()))
        holes.append((cx, cy, CUP_HOLE, "CUP", "M3 clearance, countersunk below, into the cup"))
    made.append(("Corner cup", 4, f"{CUP_W + CUP_WALL:g} x {CUP_W + CUP_WALL:g} x {wall_top:g}",
                 f"ledge {cup_h:g} tall under the foot, {CUP_WALL:g} mm walls on the two outer "
                 f"sides to {wall_top:g}, a {CUP_SCREW_HOLE:g} hole for the M3 screw; print flat"))
    pi_positions = []
    for pos, (to_a, to_pi) in maps.items():
        to_a, to_pi = shifted(to_a, to_pi, ax, ay)
        boxes += common_boxes(pi, to_a, to_pi, z, s_pi, holes, pos)
        pi_positions.append((f"{pos}: plugs into {', '.join(positions[pos])}", *to_pi(0.0, 0.0)))
    levels = [
        ("Cup ledge", cup_h),
        ("Arty underside", round(arty_top - arty["thickness"], 2)),
        ("Arty top face", arty_top),
        ("Host socket rows", z["host_rows"]),
        ("Pi underside", z["pi_under"]),
        ("Pi top face", z["pi_top"]),
        ("Adapter underside", z["socket_top"]),
        ("Adapter top face", z["adapter_top"]),
        ("Plug rows", z["plug_rows"]),
    ]
    standoffs = [
        (4, "corner cup, printed, and an M3 countersunk screw from below", "Arty A7"),
        (4, f"M2.5 x {s_pi:g} F/F, in either set of four holes", "Raspberry Pi"),
    ]
    return dict(key="arty-pi", title="Base Plate, Arty A7 and Raspberry Pi",
                subtitle="An Arty A7 in corner cups, a Pi, and the direct Raspmod between them",
                w=W, h=H, holes=holes, boxes=boxes, levels=levels, standoffs=standoffs,
                z=z, s_pi=s_pi, pi_t=pi_t, pi_t_src=pi_t_src, host_top=arty_top,
                cup_h=cup_h, arty=arty, made=made, positions=pi_positions)


# ---------------------------------------------------------------------------
# Writing it out
# ---------------------------------------------------------------------------

TEMPLATE = '''"""The two base plates: a Raspberry Pi and an FPGA board, joined by the direct Raspmod.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with pdfplumber --with cadquery python base_plates/design.py

Plate coordinates: origin at the plate's lower-left corner, X right, Y away
from the viewer, seen from above; Z up from the plate's top face.  See
design.py for how every figure is arrived at.
"""

from __future__ import annotations

from base_plates.model import Box, Plate, Standoff
from tools.schema import BoardSpec, Hole, Outline, Source

#: The stack, above the Pi's top face: see design.py.
ADAPTER_UNDER = {adapter_under}
ADAPTER_TOP = {adapter_top}
HOST_ABOVE_PI = {host_above_pi}
HOST_ROWS = {host_rows}
PLUG_ROWS = {plug_rows}
#: A corner cup's screw hole: the M3 screw cuts its own thread in it.
CUP_SCREW_HOLE = {cup_screw_hole}
EDGE_TO_PLUG_FACE = {edge_to_plug_face}
#: The Pi's PCB, measured: {pi_t_src}.
PI_PCB_T = {pi_t}
#: The Arty's PCB and its rubber feet, from Digilent's rev C STEP model.
ARTY_PCB_T = {arty_t}
ARTY_FEET_H = {arty_feet_h}
ARTY_FEET_DIA = {arty_feet_dia}
ARTY_FEET = {arty_feet}
#: The adapter's footprint over the Pi, in the Pi's frame: what has to be
#: no taller than ADAPTER_UNDER there.
ADAPTER_OVER_PI = {adapter_over_pi}

PLATES = {{
{plates}
}}
'''

PLATE_TEMPLATE = '''    {key!r}: Plate(
        key={key!r},
        title={title!r},
        subtitle={subtitle!r},
        spec=BoardSpec(
            key={stem!r},
            title={title!r},
            subtitle={subtitle!r},
            family="baseplate",
            outline=Outline(width={w}, height={h}, corner_radius=4.0, thickness={t}),
            holes=(
{holes}
            ),
            sources=(
{sources}
            ),
            notes=(
{notes}
            ),
        ),
        boxes=(
{boxes}
        ),
        standoffs=(
{standoffs}
        ),
        levels=(
{levels}
        ),
        residual={residual},
        fits={fits!r},
        excluded={excluded!r},
        pi_positions={positions!r},
        made={made!r},
    ),
'''


def render_plate(p: dict, fits, excluded, sources, notes) -> str:
    holes = []
    counts: dict[str, int] = {}
    for x, y, dia, prefix, what in p["holes"]:
        counts[prefix] = counts.get(prefix, 0) + 1
        holes.append(f'                Hole(x={x}, y={y}, dia={dia}, label={prefix + str(counts[prefix])!r}, '
                     f'kind={prefix.lower().rstrip("ab")!r}),  # {what}')
    boxes = []
    for b in p["boxes"]:
        kind, label, x0, x1, y0, y1, z0, z1, rows = b[:9]
        pos = b[9] if len(b) > 9 else ""
        boxes.append(f"            Box({kind!r}, {label!r}, {x0}, {x1}, {y0}, {y1}, "
                     f"{round(z0, 2)}, {round(z1, 2)}, {rows!r}, {pos!r}),")
    standoffs = "\n".join(f"            Standoff({q}, {w!r}, {h!r})," for q, w, h in p["standoffs"])
    levels = "\n".join(f"            ({n!r}, {v!r})," for n, v in p["levels"])
    return PLATE_TEMPLATE.format(
        key=p["key"], stem=p["key"], title=p["title"], subtitle=p["subtitle"],
        w=p["w"], h=p["h"], t=PLATE_T, holes="\n".join(holes),
        sources="\n".join(f"                Source(label={l!r},\n                       ref={r!r},\n"
                          f"                       note={n!r})," for l, r, n in sources),
        notes="\n".join(f"                {n!r}," for n in notes),
        boxes="\n".join(boxes), standoffs=standoffs, levels=levels,
        residual=p["z"]["residual"], fits=tuple(fits), excluded=tuple(excluded),
        positions=tuple(p["positions"]), made=tuple(p["made"]))


def main() -> None:
    pi_t, pi_t_src = pi_thickness()
    arty = arty_from_step()
    arty["feet"] = dxf_feet(arty)
    fits, excluded = which_pis_fit()
    tt = tt_plate(pi_t, pi_t_src)
    ar = arty_plate(pi_t, pi_t_src, arty)
    adapter_name = drawing_name("accessories", "raspmod-direct")

    common_sources = [
        ("Adapter", f"accessories/raspmod_direct.py, {adapter_name}",
         "outline, plugs and socket pin 1"),
        ("Raspberry Pi", "raspberry_pi/boards.py",
         f"outline, holes and header; the PCB {pi_t} thick is not published and is "
         f"{pi_t_src}"),
        HOST_SOCKET_SRC, PLUG_SRC, SOCKET_SRC, PI_HEADER_SRC,
    ]
    # The notes say what the tables and the dimensions cannot: why each
    # height is what it is, which way round the Pi goes, and what is assumed.
    # The arithmetic behind the heights is in base_plates/README.md.
    fit_note = (f"FITS a {' or a '.join(fits)}. NOT a "
                + " or a ".join(m for m, _ in excluded)
                + f": their {excluded[0][1].split(',')[0]} is under the adapter.")
    plan_note = ("The adapter's pin 1 sits on the Pi's pin 1, which turns it a half turn to the "
                 "Pi: its pin-1 end is over the Pi's SD-card end. Push the plugs home until their "
                 f"faces meet the hosts', {EDGE_TO_PLUG_FACE} behind the adapter's edge.")
    mirror_note = (f"DO NOT BUILD {adapter_name} AS DRAWN: its pin mapping is mirrored, plug pin 1 "
                   "on host pin 6. Its copper is to be re-routed first; this plate does not change.")
    tt_notes = [
        f"{drawing_name('mounting-plate', PLATE.key)} lies flat on this plate, screwed down "
        f"through its six M4 fixings into the tapped holes; the demoboard stands on it on its "
        f"{STANDOFF_HEIGHT:g} mm standoffs as that sheet says.",
        f"The Pi stands on M2.5 x {tt['s_pi'] - WASHER:g} standoffs over 0.5 washers, screwed "
        f"from below, countersunk; the plug rows then meet the host rows to "
        f"{tt['z']['residual']:+.2f}.",
        plan_note,
        fit_note,
        mirror_note,
    ]
    arty_notes = [
        "The Arty has no mounting holes: it stands on its rubber feet in four printed corner "
        f"cups, see DETAIL B, screwed from below, countersunk, the M3 screw cutting its own "
        f"thread in the cup.",
        f"The Pi stands on M2.5 x {ar['s_pi']:g} standoffs, the shortest usual, screwed from "
        f"below, countersunk; the cups' height follows, and the plug rows meet the host rows "
        f"to {ar['z']['residual']:+.2f}.",
        "TWO POSITIONS: holes PIA1-4 put the Pi where the plugs go into JA, JB and JC; PIB1-4 "
        "where they go into JB, JC and JD. Use one set.",
        plan_note,
        fit_note,
        "ASSUMED: the Arty's Pmod sockets stand on 3.3 mm legs like the demoboard's. Digilent "
        "name no part, and their STEP models a socket as a plain box. If the body sits on the "
        f"board instead, the rows are 3.26 lower: make the cups 3.26 taller, "
        f"{ar['cup_h'] + 3.26:.2f} under the foot.",
        mirror_note,
    ]
    tt_sources = common_sources + [
        ("TT mounting plate", "tinytapeout/mounting_plate/plate.py",
         "outline, the six M4 fixings, the hosts, the 8 mm standoff"),
    ]
    arty_sources = common_sources + [
        ("Arty A7", "fpga/boards.py", "outline and the four hosts; no mounting holes"),
        ("Arty rev C STEP", "https://digilent.com/reference/_media/reference/programmable-logic/arty/arty_revc_cad.zip",
         f"board {arty['thickness']} thick; feet {arty['feet_h']} tall, {arty['feet_dia']} "
         "across, 5.0 from each corner"),
    ]
    text = TEMPLATE.format(
        adapter_under=ADAPTER_UNDER, adapter_top=ADAPTER_TOP, host_above_pi=HOST_ABOVE_PI,
        host_rows=HOST_ROWS, plug_rows=PLUG_ROWS, edge_to_plug_face=EDGE_TO_PLUG_FACE,
        cup_screw_hole=CUP_SCREW_HOLE,
        pi_t=pi_t, pi_t_src=pi_t_src, arty_t=arty["thickness"], arty_feet_h=arty["feet_h"],
        arty_feet_dia=arty["feet_dia"], arty_feet=tuple(arty["feet"]),
        adapter_over_pi=adapter_over_pi(),
        plates=render_plate(tt, fits, excluded, tt_sources, tt_notes)
        + render_plate(ar, fits, excluded, arty_sources, arty_notes))
    OUT.write_text(text)
    for p in (tt, ar):
        print(f"{p['key']:8s} {p['w']:g} x {p['h']:g} mm, {len(p['holes'])} holes, "
              f"Pi on {p['s_pi']:g}, host top {p['host_top']:.2f}, residual {p['z']['residual']:+.2f}")
    print(f"Pi PCB {pi_t} ({pi_t_src}); Arty {arty['thickness']} on {arty['feet_h']} feet; "
          f"fits {fits}")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
