#!/usr/bin/env python3
"""Check ``v1.py``, the hand-written Camera Module v1.3, against its sources.

``boards.py`` is generated, so a transcription error in it fails the
extraction.  ``v1.py`` is typed in, so this does for it what the extractor
does for the others, in three parts:

* **Quotes.**  Every figure and phrase ``v1.py`` attributes to a source is
  looked for in the cached copy of that source, as text: Gert van Loo's
  sheet through its Scribd text layer, Raspberry Pi Spy's diagram through
  its PDF text, Arducam's drawing likewise, and the forum thread, the
  article and Raspberry Pi's documentation as pages.  That a figure is on
  the source is what can be checked; what it dimensions is read off the
  drawing by eye, and ``v1.py`` says so beside each one.
* **Arithmetic.**  The positions in ``v1.py`` are worked out from those
  printed figures again here, and the scaled ones are measured again by
  ``measure_cm1.py``, and each has to come out as ``v1.py`` has it.
* **The independent checks**, which are what the error bars rest on: the
  hole centres Gert measured by hand in 2013 against the ones Raspberry
  Pi's own Camera Module 2 and 3 drawings give, held to the 0.03 the sheet
  quotes.  Then two sanity checks, which a gross error would fail and a
  fine one would not: his three heights added up against Raspberry Pi's
  "around 9 mm", and Raspberry Pi Spy's measurement against his.

Needs the sources in ``tmp/rpi``: ``tools/fetch_raspberry_pi_camera.sh``.

Run: uv run --no-project --with pdfplumber --with pillow --with numpy \\
         python raspberry_pi_camera/verify.py
"""

from __future__ import annotations

import html
import math
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from raspberry_pi_camera import measure_cm1, v1  # noqa: E402
from raspberry_pi_camera.boards import BOARDS  # noqa: E402

CACHE = ROOT / "tmp" / "rpi" / "cm1"

#: What each source is quoted as saying.  Figures are matched whole: "2"
#: has to be a text span of its own on Gert's sheet, not the 2 in "21.85".
GVL_FIGURES = ("23.9", "25", "21.85", "9.35", "2", "23", "5.1", "8", "8.0",
               "5.2", "0.95", "5.6", "2.8", "1.27", "16.2", "ø")
GVL_PHRASES = ("Raspberry-Pi Camera module", "Gert van Loo, 21 May 2013",
               "Best effort, manually measured, no guarantees!",
               "Rev 1.0 : 21 May 2013, All sizes in mm, scale 5:1")
THREAD_PHRASES = (
    "hand measured, accuracy about 0.05 mm no guarantees",
    "from the drawing it would appear that the lens axis is just off line "
    "from the adjacent mounting holes",
    "the camera housing itself is stuck to the board with a patch of "
    "adhesive and comes off fairly easily",
)
SPY_FIGURES = ("25mm", "24mm", "21mm", "12.5mm", "2mm", "~2mm hole", "8mm",
               "8.5mm", "5.5mm", "9.5mm", "16mm")
SPY_PHRASES = ("The PCB is 25x24mm and is approximately 1mm thick.",
               "The distance between the reverse side of the PCB and the "
               "face of the camera is 6mm.",
               "The mounting holes will accept a 2mm machine screw "
               "according to various posts and photos I have seen.",
               "a set of plastic calipers")
B0033_FIGURES = ("25.00 mm", "24.00 mm", "21.00 mm", "12.50 mm", "2.00 mm",
                 "8.00 mm", "10.25 mm", "R=1.00mm")
B0033_PHRASES = ("fully compatible with official one",)
RPI_SIZE = "Around 25 × 24 × 9 mm"

#: The figure the sheet quotes for the hole centres, and so the limit held.
HOLE_PATTERN_LIMIT = 0.03

