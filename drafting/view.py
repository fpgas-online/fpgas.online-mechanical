"""A scaled orthographic view: maps model millimetres onto the sheet."""

from __future__ import annotations

from dataclasses import dataclass

from .sheet import Rect

# Standard drawing scales, largest first.  A drawing is far easier to read at a
# recognised scale than at some arbitrary best fit.
STANDARD_SCALES = [
    (5, 1), (2, 1), (1, 1), (1, 2), (1, 2.5), (1, 5), (1, 10), (1, 20),
]


def scale_text(num: float, den: float) -> str:
    def clean(v):
        return f"{v:g}"
    return f"{clean(num)}:{clean(den)}"


@dataclass
class View:
    """Placement of a model-space bounding box inside a sheet rectangle.

    ``margin`` is space reserved *inside* the sheet rectangle for the
    dimensions, balloons and labels that live outside the part outline.
    """

    rect: Rect
    model_x0: float
    model_y0: float
    model_x1: float
    model_y1: float
    scale: float = 1.0
    scale_label: str = "1:1"
    offset_x: float = 0.0
    offset_y: float = 0.0

    @classmethod
    def fit(cls, rect: Rect, bbox: tuple[float, float, float, float],
            margin: float = 26.0, force_scale: float | None = None,
            centre_y: bool = True) -> "View":
        x0, y0, x1, y1 = bbox
        avail_w = rect.w - 2 * margin
        avail_h = rect.h - 2 * margin
        mw, mh = x1 - x0, y1 - y0
        chosen, label = None, "1:1"
        if force_scale:
            chosen = force_scale
            label = scale_text(force_scale, 1) if force_scale >= 1 \
                else scale_text(1, 1 / force_scale)
        else:
            for num, den in STANDARD_SCALES:
                s = num / den
                if mw * s <= avail_w and mh * s <= avail_h:
                    chosen, label = s, scale_text(num, den)
                    break
        if chosen is None:
            chosen = min(avail_w / mw, avail_h / mh)
            label = f"1:{1 / chosen:.3g}"
        cx = rect.cx - (x0 + x1) / 2 * chosen
        cy = rect.cy - (y0 + y1) / 2 * chosen if centre_y else \
            rect.y1 - margin - mh * chosen + y0 * chosen
        return cls(rect, x0, y0, x1, y1, chosen, label, cx, cy)

    # -- transforms ---------------------------------------------------------

    def x(self, mx: float) -> float:
        return self.offset_x + mx * self.scale

    def y(self, my: float) -> float:
        return self.offset_y + my * self.scale

    def pt(self, mx: float, my: float) -> tuple[float, float]:
        return self.x(mx), self.y(my)

    def d(self, length: float) -> float:
        return length * self.scale

    @property
    def sheet_bbox(self) -> Rect:
        return Rect(self.x(self.model_x0), self.y(self.model_y0),
                    self.d(self.model_x1 - self.model_x0),
                    self.d(self.model_y1 - self.model_y0))
