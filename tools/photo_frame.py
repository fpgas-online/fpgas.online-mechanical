"""Measuring a board from a photograph of it, square on.

For a board whose maker publishes no drawing: find the board's own edges in
the photograph, map its corners onto the rectangle the maker says it is, and
measure everything else in that frame in millimetres.  The frame is the
repository's own (tools/schema.py): lower-left corner of the board seen from
the component side, X right, Y up.  A photograph of the underside is mirrored
into it, so a hole measured from either side lands on the same coordinates.

accessories/measure_pmod_hat.py fits two screws and assumes no perspective;
this fits the four corners with a homography, which removes the perspective
of a camera that was not quite square on.  What a homography cannot remove is
the parallax of anything standing off the board -- a connector's top face is
nearer the lens and drawn larger -- which is the caller's to correct.

Needs numpy and opencv-python-headless.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class Frame:
    """The board rectangle a photograph is fitted to, and its rectified image.

    *px_per_mm* and *margin* fix the rectified image: the board and *margin*
    millimetres all round it, so parts overhanging the edge stay in view.
    """

    width: float
    height: float
    px_per_mm: float = 20.0
    margin: float = 10.0

    def to_px(self, x: float, y: float) -> tuple[float, float]:
        s, m = self.px_per_mm, self.margin
        return (x + m) * s, (self.height + m - y) * s

    def to_mm(self, px: float, py: float) -> tuple[float, float]:
        s, m = self.px_per_mm, self.margin
        return px / s - m, self.height + m - py / s

    def corners(self, flip: str | None) -> list[tuple[float, float]]:
        """The board corner under each image corner, top-left first, clockwise.

        None is a top view; "x" a bottom view turned over left to right, "y"
        one turned over top to bottom.
        """
        w, h = self.width, self.height
        return {None: [(0, h), (w, h), (w, 0), (0, 0)],
                "x": [(w, h), (0, h), (0, 0), (w, 0)],
                "y": [(0, 0), (w, 0), (w, h), (0, h)]}[flip]


def clear_spans(frame: Frame, flip, hidden: dict, corner: float):
    """For each image edge, the fractions of it where the board edge shows.

    *hidden* gives, per board edge ("top", "bottom", "left", "right"), the
    board-frame intervals a connector hides; *corner* is kept clear of each
    end, where the corner radius is.
    """
    out = []
    pts = frame.corners(flip)
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        axis = 0 if a[1] == b[1] else 1
        name = (("top" if a[1] == frame.height else "bottom") if axis == 0
                else ("right" if a[0] == frame.width else "left"))
        length = abs(b[axis] - a[axis])
        blocked = sorted([(0.0, corner), (length - corner, length)]
                         + [tuple(sorted((abs(lo - a[axis]), abs(hi - a[axis]))))
                            for lo, hi in hidden.get(name, ())])
        free, pos = [], 0.0
        for lo, hi in blocked:
            if lo > pos + 0.3:
                free.append((pos / length, lo / length))
            pos = max(pos, hi)
        out.append(free)
    return out


def edge_points(lum, p0, p1, half: int, spans, n: int = 500) -> np.ndarray:
    """Where the board edge crosses each scanline across the line p0-p1.

    Scanlines run from outside the board inwards, so the edge is the first
    steep fall into the dark board, found to a fraction of a pixel.
    """
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    nrm = np.array([-d[1], d[0]])
    s = np.arange(-half, half + 1)
    pts = []
    for t in np.linspace(0, 1, n):
        if not any(a <= t <= b for a, b in spans):
            continue
        xy = (p0 + (p1 - p0) * t)[None, :] + s[:, None] * nrm[None, :]
        prof = cv2.remap(lum, xy[:, 0].astype(np.float32).reshape(1, -1),
                         xy[:, 1].astype(np.float32).reshape(1, -1),
                         cv2.INTER_LINEAR)[0]
        g = -np.gradient(prof)
        if g.max() < 8:
            continue
        k = int(np.argmax(g > 0.5 * g.max()))
        while k + 1 < len(g) and g[k + 1] > g[k]:
            k += 1
        off = 0.0
        curve = g[k - 1] - 2 * g[k] + g[k + 1] if 0 < k < len(g) - 1 else 0
        if curve:
            off = 0.5 * (g[k - 1] - g[k + 1]) / curve
        pts.append(p0 + (p1 - p0) * t + (s[k] + off) * nrm)
    return np.array(pts)


def fit_line(pts):
    """A line through *pts*, dropping what a connector or a nick put off it.

    Returns ((point, direction), rms residual in pixels, points kept).
    """
    keep = np.ones(len(pts), bool)
    for _ in range(6):
        m = pts[keep].mean(0)
        d = np.linalg.svd(pts[keep] - m)[2][0]
        r = (pts - m) @ np.array([-d[1], d[0]])
        keep = np.abs(r) < 3 * (1.5 * np.median(np.abs(r[keep])) + 0.3)
    return (m, d), float(np.sqrt((r[keep] ** 2).mean())), int(keep.sum())


def fit_board(img, frame: Frame, approx, flip, hidden: dict, corner: float):
    """Find the board in *img* and rectify it onto *frame*.

    *approx* is roughly where the four corners are, in image pixels, top-left
    first and clockwise.  Returns the fitted corners, each edge's (rms, points
    kept), and the rectified image, in which *frame*'s to_px and to_mm hold.
    """
    lum = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                           .astype(np.float32), (0, 0), 1.2)
    spans = clear_spans(frame, flip, hidden, corner)
    corners = [np.array(p, float) for p in approx]
    half = int(0.02 * img.shape[1])
    for _ in range(3):
        fits = [fit_line(edge_points(lum, corners[i], corners[(i + 1) % 4],
                                     half, spans[i])) for i in range(4)]
        corners = []
        for i in range(4):
            (m1, d1), (m2, d2) = fits[i - 1][0], fits[i][0]
            t = np.linalg.solve(np.array([d1, -d2]).T, m2 - m1)
            corners.append(m1 + t[0] * d1)
        half = max(8, half // 2)
    dst = np.float32([frame.to_px(*p) for p in frame.corners(flip)])
    T = cv2.getPerspectiveTransform(np.float32(corners), dst)
    m, s = frame.margin, frame.px_per_mm
    size = (int((frame.width + 2 * m) * s), int((frame.height + 2 * m) * s))
    rect = cv2.warpPerspective(img, T, size, flags=cv2.INTER_CUBIC,
                               borderValue=(255, 255, 255))
    return np.array(corners), [(f[1], f[2]) for f in fits], rect


def photographed_height(corners, width: float) -> float:
    """The board's height if its width is *width*, as the photograph has it.

    The homography cannot say this -- it maps the corners onto whatever
    rectangle it is given -- so it is read from the photograph instead: the
    ratio of the board's two sides at its centre.  That is the true ratio for
    a camera square on and is out by (1 - cos tilt) otherwise.
    """
    G = cv2.getPerspectiveTransform(
        np.float32([[0, 0], [1, 0], [1, 1], [0, 1]]), np.float32(corners))

    def at(u, v):
        p = G @ np.array([u, v, 1.0])
        return p[:2] / p[2]
    c = at(.5, .5)
    return width * (np.linalg.norm(at(.5, .5001) - c)
                    / np.linalg.norm(at(.5001, .5) - c))


def fit_circle(pts):
    """Least-squares circle through *pts*: centre x, centre y, radius."""
    x, y = pts[:, 0], pts[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    cx, cy, c = np.linalg.lstsq(A, x * x + y * y, rcond=None)[0]
    return cx, cy, float(np.sqrt(c + cx * cx + cy * cy))


def ring(rect, frame: Frame, x: float, y: float):
    """A plated hole's copper ring near board point (x, y), in millimetres.

    Rays from the guessed centre.  Gold on blue is the strongest contrast on
    the board in the red-minus-blue difference, so on each ray the outer edge
    is where that falls going outwards and the inner edge, the hole, where it
    falls going inwards.  A circle is fitted to each with outliers dropped,
    and the guess refined from the outer one.  Returns {"outer": ...,
    "inner": ...}, each with x, y, dia and rms, or None if no ring is found.
    """
    img = rect.astype(np.float32)
    rb = cv2.GaussianBlur(img[..., 2] - img[..., 0], (0, 0), 1.0)
    s = frame.px_per_mm
    out = None
    for _ in range(3):
        cx, cy = frame.to_px(x, y)
        res = {}
        for key, (r0, r1), sign in (("outer", (1.9, 3.4), 1),
                                    ("inner", (0.9, 2.1), -1)):
            rs = np.arange(r0 * s, r1 * s, 0.5)
            pts = []
            for a in np.linspace(0, 2 * np.pi, 180, endpoint=False):
                prof = cv2.remap(
                    rb, (cx + rs * np.cos(a)).astype(np.float32).reshape(1, -1),
                    (cy + rs * np.sin(a)).astype(np.float32).reshape(1, -1),
                    cv2.INTER_LINEAR)[0]
                g = -np.gradient(prof) * sign
                k = int(np.argmax(g))
                if g[k] < 6 or k in (0, len(g) - 1):
                    continue
                curve = g[k - 1] - 2 * g[k] + g[k + 1]
                rr = rs[k] + (0.25 * (g[k - 1] - g[k + 1]) / curve if curve else 0)
                pts.append((cx + rr * np.cos(a), cy + rr * np.sin(a)))
            if len(pts) < 20:
                continue
            pts = np.array(pts)
            keep = np.ones(len(pts), bool)
            for _ in range(4):
                fx, fy, fr = fit_circle(pts[keep])
                d = np.hypot(pts[:, 0] - fx, pts[:, 1] - fy) - fr
                keep = np.abs(d) < 2.5 * (1.4826 * np.median(np.abs(d[keep])) + 0.2)
            fx, fy, fr = fit_circle(pts[keep])
            mx, my = frame.to_mm(fx, fy)
            res[key] = dict(x=mx, y=my, dia=2 * fr / s,
                            rms=float(np.sqrt((d[keep] ** 2).mean())) / s)
        if "outer" not in res:
            return None
        x, y = res["outer"]["x"], res["outer"]["y"]
        out = res
    return out


def blob(rect, frame: Frame, x: float, y: float, r: float, weight) -> tuple:
    """Centroid of the brightest part of *weight* within *r* mm of (x, y).

    *weight* is an image the size of *rect*; the part is split from its
    surroundings by Otsu's threshold inside the disc, and the disc is moved
    onto the centroid and the split redone, four times.
    """
    s = frame.px_per_mm
    for _ in range(4):
        cx, cy = frame.to_px(x, y)
        rr = r * s
        x0, y0 = int(cx - rr - 2), int(cy - rr - 2)
        w = weight[y0:y0 + int(2 * rr) + 5, x0:x0 + int(2 * rr) + 5]
        yy, xx = np.mgrid[0:w.shape[0], 0:w.shape[1]]
        inside = (xx + x0 - cx) ** 2 + (yy + y0 - cy) ** 2 <= rr * rr
        t, _ = cv2.threshold(np.clip(w, 0, 255).astype(np.uint8), 0, 255,
                             cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        m = (w > t) & inside
        if m.sum() < 5:
            return None
        x, y = frame.to_mm((xx[m] + x0).mean(), (yy[m] + y0).mean())
    return x, y


def grid_image(rect, frame: Frame, box, zoom: float = 2.0):
    """A crop of the rectified view with a 1 mm grid ruled and numbered on it.

    What the hand readings in a measuring script are read off, so that any
    one of them can be checked.  *box* is (x0, y0, x1, y1), mm.
    """
    x0, y0, x1, y1 = box
    p0, p1 = frame.to_px(x0, y1), frame.to_px(x1, y0)
    c = cv2.resize(rect[int(p0[1]):int(p1[1]), int(p0[0]):int(p1[0])], None,
                   fx=zoom, fy=zoom, interpolation=cv2.INTER_CUBIC)
    for v in range(int(np.ceil(x0)), int(np.floor(x1)) + 1):
        px = int((frame.to_px(v, 0)[0] - int(p0[0])) * zoom)
        cv2.line(c, (px, 0), (px, c.shape[0]), (0, 0, 255), 1)
        cv2.putText(c, str(v), (px + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 0, 255), 1)
    for v in range(int(np.ceil(y0)), int(np.floor(y1)) + 1):
        py = int((frame.to_px(0, v)[1] - int(p0[1])) * zoom)
        cv2.line(c, (0, py), (c.shape[1], py), (0, 0, 255), 1)
        cv2.putText(c, str(v), (2, py - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 0, 255), 1)
    return c