#: A sanity limit, not a tolerance.  Raspberry Pi's "Around 25 × 24 × 9 mm"
#: is given for the Camera Module 2 as well, and the same table's heights for
#: the Camera Module 3, 11.5 and 12.4, are 0.2 and 0.4 from the 11.3 and 12
#: its own drawings print; a figure that round is good to half a millimetre.
HEIGHT_LIMIT = 0.5

failures: list[str] = []


def check(ok: bool, what: str) -> None:
    print(("  ok    " if ok else "  FAIL  ") + what)
    if not ok:
        failures.append(what)


def need(name: str) -> Path:
    path = CACHE / name
    if not path.exists():
        raise SystemExit(f"{path} is missing: run "
                         "tools/fetch_raspberry_pi_camera.sh")
    return path


def page_text(name: str) -> str:
    raw = need(name).read_text(encoding="utf-8", errors="replace")
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", text)


def pdf_strings(name: str) -> list[str]:
    """Each run of text the PDF draws as one piece, in drawing order.

    Not ``extract_text``: both drawings letter their dimensions along the
    dimension lines, some upright and some turned, and one of Raspberry Pi
    Spy's is turned 88.6 degrees rather than 90, which pdfplumber reads as
    upright and scatters a character to a line.  A string here is a run of
    characters drawn one after another with the same rotation, each within a
    character or so of the last, which is what a text object in the file is.
    """
    out: list[str] = []
    with pdfplumber.open(need(name)) as pdf:
        for page in pdf.pages:
            cur, prev = "", None
            for c in page.chars:
                rot = tuple(round(v, 3) for v in c["matrix"][:4])
                centre = ((c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2)
                size = max(c["x1"] - c["x0"], c["bottom"] - c["top"])
                if prev and (rot != prev[0] or math.dist(centre, prev[1])
                             > 1.6 * max(size, prev[2])):
                    out.append(cur.strip())
                    cur = ""
                cur += c["text"]
                prev = (rot, centre, size)
            out.append(cur.strip())
    return out


def quotes() -> None:
    print("quotes")
    raw = need("scribd-page1.jsonp").read_text(encoding="utf-8")
    spans = [html.unescape(s).strip() for s in
             re.findall(r"<span[^>]*>([^<]*)</span>", raw.replace('\\"', '"'))]
    for fig in GVL_FIGURES:
        check(fig in spans, f"Gert van Loo's sheet prints {fig!r}")
    for phrase in GVL_PHRASES:
        check(any(s.startswith(phrase) for s in spans)
              or phrase in " ".join(spans),
              f"Gert van Loo's sheet says {phrase!r}")

    thread = page_text("forum-t44466.html")
    check("by Gert van Loo" in thread and "Mechanical data" in thread,
          "the forum thread is Gert van Loo's 'Mechanical data'")
    for phrase in THREAD_PHRASES:
        check(phrase in thread, f"the thread says {phrase!r}")

    spy = pdf_strings("rpispy-diagram.pdf")
    for fig in SPY_FIGURES:
        check(fig in spy, f"Raspberry Pi Spy's diagram prints {fig!r}")
    check("Raspberry Pi Camera" in spy and "Rev 1.3" in spy,
          "Raspberry Pi Spy's diagram is of a board lettered "
          "'Raspberry Pi Camera', 'Rev 1.3'")
    article = page_text("rpispy-article.html")
    for phrase in SPY_PHRASES:
        check(phrase in article, f"Raspberry Pi Spy says {phrase!r}")

    b0033 = pdf_strings("uctronics-B0033.pdf")
    for fig in B0033_FIGURES:
        check(fig in b0033, f"Arducam's B0033 drawing prints {fig!r}")
    prose = " ".join(b0033)
    for phrase in B0033_PHRASES:
        check(phrase in prose, f"Arducam say {phrase!r}")

    # The documentation's product table: the Size row's first cell has to be
    # the Camera Module 1 column's, so the columns are read off in order.
    docs = page_text("camera.html")
    table = docs[docs.index("Camera Module 1"):]
    header = table[:table.index("Size")]
    size_row = table[table.index("Size"):table.index("Weight")]
    first_col = header.split("Camera Module")[1].strip()
    first_size = size_row[len("Size"):].strip()
    check(first_col.startswith("1") and first_size.startswith(RPI_SIZE),
          f"Raspberry Pi's table gives Camera Module 1 {RPI_SIZE!r}")


def arithmetic() -> None:
    print("arithmetic")
    h = 23.9
    check(v1.BOARD_WIDTH == 25.0 and v1.BOARD_HEIGHT == h
          and v1.BOARD_THICKNESS == 0.95 and v1.HOLE_DIA == 2.0
          and v1.LENS_TOP_Z == 5.2 and v1.FFC_CABLE_WIDTH == 16.2,
          "outline, thickness, hole size, lens height and cable are the "
          "sheet's 25, 23.9, 0.95, ø2, 5.2 and 16.2")
    want = {"MT1": (2.0, h - 21.85), "MT2": (23.0, h - 21.85),
            "MT3": (2.0, h - 9.35), "MT4": (23.0, h - 9.35)}
    for label, (x, y) in want.items():
        gx, gy = v1.HOLES[label]
        check(math.isclose(gx, x, abs_tol=0.005)
              and math.isclose(gy, y, abs_tol=0.005),
              f"{label} at ({gx}, {gy}) is 21.85 or 9.35 from the connector "
              "edge and 2 or 23 from the lower edge")
    x0, y0, x1, y1 = v1.LENS
    check(math.isclose(y1, h - 5.1, abs_tol=0.005)
          and math.isclose(y1 - y0, 8.0, abs_tol=0.005)
          and math.isclose(x0, 8.5, abs_tol=0.005)
          and math.isclose(x1 - x0, 8.0, abs_tol=0.005),
          "lens module is 8 square, 5.1 from the connector edge and 8.5 "
          "from each side")
    check(math.isclose(v1.FFC[1], h - 5.6, abs_tol=0.005)
          and math.isclose(v1.FFC_BODY[1], h - 5.6, abs_tol=0.005)
          and math.isclose(v1.FFC_BOTTOM_Z, -0.95 - 2.8, abs_tol=0.005)
          and math.isclose(v1.FFC_CABLE_Z, -0.95 - 1.27, abs_tol=0.005),
          "connector is 5.6 deep and 2.8 below the board, the cable's upper "
          "face 1.27 below")

    m = measure_cm1.measure(need("scribd-page1-original.jpg"))
    print(f"  (measure_cm1: worst residual {m['worst']:.2f} over the "
          "printed figures it checks)")
    check(m["worst"] + 0.05 <= v1.SCALED_TOL,
          f"SCALED_TOL {v1.SCALED_TOL} covers the worst residual "
          f"{m['worst']:.2f} and Gert's own 0.05")
    for name, box, (c0, c1) in (
            ("connector envelope", v1.FFC, m["connector_face_v"]),
            ("connector body", v1.FFC_BODY, m["connector_v"]),
            ("cable", (v1.FFC_CABLE[0], 0, v1.FFC_CABLE[1]), m["cable_v"])):
        check(math.isclose(box[0], round(c0, 2), abs_tol=0.005)
              and math.isclose(box[2], round(c1, 2), abs_tol=0.005),
              f"{name} along the edge is the scaled {c0:.2f} to {c1:.2f}")
    t0, t1 = m["tail_u"]
    check(math.isclose(v1.TAIL[1], round(h - t1, 2), abs_tol=0.005),
          f"flex tail ends the scaled {h - t1:.2f} from the lower edge")
    check(math.isclose(v1.TAIL_TOP_Z, round(m["tail_height"], 2),
                       abs_tol=0.005),
          f"flex tail stands the scaled {m['tail_height']:.2f}")
    steps = m["lens_profile"]
    check(all(math.isclose(z, round(sz, 2), abs_tol=0.005)
              for (z, _, _), (sz, _) in zip(v1.LENS_PROFILE[:2], steps[::-1]))
          and abs(v1.LENS_PROFILE[1][1] - m["barrel_dia"]) <= v1.SCALED_TOL
          and abs(v1.LENS_PROFILE[1][1] - steps[1][1]) <= v1.SCALED_TOL
          and abs(v1.LENS_PROFILE[2][1] - steps[0][1]) <= v1.SCALED_TOL,
          "lens stack steps are the scaled ones")


def independent() -> None:
    print("independent checks")
    mine = v1.HOLES
    for key in ("cm2", "cm3"):
        spec = BOARDS[key]
        theirs = {h.label: (h.x, h.y) for h in spec.holes}
        worst = 0.0
        for label, (x, y) in mine.items():
            tx, ty = theirs[label]
            # From the connector edge, which is where both boards are
            # measured from: the Camera Module 2 and 3 boards are 0.04
            # shorter, and the difference is all at the far edge.
            worst = max(worst, abs(x - tx),
                        abs((v1.BOARD_HEIGHT - y)
                            - (spec.outline.height - ty)))
        check(worst <= HOLE_PATTERN_LIMIT,
              f"hole centres agree with {spec.title}'s drawing to "
              f"{worst:.3f}, from the connector edge (limit "
              f"{HOLE_PATTERN_LIMIT})")
    total = v1.OVERALL_HEIGHT
    check(abs(total - 9.0) <= HEIGHT_LIMIT,
          f"lens {v1.TOP_Z:.2f} + board {v1.BOARD_THICKNESS:.2f} + connector "
          f"{-v1.BOTTOM_Z - v1.BOARD_THICKNESS:.2f} = {total:.2f}, against "
          f"Raspberry Pi's 'around 9' (limit {HEIGHT_LIMIT})")
    # Raspberry Pi Spy, measured with calipers, to the half millimetre.
    spy_back_to_face = v1.LENS_TOP_Z + v1.BOARD_THICKNESS
    check(abs(spy_back_to_face - 6.0) <= 0.25,
          f"board underside to lens face {spy_back_to_face:.2f}, against "
          "Raspberry Pi Spy's 6mm")
    check(math.isclose(v1.HOLES["MT3"][1] - v1.HOLES["MT1"][1], 12.5)
          and math.isclose(v1.HOLES["MT2"][0] - v1.HOLES["MT1"][0], 21.0),
          "hole rectangle is Raspberry Pi Spy's 21 x 12.5")
    # Consistency, not an independent check: LENS_TOL is made from this
    # spread, so this only holds v1.py to its own arithmetic.  Raspberry Pi
    # Spy reads to the half millimetre, so its 5.5 may be a quarter off.
    spy_lens, spy_step = 5.5, 0.25
    gvl_lens = v1.BOARD_HEIGHT - v1.LENS[3]
    worst = round(abs(spy_lens - gvl_lens) + spy_step, 2)
    check(worst <= v1.LENS_TOL,
          f"lens module {gvl_lens:.2f} from the connector edge, Raspberry Pi "
          f"Spy's {spy_lens} to the half millimetre: up to {worst:.2f} apart, "
          f"which LENS_TOL {v1.LENS_TOL} covers (consistency)")
    # For information, not held to anything: a different board's connector.
    print(f"  info  connector body {v1.FFC_BODY[2] - v1.FFC_BODY[0]:.2f} and "
          f"envelope {v1.FFC[2] - v1.FFC[0]:.2f} along the edge; the Camera "
          "Module 2's are 19.61 and 20.88 on Raspberry Pi's drawing")


def main() -> int:
    quotes()
    arithmetic()
    independent()
    if failures:
        print(f"\nverify: {len(failures)} check(s) failed")
        return 1
    print("\nverify: v1.py agrees with its sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
