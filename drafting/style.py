"""Drawing style: line weights, text sizes and text metrics.

Sheet units are millimetres throughout.  The SVG is emitted with a viewBox in
millimetres and a physical width/height in millimetres, so 1 user unit is 1 mm
on paper and every weight below is a real pen width.

Weights and text heights follow ISO 128 / ISO 3098 practice: two line groups a
factor of two apart, and text no smaller than 2.5 mm so it survives printing.
"""

from __future__ import annotations

import functools

from PIL import ImageFont

# --- fonts -----------------------------------------------------------------

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_FILES = {
    ("condensed", False): f"{FONT_DIR}/DejaVuSansCondensed.ttf",
    ("condensed", True): f"{FONT_DIR}/DejaVuSansCondensed-Bold.ttf",
    ("sans", False): f"{FONT_DIR}/DejaVuSans.ttf",
    ("sans", True): f"{FONT_DIR}/DejaVuSans-Bold.ttf",
}
FONT_FAMILY = {
    "condensed": "DejaVu Sans Condensed, DejaVu Sans, Liberation Sans, sans-serif",
    "sans": "DejaVu Sans, Liberation Sans, sans-serif",
}

_MEASURE_PX = 200.0     # measure at a large size, then scale, for precision

#: Cap height of the DejaVu faces, as a fraction of the em.  Measured, not
#: assumed: ``ImageFont.getbbox("H")`` gives 0.7290 for all four faces used.
#:
#: This matters because ISO 3098 specifies lettering by *character height*, the
#: height of a capital, while a font size is the em.  Setting font-size to 2.5
#: gives a 1.82 mm capital, well under the 2.5 mm floor, so every text size in
#: this module is a cap height and is converted to an em on the way out.
CAP_RATIO = 0.7290
DESCENDER_RATIO = 0.2360    # em below the baseline


def em(cap_height: float) -> float:
    """Font size, in millimetres, that gives *cap_height* millimetre capitals."""
    return cap_height / CAP_RATIO


@functools.lru_cache(maxsize=8)
def _font(face: str, bold: bool):
    return ImageFont.truetype(FONT_FILES[(face, bold)], int(_MEASURE_PX))


@functools.lru_cache(maxsize=8192)
def text_width(text: str, cap_height: float, face: str = "condensed",
               bold: bool = False) -> float:
    """Width of *text* in millimetres when set to *cap_height* millimetre caps.

    Real metrics matter here: the layout code packs tables and dimension text
    into fixed columns, and guessing at an average character width is how
    labels end up overlapping.
    """
    if not text:
        return 0.0
    f = _font(face, bold)
    return f.getlength(text) * em(cap_height) / _MEASURE_PX


def text_height(cap_height: float) -> float:
    """Height above the baseline, i.e. the cap height itself."""
    return cap_height


def descender(cap_height: float) -> float:
    return em(cap_height) * DESCENDER_RATIO


def line_pitch(cap_height: float) -> float:
    """Baseline-to-baseline spacing for running text."""
    return em(cap_height) * 1.32


# --- line weights (mm) -----------------------------------------------------

W_OUTLINE = 0.50        # visible edges of the part
W_HIDDEN = 0.25         # hidden detail
W_THIN = 0.25           # dimension, extension, leader, hatching
W_CENTRE = 0.25         # centre lines
W_FRAME = 0.70          # sheet frame
W_TABLE = 0.25
W_TABLE_HEAVY = 0.40
W_COMPONENT = 0.35      # component body outlines on the board
W_PHANTOM = 0.25        # adjacent parts, drawn as phantom outlines

# --- line types (ISO 128-2 / ISO 128-24), as SVG dash arrays in mm ----------
#
# Only three broken line types appear on these sheets, and each carries exactly
# one meaning.  They are named here rather than written out at each call site,
# because a chain-dot and a chain-double-dot look nearly alike at A3 and had
# drifted apart into six slightly different hand-written patterns.
#
#   type G, long-dash dotted  -> centre lines and axes of symmetry
#   type K, long-dash double-dotted -> outlines of adjacent parts, envelopes
#                                      and keep-out zones: things that are not
#                                      features of the part being drawn
#   type F, dashed            -> hidden detail, and parts deliberately not
#                                fitted

D_CENTRE = "3.2,1.2,0.6,1.2"
D_PHANTOM = "6.0,1.4,0.7,1.4,0.7,1.4"
D_HIDDEN = "2.2,1.4"

# --- text sizes (mm of CAP HEIGHT, per ISO 3098) ---------------------------
#
# 2.5 mm is the floor for a drawing meant to be read at A3.  Nothing here goes
# below it; T_TINY is that floor, not something smaller.

T_MIN = 2.5             # ISO 3098 floor
T_DIM = 2.5             # dimension values
T_LABEL = 2.5           # balloons, feature labels
T_NOTE = 2.5            # notes
T_TABLE = 2.5
T_TABLE_HEAD = 2.5
T_TINY = 2.5
T_SUBHEAD = 3.5
T_TITLE = 5.0
T_SHEET_TITLE = 6.0

#: The ISO 3098 preferred lettering heights, largest first.  Anything that has
#: to shrink to fit steps down this ladder rather than to an arbitrary size.
TEXT_LADDER = (10.0, 7.0, 5.0, 3.5, 2.5)

# --- dimension geometry (mm) ----------------------------------------------

ARROW_LEN = 3.0
ARROW_HALF_WIDTH = 0.9
EXT_GAP = 1.2           # gap between the feature and the start of an extension line
EXT_OVER = 2.0          # how far an extension line runs past the dimension line
DIM_TEXT_GAP = 0.9      # gap between dimension line and its text
DIM_STEP = 8.0          # spacing between stacked dimension lines
CENTRE_OVER = 1.6       # centre-mark overshoot past a hole

# --- colours ---------------------------------------------------------------
#
# Printed drawings are black on white.  Colour is used only to separate
# annotation layers on screen, and every colour here stays dark enough to
# photocopy and to read on a projector.

C_LINE = "#000000"
C_THIN = "#1a1a1a"
C_DIM = "#004c99"       # dimensions and their text
C_NOTE = "#000000"
C_COMPONENT = "#333333"
C_HIGHLIGHT = "#a00000"  # the features a given sheet is about
C_PHANTOM = "#7a7a7a"
C_FILL_HOLE = "#ffffff"
C_FILL_LIGHT = "#f0f0f0"
C_FILL_TABLE_HEAD = "#e6e6e6"

# --- sheet -----------------------------------------------------------------

SHEET_SIZES = {
    "A4": (297.0, 210.0),
    "A3": (420.0, 297.0),
    "A2": (594.0, 420.0),
}
SHEET_MARGIN = 10.0
