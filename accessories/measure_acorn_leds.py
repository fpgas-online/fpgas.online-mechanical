#!/usr/bin/env python3
"""Measure where the SQRL Acorn CLE-215+'s LEDs are, from SQRL's photographs.

SQRL published no mechanical drawing of the Acorn and their site is gone, and
no board file for it has ever been released.  What the Internet Archive does
still have is the banner off SQRL's own Acorn page: a product photograph of
a CLE-215 and a CLE-215+ lying side by side, taken from not far off square
on and cut out of its background, at about fifteen pixels to the millimetre.

    https://web.archive.org/web/20190928032642id_/
        http://squirrelsresearch.com/images/acornBanner@2x.png

``tools/fetch_acorn.sh`` fetches it, with the photographs and the schematic
that corroborate it, none of which is measured.  Both cards carry the same
layout and the same silkscreen at the far end, which is the end a camera
over the card has to see: four LEDs silkscreened A1 to A4 in a column on one
side of the retention screw's half-moon, and a fifth, silkscreened PWR, on
the other.  The two cards are two photographs from one shoot, not two
independent measurements of the card, so the spread between them is
one term of the error bar, not the whole of it.

The fit, per card:

* The card's own outline is found where nothing stands in front of it -- the
  heatsink overhangs one long edge, its blower's cable loop hangs past the
  other, and the gold finger strip is narrower than the card -- and a
  homography takes its corners onto the 80 x 23 mm rectangle ``parts.py``
  draws: the M.2 specification's Type 2280 length and SQRL's "one millimeter
  wider" than its 22.  The frame is the card's own, seen from the component
  side: X from the mating edge towards the far end, Y across it.
* Each LED is read by eye as the extent of its light body against the black
  board, off the gridded views ``--grids`` writes, and the readings are
  recorded below, as the Orange Pi PC's connectors are.  An automatic reading
  of the same bodies, half way from the board to the body, is the check on
  them.  The bodies stand a fraction of a millimetre off the board, which at
  the photographs' lean moves them by a tenth or two; that is inside the
  error bar, and not corrected.
* Everything is then put relative to the half-moon's centre, which is what
  locates the card across the HAT: the retention screw goes through it, and
  the screw is on the HAT's M.2 axis.  A position along the card is from the
  mating edge, which is the HAT's connector datum.

Which side is which is geometry, not a reading.  A card seated component side
up with its mating edge towards -X is the card seen in these photographs,
turned in its own plane and not over, so +Y here is +Y in the Pi's frame.
The M-key notch shows it the right way round: the specification puts key M at
pins 59 to 66, the pin 75 end of the finger row, and in the Pi's frame that
is the +Y side, which is where the photographs have it.

Checks, none of them used in the fit:

* the photographed aspect, which for a card seen square on is 80 x 23 and
  otherwise says how far the camera leaned -- the homography takes the lean
  out, so this is reported, not charged;
* the finger pitch across the long pin group, which the specification fixes
  at 0.50 mm: it checks the scale across the card, which is the direction the
  LED column runs in;
* the half-moon's cutout, 3.50 mm across in the specification, which checks
  the same scale again at the LEDs' own end of the card -- though SQRL's
  retoucher painted the cutout in, so its edge is the plating's;
* the two cards against each other, and the readings by eye against the
  automatic ones.

The error bar is the worst of the two scale checks, applied at the LED
furthest from the half-moon, plus the larger of the two cards' spread and the
readings' disagreement with the automatic ones.

Run: uv run --no-project --with numpy --with opencv-python-headless python \\
         accessories/measure_acorn_leds.py [--grids tmp/acorn-leds]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from accessories.parts import (ACORN_LED_READINGS,  # noqa: E402
                               ACORN_LED_TOL, ACORN_LENGTH, ACORN_WIDTH,
                               POE_M2_AXIS_Y, POE_M2_DATUM_X)
from tools.photo_frame import (Frame, fit_board, fit_circle,  # noqa: E402
                               grid_image, photographed_height)

SRC = ROOT / "tmp" / "src" / "acorn-cle-215"
BANNER = "sqrl-acornBanner@2x.png"

#: The card, in its own frame, at 40 pixels to the millimetre.
FRAME = Frame(ACORN_LENGTH, ACORN_WIDTH, px_per_mm=40.0, margin=4.0)

#: Each card in the banner: roughly where its corners are, image pixels, in
#: the order photo_frame wants them -- the mating edge's +Y corner first,
#: then clockwise seen from the component side.
CARDS = {
    "CLE-215+": [(309, 876), (1173, 42), (1445, 323), (581, 1158)],
    "CLE-215": [(34, 1306), (1204, 1029), (1295, 1409), (124, 1687)],
}

#: Where each card edge is not the card's own, card frame, millimetres: the
#: heatsink overhangs +Y from X 11 on, the blower's cable loop hangs past -Y
#: from X 60, the half-moon is in the far end, and at the mating edge the
#: finger strip is narrower than the card and notched for the key.
HIDDEN = {"top": [(0.0, 5.0), (11.0, 64.0)],
          "bottom": [(0.0, 5.0), (60.0, 80.0)],
          "right": [(7.0, 16.0)],
          "left": [(0.0, 2.5), (14.0, 18.0), (20.5, 23.0)]}
CORNER = 1.0

#: PCI Express M.2 Specification Revision 1.0: the finger pitch on each face
#: (figure 16, "0.50 TYP. PITCH"), the retention cutout ("Ø 3.50±0.08") and
#: key M's pins (table 42, "59-66").
SPEC_PITCH = 0.50
SPEC_CUTOUT = 3.50

#: The five LEDs, silkscreen legend first, and roughly where each is in the
#: card frame.  Only where to look.
LEDS = {"A1": (78.5, 22.2), "A2": (78.5, 19.9), "A3": (78.5, 17.6),
        "A4": (78.5, 15.2), "PWR": (78.5, 8.3)}

#: The same five, read by eye off the gridded views at 120 pixels to the
#: millimetre: x0, y0, x1, y1 in the card frame.  The readings adopted;
#: the profile readings in `led_extent` are the check on them.
READ_BY_EYE = {
    "CLE-215": {"A1": (77.38, 21.88, 79.67, 22.54),
                "A2": (77.38, 19.46, 79.63, 20.25),
                "A3": (77.38, 17.21, 79.63, 17.92),
                "A4": (77.38, 14.83, 79.63, 15.54),
                "PWR": (77.42, 8.04, 79.63, 8.62)},
    "CLE-215+": {"A1": (77.40, 21.88, 79.63, 22.50),
                 "A2": (77.40, 19.57, 79.63, 20.23),
                 "A3": (77.40, 17.25, 79.63, 17.93),
                 "A4": (77.40, 14.92, 79.63, 15.63),
                 "PWR": (77.42, 8.07, 79.65, 8.83)},
}


def load(path: Path):
    """The banner, as the card silhouettes and as the photograph.

    The banner is cut out of its background, so the card's edge is where its
    alpha is, and that is cleaner than any edge in the picture: the silhouette
    is the card black on white, and the photograph is composited on white for
    reading the LEDs off.  The banner's own white panels are not card.
    """
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit(f"{path} missing: run tools/fetch_acorn.sh")
    alpha, bgr = im[..., 3], im[..., :3]
    card = (alpha > 128) & ~(bgr > 200).all(axis=2)
    sil = np.where(card[..., None], 0, 255).astype(np.uint8).repeat(3, axis=2)
    photo = bgr.copy()
    photo[alpha <= 128] = 255
    return sil, photo


def pulled_in(approx):
    """Rough corners with the -Y edge set 23/80 of the length off the +Y one.

    The rough corners are the silhouette's own bounding box, which the cable
    loop widens; the fit only looks a little way either side of them.
    """
    tl, tr, br, bl = (np.array(q, float) for q in approx)
    d = (tr - tl) / np.linalg.norm(tr - tl)
    n = np.array([-d[1], d[0]])
    if np.dot(n, bl - tl) < 0:
        n = -n
    w = np.linalg.norm(tr - tl) * FRAME.height / FRAME.width
    return [tl, tr, tr + n * w, tl + n * w]


def rectify(photo, corners):
    dst = np.float32([FRAME.to_px(*q) for q in FRAME.corners(None)])
    T = cv2.getPerspectiveTransform(np.float32(corners), dst)
    size = (int((FRAME.width + 2 * FRAME.margin) * FRAME.px_per_mm),
            int((FRAME.height + 2 * FRAME.margin) * FRAME.px_per_mm))
    return cv2.warpPerspective(photo, T, size, flags=cv2.INTER_CUBIC,
                               borderValue=(255, 255, 255))


def finger_pitch(rect, lo: float, hi: float) -> float:
    """The period of the gold fingers between *lo* and *hi* across the card.

    The fingers are gold on a black card, so red less blue picks them out;
    the period is the strongest Fourier component between 0.40 and 0.60 mm.
    """
    rb = rect[..., 2].astype(float) - rect[..., 0].astype(float)
    xa, _ = FRAME.to_px(0.6, 0.0)
    xb, _ = FRAME.to_px(1.8, 0.0)
    prof = rb[:, int(xa):int(xb)].mean(axis=1)
    ys = np.array([FRAME.to_mm(0.0, py)[1] for py in range(len(prof))])
    s = (ys > lo) & (ys < hi)
    q, yy = prof[s] - prof[s].mean(), ys[s]
    pers = np.arange(0.40, 0.60, 0.0005)
    power = [abs(np.sum(q * np.exp(-2j * np.pi * yy / p))) for p in pers]
    return float(pers[int(np.argmax(power))])


def finger_strip(sil_rect):
    """The finger strip half a millimetre in from the mating edge: where it
    starts and ends across the card, and the key notch's centre, which is
    the one gap in it with card on both sides."""
    px, _ = FRAME.to_px(0.5, 0.0)
    col = sil_rect[:, int(px), 0] <= 128
    ys = np.array([FRAME.to_mm(0.0, py)[1] for py in range(len(col))])
    runs, i = [], 0
    while i < len(col):
        if col[i]:
            j = i
            while j + 1 < len(col) and col[j + 1]:
                j += 1
            runs.append((min(ys[i], ys[j]), max(ys[i], ys[j])))
            i = j + 1
        else:
            i += 1
    # Only this card's: the banner's other card lies close by, past -Y.
    runs = sorted(r for r in runs if r[1] - r[0] > 1.0
                  and -0.5 < r[0] and r[1] < FRAME.height + 0.5)
    if len(runs) != 2:
        raise SystemExit(f"finger strip is {len(runs)} runs, wanted the two "
                         "groups either side of the key")
    return runs[0][0], runs[1][1], (runs[0][1] + runs[1][0]) / 2


def half_moon(rect):
    """The half-moon's gold: centre, pad and cutout diameters, card frame.

    The pad is gold on black and the cutout, which SQRL's retoucher painted
    in, black inside it.  The boundary points of the gold, less those along
    the cut far edge, split by distance from their first centre into the
    pad's outer edge and the cutout's, and a circle is fitted to each.
    """
    img = rect.astype(int)
    gold = ((img[..., 2] - img[..., 0] > 50) & (img[..., 2] > 110))
    x0, y0 = FRAME.to_px(76.0, 15.5)
    x1, y1 = FRAME.to_px(80.5, 7.5)
    m = np.zeros(gold.shape, np.uint8)
    m[int(y0):int(y1), int(x0):int(x1)] = gold[int(y0):int(y1), int(x0):int(x1)]
    cs, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    pts = np.vstack([c[:, 0, :] for c in cs]).astype(float)
    mm = np.array([FRAME.to_mm(px, py) for px, py in pts])
    mm = mm[mm[:, 0] < FRAME.width - 0.7]
    cx, cy, _ = fit_circle(mm)
    for _ in range(3):
        d = np.hypot(mm[:, 0] - cx, mm[:, 1] - cy)
        ox, oy, orad = fit_circle(mm[d > 2.25])
        ix, iy, irad = fit_circle(mm[d <= 2.25])
        cx, cy = ox, oy
    return dict(x=(ox + ix) / 2, y=(oy + iy) / 2, pad=2 * orad, cutout=2 * irad)


#: The window an LED is looked for in, along the card: from just clear of
#: the silkscreen polarity bar beside each one, which ends at X 77.25, to
#: just short of the card's far edge, where the paper beyond is white.
LED_X_WINDOW = (77.30, FRAME.width - 0.15)


def _run(on: np.ndarray, axis_mm: np.ndarray, start: int):
    """The run of True in *on* through index *start*, as its two ends, mm."""
    if not on[start]:
        raise SystemExit("an LED's window is not on the LED")
    i = start
    while i > 0 and on[i - 1]:
        i -= 1
    j = start
    while j < len(on) - 1 and on[j + 1]:
        j += 1
    return min(axis_mm[i], axis_mm[j]), max(axis_mm[i], axis_mm[j])


def led_extent(rect, x: float, y: float):
    """One LED's light body, x0, y0, x1, y1 in the card frame: the check.

    A pixel is body where it is brighter than half way from the board to the
    body's own brightest tenth, inside a window 0.8 mm either side of where
    the LED is, cut to the card and clear of the polarity bar.  Across the
    card, a row counts if its middle is body; along it, a column counts if
    any of the rows so found are.  That second rule is what carries the run
    across the LED's lens, which is darker than its two ends.
    """
    lum = rect.astype(float).mean(axis=2)
    xa, ya = FRAME.to_px(LED_X_WINDOW[0], min(y + 0.8, FRAME.height - 0.15))
    xb, yb = FRAME.to_px(LED_X_WINDOW[1], y - 0.8)
    win = lum[int(ya):int(yb), int(xa):int(xb)]
    base = float(np.percentile(win, 20))
    top = float(np.percentile(win, 97))
    on = win > base + (top - base) / 2
    ymm = np.array([FRAME.to_mm(0.0, py)[1] for py in range(int(ya), int(yb))])
    xmm = np.array([FRAME.to_mm(px, 0.0)[0] for px in range(int(xa), int(xb))])
    mid = on[:, len(xmm) // 3: 2 * len(xmm) // 3].mean(axis=1) > 0.3
    ylo, yhi = _run(mid, ymm, int(np.argmin(abs(ymm - y))))
    rows = (ymm >= ylo) & (ymm <= yhi)
    cols = on[rows].any(axis=0)
    xlo, xhi = _run(cols, xmm, len(xmm) // 2)
    return xlo, ylo, xhi, yhi


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grids", type=Path,
                    help="write the gridded views the readings by eye are "
                         "taken from into this directory")
    args = ap.parse_args()
    sil, photo = load(SRC / BANNER)
    print(f"image {photo.shape[1]} x {photo.shape[0]}: {SRC / BANNER}")
    print(f"frame {FRAME.width:.2f} x {FRAME.height:.2f} mm, X from the "
          "mating edge, Y across, component side up\n")

    rect, moon, leds = {}, {}, {}
    scale_err = []
    eye_diff = 0.0
    for name, approx in CARDS.items():
        corners, fits, srect = fit_board(sil, FRAME, pulled_in(approx), None,
                                         HIDDEN, CORNER)
        rect[name] = rectify(photo, corners)
        h = photographed_height(corners, FRAME.width)
        lean = math.degrees(math.acos(min(1.0, FRAME.height / h)))
        print(f"--- {name} ---")
        print("  edge rms px " + " ".join(f"{r:4.2f}" for r, _ in fits)
              + f"   aspect says {h:5.2f} wide at {FRAME.width:.0f} long: a "
              f"lean of about {lean:.0f} deg, which the fit takes out")
        f_lo, f_hi, notch = finger_strip(srect)
        side = "+Y" if notch > FRAME.height / 2 else "-Y"
        print(f"  key notch at Y {notch:5.2f}, the {side} side")
        if side != "+Y":
            raise SystemExit("the key notch is not on the +Y side: this card "
                             "is being read turned over")
        print(f"  finger strip Y {f_lo:5.2f} .. {f_hi:5.2f}, stepped in from the "
              "card edge on both sides")
        long_pitch = finger_pitch(rect[name], 1.5, 15.5)
        print(f"  finger pitch {long_pitch:.4f} mm across the long group "
              f"(specification {SPEC_PITCH:.2f}: {long_pitch / SPEC_PITCH - 1:+.1%})")
        moon[name] = half_moon(rect[name])
        m = moon[name]
        print(f"  half-moon centre ({m['x']:5.2f}, {m['y']:5.2f}), cutout "
              f"{m['cutout']:.2f} (specification {SPEC_CUTOUT:.2f}: "
              f"{m['cutout'] / SPEC_CUTOUT - 1:+.1%}), pad {m['pad']:.2f}")
        print(f"  half-moon is {m['y'] - FRAME.height / 2:+.2f} off the "
              "card's own centreline")
        scale_err += [abs(long_pitch / SPEC_PITCH - 1),
                      abs(m["cutout"] / SPEC_CUTOUT - 1)]
        leds[name] = {}
        print("  LED   by eye: X0     X1     Y0     Y1    profile, largest "
              "difference")
        for k, (x, y) in LEDS.items():
            eye = READ_BY_EYE[name][k]
            got = led_extent(rect[name], x, y)
            leds[name][k] = eye
            diff = max(abs(a - b) for a, b in zip(got, eye))
            eye_diff = max(eye_diff, diff)
            print(f"  {k:4s}   {eye[0]:6.2f} {eye[2]:6.2f} {eye[1]:6.2f} "
                  f"{eye[3]:6.2f}    {diff:4.2f}")
        print()

    # --- relative to the half-moon, and the two cards against each other ---
    print("--- X from the mating edge, Y from the half-moon's centre ---")
    rel = {}
    spread = 0.0
    for k in LEDS:
        rows = []
        for name in CARDS:
            x0, y0, x1, y1 = leds[name][k]
            m = moon[name]
            rows.append((x0, x1, y0 - m["y"], y1 - m["y"]))
        a = np.array(rows)
        mean = a.mean(axis=0)
        sp = float(np.ptp(a, axis=0).max())
        spread = max(spread, sp)
        rel[k] = mean
        print(f"  {k:4s} X {mean[0]:6.2f} .. {mean[1]:6.2f}   Y "
              f"{mean[2]:+6.2f} .. {mean[3]:+6.2f}   cards differ by {sp:.2f}")
    far = max(max(abs(v[2]), abs(v[3])) for v in rel.values())
    worst = max(scale_err)
    reading = max(spread, eye_diff)
    tol = worst * far + reading
    print(f"\n  worst scale check {worst:.1%}, at the furthest LED edge "
          f"{far:.2f} from the half-moon: {worst * far:.2f} mm")
    print(f"  plus the larger of the two cards' largest difference, "
          f"{spread:.2f}, and the readings' against the profiles, "
          f"{eye_diff:.2f}: {reading:.2f} mm")
    print(f"  Treat every LED position as +/-{math.ceil(tol * 10) / 10:.1f} mm.")

    # What parts.py carries has to be this, to the hundredth it prints.
    stale = [k for k, v in rel.items()
             if max(abs(a - b) for a, b in zip(
                 np.round(v, 2), ACORN_LED_READINGS[k])) > 0.005]
    if stale or math.ceil(tol * 10) / 10 != ACORN_LED_TOL:
        raise SystemExit("accessories/parts.py's ACORN_LED_READINGS or "
                         f"ACORN_LED_TOL differ from these: {stale}")
    print("  accessories/parts.py carries these figures and this tolerance")

    print("\n--- in the Pi's frame, on the HAT: X from the Pi's datum, Y too ---")
    print(f"  connector datum X {POE_M2_DATUM_X:.2f}, M.2 axis Y "
          f"{POE_M2_AXIS_Y:.2f} (accessories/parts.py)")
    for k, (x0, x1, dy0, dy1) in rel.items():
        print(f"  {k:4s} X {POE_M2_DATUM_X + x0:6.2f} .. {POE_M2_DATUM_X + x1:6.2f}"
              f"   Y {POE_M2_AXIS_Y + dy0:6.2f} .. {POE_M2_AXIS_Y + dy1:6.2f}")

    if args.grids:
        args.grids.mkdir(parents=True, exist_ok=True)
        for name, r in rect.items():
            stem = name.lower().replace("+", "-plus")
            for i, box in enumerate(((76.0, 14.0, 80.5, 23.5),
                                     (76.0, 6.5, 80.5, 10.5))):
                cv2.imwrite(str(args.grids / f"{stem}-{i}.png"),
                            grid_image(r, FRAME, box, zoom=3.0))
        print(f"\ngridded views written to {args.grids}")


if __name__ == "__main__":
    main()
