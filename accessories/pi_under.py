"""What a Raspberry Pi has under the direct Raspmod: every model at once.

The adapter sits on a Pi's 40-pin header with its underside ADAPTER_UNDER
above the Pi's top face, so anything on the Pi inside the adapter's
footprint and taller than that stops it seating.  This module is the list
of such parts across the models, each read off the model's own drawing,
and a composite board -- the outline, holes and header every model shares,
with those parts on it -- for the adapter's sheet to draw itself over.

Only the parts inside the adapter's footprint are here.  The USB and
Ethernet stacks of every model stand beyond its far end (X 65.65 in the
Pi's frame; the nearest, the 4B's Ethernet, starts at 66.65) and are left
off, so that what the sheet shows is what a reshaped board has to clear.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from accessories.raspmod_direct import PI_PIN1, RASPMOD_DIRECT
from base_plates.plates import ADAPTER_UNDER
from raspberry_pi.boards import BOARDS as RPI
from tinytapeout.mounting_plate.plate import PMOD_SLOT_X
from tools.schema import BoardSpec, Feature, turned


@dataclass(frozen=True)
class ClashPart:
    """A part on some Raspberry Pi model that lies under the adapter."""

    label: str
    #: The data keys of the models that carry it.  The 3B+ shares the 3B's
    #: sheet and has no key; a part it carries says so in its label.
    models: tuple[str, ...]
    x0: float
    y0: float
    x1: float
    y1: float
    #: Height above the Pi's top face.
    z: float
    source: str

    @property
    def clashes(self) -> bool:
        return self.z > ADAPTER_UNDER


CLASH_PARTS = (
    ClashPart("PoE header, 3B+ and 4B", ("rpi4b",),
              58.25 - 2.54, 49.86 - 2.54, 58.25 + 2.54, 49.86 + 2.54, 8.5,
              "Pi 4 drawing: centre 25.75 from the header's centre and 6.14 from "
              "the edge, a 2x2 on the 2.54 pitch, as tall as the 40-pin header "
              "(Z 8.5); the 3B+ drawing's PoE silk is at the same place"),
    # ASSUMED height: the drawing gives the outline and not the part.  A
    # 3 x 6 mm outline beside MT4 is a 3-pin JST SH, 4.25 tall top-entry
    # and lower side-entry; either is under the adapter.
    ClashPart("UART connector, Pi 5", ("rpi5",),
              65.24, 48.99, 68.24, 54.98, 4.3,
              "Pi 5 drawing, read from its vectors: a 3.0 x 6.0 outline beside "
              "MT4, 6 from the edge; height ASSUMED 4.3 at most, a JST SH"),
)


def parts_on(model_key: str) -> tuple[ClashPart, ...]:
    return tuple(p for p in CLASH_PARTS if model_key in p.models)


def pi_under_adapter() -> BoardSpec:
    """The composite Pi, in the Pi's own frame.

    The outline, the four mounting holes and the 40-pin header are the same
    on every Model B sized Pi (``raspberry_pi/extract.py`` checks the
    header); the Pi 5's two extra holes are drawn too, since a wider board
    may want to know.  Each part under the adapter is a feature named with
    its model and height, and the notes say which clash.
    """
    pi5 = RPI["rpi5"]
    header = next(f for f in pi5.features if f.key == "gpio40")
    features = [replace(header, note="", number=None)]
    for p in CLASH_PARTS:
        verdict = "CLASH" if p.clashes else "clears"
        features.append(Feature(key=p.label.split(",")[0].lower().replace(" ", "_"),
                                label=f"{p.label}: Z {p.z:g}, {verdict}", kind="connector",
                                x0=p.x0, y0=p.y0, x1=p.x1, y1=p.y1, note=p.source))
    # One note: what the boxes are judged against.  Which models fit is the
    # adapter's own note, and each part's height is on its label.
    notes = [f"The adapter's underside is {ADAPTER_UNDER} above the Pi's top face (its "
             "header body 2.54, the socket 3.8): a part of the Pi under it taller than "
             "that stops it seating. Every model's USB and Ethernet stack stands beyond "
             "the adapter's end and is not drawn."]
    return replace(
        pi5,
        key="pi-under-adapter",
        title="Raspberry Pi, every Model B sized model",
        subtitle="What is under the direct Raspmod",
        features=tuple(features),
        pmods=(),
        notes=tuple(notes),
        sources=(),
    )


def pi_pin1() -> tuple[float, float]:
    """The Pi's pin 1, from the header every model shares."""
    return next(f for f in RPI["rpi5"].features if f.key == "gpio40").pin1


def turn_centre() -> tuple[float, float]:
    """The point the Pi is turned about to lie under the adapter.

    The adapter sits pin 1 on pin 1, which is a half turn, so the Pi in
    the adapter's frame is the Pi turned about the midpoint of the two
    pins 1; the same turn takes the adapter's frame back to the Pi's.
    """
    p1 = pi_pin1()
    return ((p1[0] + PI_PIN1[0]) / 2, (p1[1] + PI_PIN1[1]) / 2)


def host_pitch() -> float:
    return PMOD_SLOT_X[1] - PMOD_SLOT_X[0]


def fourth_plug() -> Feature:
    """Where a fourth plug would go: one host pitch beyond P3.

    A feature with a pin field rather than a Pmod, since it is a question
    and not a part: a Pmod would be dimensioned and tabled as a host.
    """
    p3 = max((p for p in RASPMOD_DIRECT.pmods if p.role == "plug"), key=lambda p: p.cx)
    pitch = host_pitch()
    half = p3.pin_span / 2 + 1.3
    return Feature(key="p4", label="P4?", kind="connector",
                   x0=round(p3.cx + pitch - half, 2), y0=round(p3.cy - p3.row_span / 2 - 1.3, 2),
                   x1=round(p3.cx + pitch + half, 2), y1=round(p3.cy + p3.row_span / 2 + 1.3, 2),
                   pins=(p3.columns, p3.rows), pin1=(round(p3.pin1_x + pitch, 2), p3.pin1_y))


def grown_edge() -> Feature:
    """The edge a board four plugs wide would have."""
    o = RASPMOD_DIRECT.outline
    return Feature(key="four_plugs", label="board edge, four plugs",
                   kind="outline", x0=0.0, y0=0.0, x1=round(o.width + host_pitch(), 2),
                   y1=o.height)


def pi_under_direct() -> BoardSpec:
    """The composite Pi in the adapter's frame, with P4 and the grown edge."""
    cx, cy = turn_centre()
    under = turned(pi_under_adapter(), cx, cy)
    return replace(under, features=under.features + (fourth_plug(), grown_edge()))


def adapter_on_pi() -> tuple[float, float, float, float]:
    """The adapter's footprint in the Pi's frame: x0, y0, x1, y1."""
    cx, cy = turn_centre()
    o = RASPMOD_DIRECT.outline
    xs = [2 * cx - x for x in (0.0, o.width)]
    ys = [2 * cy - y for y in (0.0, o.height)]
    return (round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2))
