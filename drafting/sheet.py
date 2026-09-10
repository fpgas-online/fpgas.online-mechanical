"""Sheet furniture: frame, zone markings, title block, note blocks and tables."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import style
from .canvas import Canvas


@dataclass
class TitleBlock:
    title: str
    subtitle: str = ""
    drawing_no: str = ""
    rev: str = ""
    scale: str = "1:1"
    sheet: str = "1 OF 1"
    date: str = ""
    drawn_by: str = ""
    material: str = ""
    units: str = "mm"
    #: Kept in the title block rather than the notes, which is where a real
    #: drawing puts it and, more practically, means it can never be the note
    #: that gets trimmed when the column runs short.
    tolerance: str = "+/-0.20 edge, +/-0.10 hole pos, +/-0.08 hole dia"
    projection: str = "first angle"


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def x1(self) -> float:
        return self.x + self.w

    @property
    def y1(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def inset(self, d: float) -> "Rect":
        return Rect(self.x + d, self.y + d, self.w - 2 * d, self.h - 2 * d)


class Sheet:
    """An ISO-A sheet with a frame, zone markings and a title block.

    The usable area is split into a wide drawing area on the left and a
    narrower annotation column on the right, with the title block beneath the
    column.  Keeping tables and notes out of the drawing area is what stops
    them colliding with dimension lines.
    """

    #: Wide enough for the tables at a true 2.5 mm cap height, and no wider:
    #: the drawing area has to keep every board at 1:1, and the mounting plate
    #: at 135 mm is the widest thing that has to fit.
    COLUMN_WIDTH = 165.0
    TITLE_HEIGHT = 48.0

    def __init__(self, size: str = "A3", title: TitleBlock | None = None,
                 column_width: float | None = None):
        self.w, self.h = style.SHEET_SIZES[size]
        self.size_name = size
        self.canvas = Canvas(self.w, self.h)
        self.title = title or TitleBlock(title="")
        # Two borders, ISO 5457 style: a trim line near the paper edge and the
        # drawing frame inside it.  The strip between them carries the zone
        # markings, which is what keeps them clear of the drawing content.
        m = style.SHEET_MARGIN
        self.trim = Rect(m / 2, m / 2, self.w - m, self.h - m)
        self.frame = Rect(m + 5, m + 5, self.w - 2 * (m + 5), self.h - 2 * (m + 5))
        cw = self.COLUMN_WIDTH if column_width is None else column_width
        self.title_rect = Rect(self.frame.x1 - cw, self.frame.y, cw,
                               self.TITLE_HEIGHT)
        # A little clear of the frame at the top, so the first section heading
        # does not sit on the frame line.
        self.column = Rect(self.frame.x1 - cw, self.title_rect.y1 + 4.0,
                           cw, self.frame.y1 - self.title_rect.y1 - 7.0)
        self.area = Rect(self.frame.x, self.frame.y,
                         self.frame.w - cw - 6.0, self.frame.h)
        self._column_cursor = self.column.y1

    # -- furniture ----------------------------------------------------------

    def draw_frame(self) -> None:
        c = self.canvas
        c.rect(self.trim.x, self.trim.y, self.trim.w, self.trim.h,
               weight=style.W_THIN, colour="#888888")
        f = self.frame
        c.rect(f.x, f.y, f.w, f.h, weight=style.W_FRAME)
        self._draw_zones()

    def _draw_zones(self) -> None:
        """Zone letters down the sides and numbers along top and bottom."""
        c, f = self.canvas, self.frame
        t = self.trim
        strip = f.y - t.y
        cols = max(2, round(f.w / 70))
        rows = max(2, round(f.h / 70))
        letters = "ABCDEFGH"
        for i in range(cols):
            x0 = f.x + f.w * i / cols
            x1 = f.x + f.w * (i + 1) / cols
            if i:
                c.line(x0, t.y, x0, f.y, w=style.W_THIN, colour="#888888")
                c.line(x0, f.y1, x0, t.y1, w=style.W_THIN, colour="#888888")
            for y in (t.y + strip / 2, t.y1 - strip / 2):
                c.text((x0 + x1) / 2, y, str(cols - i), size=style.T_TINY,
                       anchor="middle", baseline="middle", colour="#666666")
        for j in range(rows):
            y0 = f.y + f.h * j / rows
            y1 = f.y + f.h * (j + 1) / rows
            if j:
                c.line(t.x, y0, f.x, y0, w=style.W_THIN, colour="#888888")
                c.line(f.x1, y0, t.x1, y0, w=style.W_THIN, colour="#888888")
            for x in (t.x + strip / 2, t.x1 - strip / 2):
                c.text(x, (y0 + y1) / 2, letters[rows - 1 - j],
                       size=style.T_TINY, anchor="middle", baseline="middle",
                       colour="#666666")

    def draw_title_block(self) -> None:
        c, r, t = self.canvas, self.title_rect, self.title
        c.rect(r.x, r.y, r.w, r.h, weight=style.W_FRAME)

        band = 15.0
        c.line(r.x, r.y1 - band, r.x1, r.y1 - band, w=style.W_TABLE_HEAVY)
        c.text(r.x + 2.5, r.y1 - band + 6.2, t.title, size=style.T_TITLE,
               face="sans", bold=True)
        if t.subtitle:
            c.text(r.x + 2.5, r.y1 - band + 1.6, t.subtitle,
                   size=style.T_LABEL, colour="#333333")

        # Two rows of narrow fields, then one full-width row for the fields
        # whose values are long enough to run out of a quarter-width cell.
        grid = [
            ("DRAWN", t.drawn_by), ("DATE", t.date), ("UNITS", t.units),
            ("SCALE", t.scale), ("SIZE", self.size_name), ("SHEET", t.sheet),
            ("DRAWING NO", t.drawing_no), ("REV", t.rev),
        ]
        wide = [("MATERIAL", t.material, 0.34),
                ("GENERAL TOLERANCE", t.tolerance, 0.66)]
        rows, cols = 3, 4
        ch = (r.h - band) / rows
        cw = r.w / cols
        for i, (label, value) in enumerate(grid):
            col, row = i % cols, i // cols
            x = r.x + col * cw
            y = r.y1 - band - (row + 1) * ch
            if col:
                c.line(x, y, x, y + ch, w=style.W_TABLE)
            if row:
                c.line(x, y + ch, x + cw, y + ch, w=style.W_TABLE)
            self._title_cell(x, y, ch, label, value)
        y = r.y
        c.line(r.x, y + ch, r.x1, y + ch, w=style.W_TABLE)
        x = r.x
        for label, value, frac in wide:
            if x > r.x:
                c.line(x, y, x, y + ch, w=style.W_TABLE)
            self._title_cell(x, y, ch, label, value)
            x += r.w * frac

    def _title_cell(self, x: float, y: float, ch: float, label: str,
                    value: str) -> None:
        c = self.canvas
        c.text(x + 1.6, y + ch - style.T_TINY - 1.0, label, size=style.T_TINY,
               colour="#666666")
        c.text(x + 1.6, y + 1.6, value or "-", size=style.T_LABEL, bold=True)

    def projection_symbol(self, x: float, y: float, scale: float = 1.0) -> None:
        """First-angle projection symbol (ISO 128), drawn as a truncated cone."""
        c = self.canvas
        s = scale
        c.text(x, y + 7.2 * s, "FIRST ANGLE PROJECTION", size=style.T_TINY,
               anchor="middle", colour="#666666")
        c.line(x - 11 * s, y + 3 * s, x + 11 * s, y + 3 * s,
               w=style.W_CENTRE, colour="#666666", dash="3,1.2,0.6,1.2")
        c.polyline([(x - 9 * s, y + 5.4 * s), (x - 1 * s, y + 4.2 * s),
                    (x - 1 * s, y + 1.8 * s), (x - 9 * s, y + 0.6 * s)],
                   close=True, w=style.W_OUTLINE)
        c.circle(x + 5.4 * s, y + 3 * s, 2.4 * s, w=style.W_OUTLINE)
        c.circle(x + 5.4 * s, y + 3 * s, 1.2 * s, w=style.W_OUTLINE)

    # -- annotation column --------------------------------------------------

    #: Right-hand gutter inside the annotation column.  Without it, a wrapped
    #: note that exactly fills the column runs up against the frame line.
    COLUMN_GUTTER = 3.0

    def column_block(self, height: float) -> Rect:
        """Reserve *height* mm at the top of the remaining annotation column."""
        top = self._column_cursor
        self._column_cursor = top - height - 4.0
        return Rect(self.column.x, top - height,
                    self.column.w - self.COLUMN_GUTTER, height)

    @property
    def column_remaining(self) -> float:
        return self._column_cursor - self.column.y

    def heading(self, rect: Rect, text: str) -> float:
        """Draw a section heading at the top of *rect*; return the y below it."""
        c = self.canvas
        c.text(rect.x, rect.y1 - style.T_SUBHEAD, text, size=style.T_SUBHEAD,
               face="sans", bold=True)
        y = rect.y1 - style.T_SUBHEAD - 1.4
        c.line(rect.x, y, rect.x1, y, w=style.W_TABLE_HEAVY)
        return y - 2.2

    #: Height a heading occupies, including its rule and the gap under it.
    HEADING_HEIGHT = style.T_SUBHEAD + 3.6

    def notes_height(self, width: float, title: str, lines: list[str],
                     size: float = style.T_NOTE, numbered: bool = True) -> float:
        """Height a note block will occupy, so a caller can reserve it exactly.

        Reserving a guessed height and then drawing whatever fits is how the
        notes ended up running through the sources heading.
        """
        indent = 5.0 if numbered else 0.0
        total = self.HEADING_HEIGHT if title else 0.0
        for line in lines:
            total += (len(wrap(line, width - indent, size))
                      * style.line_pitch(size)) + 1.0
        return total

    def notes(self, rect: Rect, title: str, lines: list[str],
              size: float = style.T_NOTE, numbered: bool = True) -> float:
        """Draw a numbered note block, wrapping to the column width."""
        c = self.canvas
        y = self.heading(rect, title) if title else rect.y1
        indent = 5.0 if numbered else 0.0
        for i, line in enumerate(lines, 1):
            wrapped = wrap(line, rect.w - indent, size)
            if numbered:
                c.text(rect.x, y - size, f"{i}.", size=size)
            for part in wrapped:
                c.text(rect.x + indent, y - size, part, size=size)
                y -= style.line_pitch(size)
            y -= 1.0
        return y

    def table_height(self, title: str, rows: int,
                     size: float = style.T_TABLE) -> float:
        """Height a table will occupy, heading included."""
        return ((self.HEADING_HEIGHT if title else 0.0)
                + (rows + 1) * style.em(size) * 1.62 + 2.0)

    def table(self, rect: Rect, title: str, headers: list[str],
              rows: list[list[str]], aligns: list[str] | None = None,
              size: float = style.T_TABLE) -> float:
        """Draw a bordered table; return the y coordinate of its bottom edge."""
        c = self.canvas
        y = self.heading(rect, title) if title else rect.y1
        ncol = len(headers)
        aligns = aligns or ["start"] * ncol
        pad = 1.8
        widths = []
        for i in range(ncol):
            cells = [headers[i]] + [r[i] for r in rows]
            widths.append(max(style.text_width(t, size, bold=(t is headers[i]))
                              for t in cells) + 2 * pad)
        total = sum(widths)
        if total > rect.w:
            # Squashing columns proportionally clips their text.  Take the
            # padding out first, and only then scale, so the damage is spread
            # across the gutters rather than the words.
            widths = [w - 2 * pad + 2 * 0.6 for w in widths]
            total = sum(widths)
            if total > rect.w:
                widths = [w * rect.w / total for w in widths]
                total = rect.w
            pad = 0.6

        rh = style.em(size) * 1.62
        top = y
        c.rect(rect.x, y - rh, total, rh, weight=style.W_TABLE,
               fill=style.C_FILL_TABLE_HEAD)
        x = rect.x
        for i, head in enumerate(headers):
            c.text(_cell_x(x, widths[i], pad, aligns[i]), y - rh + rh * 0.32,
                   head, size=size, bold=True, anchor=_anchor(aligns[i]))
            x += widths[i]
        y -= rh

        for row in rows:
            c.rect(rect.x, y - rh, total, rh, weight=style.W_TABLE)
            x = rect.x
            for i, cell in enumerate(row):
                c.text(_cell_x(x, widths[i], pad, aligns[i]), y - rh + rh * 0.32,
                       cell, size=size, anchor=_anchor(aligns[i]))
                x += widths[i]
            y -= rh
        x = rect.x
        for wdt in widths[:-1]:
            x += wdt
            c.line(x, top, x, y, w=style.W_TABLE)
        return y


def _anchor(align: str) -> str:
    return {"start": "start", "end": "end", "middle": "middle"}[align]


def _cell_x(x: float, w: float, pad: float, align: str) -> float:
    return {"start": x + pad, "end": x + w - pad, "middle": x + w / 2}[align]


def _split_long(word: str, width: float, size: float) -> list[str]:
    """Break a token too long to fit on its own line, such as a bare URL."""
    parts, cur = [], ""
    for ch in word:
        if style.text_width(cur + ch, size) > width and cur:
            parts.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        parts.append(cur)
    return parts


def wrap(text: str, width: float, size: float) -> list[str]:
    """Greedy word wrap to *width* millimetres, using real font metrics.

    Long unbreakable tokens are split rather than allowed to run past the
    column: source entries are mostly URLs, and one of them is long enough to
    reach the sheet frame.
    """
    words = []
    for word in text.split():
        if style.text_width(word, size) > width:
            words += _split_long(word, width, size)
        else:
            words.append(word)
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if style.text_width(trial, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]
