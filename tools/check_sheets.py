#!/usr/bin/env python3
"""Check generated sheets for text collisions and out-of-frame content.

Two failure modes are easy to introduce and easy to miss when a sheet is only
eyeballed at screen size: two pieces of text landing on top of each other, and
something drifting outside the drawing frame.  Both are cheap to test for,
because the SVG carries every text element's position and size, and the font
metrics are the same ones the layout code used.

Reports rather than asserts: some overlaps are deliberate (a dimension value
sitting on its own dimension line, say), so the output is for a human to read.

Run: uv run --no-project --with pillow python tools/check_sheets.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.drafting import style  # noqa: E402
from tools.drafting.sheet import Sheet  # noqa: E402
from tools.layout import drawing_name_for, preview_for, rel, sheets  # noqa: E402

TEXT_RE = re.compile(
    r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*?font-size="([\d.]+)"[^>]*?'
    r'text-anchor="(\w+)"([^>]*)>(.*?)</text>')
ROTATE_RE = re.compile(r'rotate\(([-\d.]+) ([-\d.]+) ([-\d.]+)\)')

#: Cap height below which text on a sheet is a defect.  ISO 3098 puts the floor
#: at 2.5 mm; the slack is for floating point, not for smaller text.
MIN_TEXT_MM = 2.45

#: Overlaps smaller than this are touching, not colliding.
OVERLAP_TOL = 0.35

#: Two pieces of text on the same line, closer than this, read as one word.
#: ISO 3098 puts the minimum word gap at 0.6 of the character height, which is
#: 1.5 mm at the 2.5 mm cap height used here.  A slightly smaller figure is
#: used so that ordinary table cells, whose padding is deliberate, are not
#: reported: what this is for is a label that has drifted up against its
#: neighbour, which is how "H3" and "PMOD 1" came to print as "H3PMOD 1".
MIN_WORD_GAP = 1.2


def unescape(s: str) -> str:
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#x27;", "'"))


def boxes(svg: str) -> list[tuple[float, float, float, float, str, float]]:
    out = []
    for m in TEXT_RE.finditer(svg):
        x, y = float(m.group(1)), float(m.group(2))
        # The SVG carries an em; the layout works in cap heights.
        size = float(m.group(3)) * style.CAP_RATIO
        anchor, rest, text = m.group(4), m.group(5), unescape(m.group(6))
        if not text.strip():
            continue
        bold = "font-weight=" in rest
        w = style.text_width(text, size, bold=bold)
        asc, desc = style.text_height(size), style.descender(size)
        x0 = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
        box = (x0, y - asc, x0 + w, y + desc)
        rot = ROTATE_RE.search(rest)
        if rot:
            ang = math.radians(float(rot.group(1)))
            cx, cy = float(rot.group(2)), float(rot.group(3))
            corners = [(box[0], box[1]), (box[2], box[1]),
                       (box[2], box[3]), (box[0], box[3])]
            pts = []
            for px, py in corners:
                dx, dy = px - cx, py - cy
                pts.append((cx + dx * math.cos(ang) - dy * math.sin(ang),
                            cy + dx * math.sin(ang) + dy * math.cos(ang)))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            box = (min(xs), min(ys), max(xs), max(ys))
        out.append((*box, text, size))
    return out


LINE_RE = re.compile(
    r'<line x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)" '
    r'stroke="([#\w]+)"')

#: Lines a label must not sit on.  Table rules and heading underlines are drawn
#: deliberately close to their text, so only annotation and geometry lines are
#: checked: dimension and leader lines, feature outlines, and phantom parts.
CHECKED_STROKES = {style.C_DIM, style.C_HIGHLIGHT, style.C_PHANTOM,
                   style.C_COMPONENT}


def lines(svg: str):
    for m in LINE_RE.finditer(svg):
        x1, y1, x2, y2 = (float(v) for v in m.groups()[:4])
        if m.group(5) in CHECKED_STROKES:
            yield x1, y1, x2, y2


def all_lines(svg: str):
    """Every ruled line, whatever its colour.

    The stroke filter above is right for "is a line running through this
    text", where a table rule beside its own text is not a fault.  It is wrong
    for "do these two words run together", where a table rule between them is
    exactly what keeps them apart.
    """
    for m in LINE_RE.finditer(svg):
        yield tuple(float(v) for v in m.groups()[:4])


def box_hits_line(box, seg, tol: float) -> float:
    """How far a segment reaches inside a text box, 0 if it stays clear."""
    x0, y0, x1, y1 = box[0] + tol, box[1] + tol, box[2] - tol, box[3] - tol
    if x1 <= x0 or y1 <= y0:
        return 0.0
    ax, ay, bx, by = seg
    # Sample rather than clip: a few points is enough to say whether a line
    # runs through a word, and the maths stays obvious.
    inside = 0
    steps = 40
    for i in range(steps + 1):
        t = i / steps
        px, py = ax + (bx - ax) * t, ay + (by - ay) * t
        if x0 <= px <= x1 and y0 <= py <= y1:
            inside += 1
    if not inside:
        return 0.0
    return math.hypot(bx - ax, by - ay) * inside / steps


def overlap(a, b) -> float:
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return min(dx, dy) if dx > 0 and dy > 0 else 0.0


def side_gap(a, b, rules) -> float | None:
    """Horizontal gap between two pieces of text that share a line.

    None when they do not share a line, when they overlap (which the overlap
    test already reports), or when a ruled line runs between them: a table
    column rule separates two cells perfectly well however narrow the gutter,
    and every table on these sheets is ruled.
    """
    share = min(a[3], b[3]) - max(a[1], b[1])
    if share <= 0.4:
        return None
    lo, hi = (a[2], b[0]) if b[0] >= a[2] else (b[2], a[0])
    gap = hi - lo
    if gap < 0:
        return None
    top, bottom = max(a[1], b[1]), min(a[3], b[3])
    for rx, ry0, ry1 in rules:
        if lo - 0.2 <= rx <= hi + 0.2 and ry0 <= top + 0.2 and ry1 >= bottom - 0.2:
            return None
    return gap


def vertical_rules(svg_lines) -> list[tuple[float, float, float]]:
    """Vertical ruled lines, as (x, y0, y1), for the word-gap test."""
    out = []
    for x1, y1, x2, y2 in svg_lines:
        if abs(x2 - x1) < 0.05 and abs(y2 - y1) > 0.5:
            out.append((x1, min(y1, y2), max(y1, y2)))
    return out


def check_readme_previews() -> list[str]:
    """Every generated preview is shown in the root README's grid.

    The grid is written by ``tools/update_readme.py``, so a sheet added or
    renamed without rerunning it leaves the README showing the wrong set.
    Whether the paths in it resolve is ``check_doc_links``'s question, asked
    of every document rather than only this one.
    """
    readme = ROOT / "README.md"
    if not readme.exists():
        return ["README.md is missing"]
    refs = {target for _, target in doc_links(readme)}
    problems: list[str] = []
    previews = set()
    for svg in sheets():
        preview = preview_for(svg)
        if not preview.exists():
            problems.append(f"{svg.stem} has no preview; run generate_diagrams")
            continue
        previews.add(rel(preview))
    for missing in sorted(previews - refs):
        problems.append(f"{missing} is generated but not shown in README.md")
    return problems


#: How far below its label a title block value sits, at most.  The label is
#: drawn at the top of the cell and the value at the bottom, so the two are
#: less than a row apart; the next row's label is a whole row further down.
CELL_LABEL_DROP = 8.0


def drawing_no_cell(items, rules) -> tuple[str, float] | None:
    """The DRAWING NO cell's value and its room, read off the sheet itself.

    Found by the cell's own label rather than by position, and measured
    between the rules that were actually drawn rather than from the layout
    constants, so this cannot agree with a title block it is not looking at.
    That is the same rule the drafting library learned the hard way: reserve
    from the drawn geometry, not from a second calculation of it.

    None for a sheet with no title block at all -- the A4 drill templates,
    which carry their name in a header line instead.
    """
    labels = [b for b in items if b[4] == "DRAWING NO"]
    if not labels:
        return None
    label = labels[0]
    below = [b for b in items if abs(b[0] - label[0]) < 0.2
             and 0 < b[1] - label[1] < CELL_LABEL_DROP]
    if not below:
        return None
    value = min(below, key=lambda b: b[1])
    # The cell is bounded by the nearest vertical rule each side that spans
    # both the label and the value, which is to say the rules of its own row.
    spanning = [x for x, y0, y1 in rules if y0 <= label[1] and y1 >= value[3]]
    left = [x for x in spanning if x <= label[0]]
    right = [x for x in spanning if x >= value[2]]
    if not left or not right:
        return None
    return value[4], min(right) - max(left) - Sheet.CELL_PAD


def check_drawing_names() -> list[str]:
    """Every sheet's name is its own, fits its cell, and is on the sheet.

    The name is derived from the sheet's own file stem, which very nearly
    makes a collision impossible -- but ``slug`` is not injective, since
    ``rpi5``, ``rpi-5`` and ``rpi_5`` all give ``RPI-5``, so uniqueness is
    checked rather than assumed.  It is checked harder than that now that a
    family may have a name rule in ``FAMILY_NAME_RULES``, because a rule
    throws away more of the stem than ``slug`` does on purpose: a demo board
    sheet is named for the first revision it covers, so two sheets starting
    at one revision would take one name, and two rows of ``ACC_NAMES`` could
    be given the same value.  The set is small enough to answer outright, so
    it is answered rather than reasoned about.

    A name that is a *prefix* of another sheet's is reported the same way.
    Two such names are distinct strings, so the test above passes them, but
    nothing that quotes the shorter one can be read unambiguously: "work from
    the coordinates on TT-MP" points at a family rather than at a drawing
    when ``TT-MP-FITTING-GUIDE`` is one of its sheets, and searching a set of
    documents for the shorter name returns every mention of the longer.  It
    was worse than ambiguous while the carry test below was a substring
    search: handing the bare family prefix back was ``drawing_name``'s first
    answer for the mounting plate, and deleting the title block from the
    plate's SVG left the check passing on the plate's *note* citing the
    fitting guide.  That hole is closed -- the cell is found by its label and
    compared exactly -- but the rule it taught is general, and the next name
    of that shape will not arrive from a bare prefix: ``tt_name`` strips the
    ``p`` separators, so a ``v3p2`` sheet is ``V32`` and a future ``v3p2p1``
    sheet would be ``V321``, which begins with it.  ``drawing_name``'s
    docstring makes producing no such name a rule; this is where the rule is
    enforced rather than asserted.

    Nor does derivation say the result fits.  The title block is a fixed
    165 mm wide whatever a family chooses to call its sheets, and the
    families with no rule are named for stems nobody is keeping short for
    this: ``FPGA-BUTTERSTICK`` is 34.33 mm of lettering at the ISO 3098
    minimum and ``TT-MP-FITTING-GUIDE`` 37.56 mm.  ``Sheet._title_cell``
    refuses to draw a value that overruns its cell, so an overflow cannot
    reach paper -- but that refusal happens one sheet at a time, partway
    through a render, with the rest of the set unbuilt.  Here the whole set
    is answered at once, against the room the cell was actually drawn with.

    The properties are independent and each is reported on its own: a name
    that does not fit is a different defect from one the sheet does not
    carry, and a sheet can have both.

    The two A4 drill templates have no title block and so no cell to overrun.
    Their name goes in a header line whose width ``_fit_beside`` checks as it
    draws, and a title running into it would show up here anyway, in the
    overlap and word-gap tests every text element on every sheet goes through.
    """
    problems = []
    seen: dict[str, Path] = {}
    for svg in sheets():
        name = drawing_name_for(svg)
        if name in seen:
            problems.append(f"{name} names two sheets, {rel(seen[name])} and "
                            f"{rel(svg)}")
        for other, other_svg in seen.items():
            if other == name or not (other.startswith(name)
                                     or name.startswith(other)):
                continue
            short, long = sorted((name, other), key=len)
            paths = {name: svg, other: other_svg}
            problems.append(
                f"{short} names {rel(paths[short])} and is a prefix of "
                f"{long}, which names {rel(paths[long])}, so no test that "
                "reads a sheet can tell the two names apart")
        seen[name] = svg

        text = svg.read_text()
        items = boxes(text)
        cell = drawing_no_cell(items, vertical_rules(all_lines(text)))
        if cell is None:
            # No title block: the name is in the header line, as its own word.
            if not any(b[4] == name or b[4].startswith(f"{name} ")
                       for b in items):
                problems.append(f"{rel(svg)} has no title block and no header "
                                f"text carrying its drawing name, {name}")
            continue

        value, room = cell
        width = style.text_width(name, style.T_MIN, bold=True)
        if width > room:
            problems.append(
                f"{rel(svg)}: the drawing name {name} needs {width:.2f} mm of "
                f"the {room:.2f} mm in the DRAWING NO cell, at the ISO 3098 "
                "minimum lettering size")
        if value != name:
            problems.append(f"{rel(svg)}: the DRAWING NO cell reads {value!r}, "
                            f"not the sheet's own name, {name}")
    return problems


#: Not ours to resolve: an absolute URL, a mail address, a bare anchor into
#: the page itself.
FOREIGN = r"(?!https?://|mailto:|data:|//|#)"

#: A link to something in the repository, in both of the forms these
#: documents use: a Markdown ``[text](path)``, and the ``src=`` and ``href=``
#: of an HTML tag.  The preview grids are HTML tables -- Markdown gives no way
#: to set a column width -- so every path in every grid is of the second kind,
#: and a check that read only Markdown links read none of them.  The anchor,
#: if any, is not checked.
DOC_LINK_RE = re.compile(
    rf"\]\({FOREIGN}([^)\s]+)\)"
    rf'|(?:src|href)="{FOREIGN}([^"]+)"')


def doc_links(doc: Path) -> list[tuple[str, str]]:
    """Every in-repository link in *doc*, as (how it is written, its target).

    The target is repository-relative, since a link is written relative to
    the file it sits in and the two differ for every document but the root
    README.
    """
    out = []
    for markdown, html in DOC_LINK_RE.findall(doc.read_text()):
        written = markdown or html
        target = written.split("#", 1)[0]
        if not target:
            continue
        resolved = (doc.parent / target).resolve()
        try:
            out.append((written, str(resolved.relative_to(ROOT))))
        except ValueError:
            # A link that climbs out of the repository resolves on this
            # machine and nowhere else, so it is returned absolute and the
            # caller reports it rather than testing whether it happens to
            # exist here.
            out.append((written, str(resolved)))
    return out


def check_doc_links() -> list[str]:
    """Every relative link in every document resolves.

    The documentation is split one README per directory, so the documents
    link to each other constantly and each link is written relative to the
    file it sits in.  Moving a directory then breaks links in files that were
    not touched, which nothing else here would notice.

    Every ``*.md`` in the tree, and both kinds of link in each: this read only
    the root README's HTML and only Markdown links elsewhere, which left the
    preview grid in every family README and the two thumbnails on the adapter
    comparison page -- all of them HTML, all of them paths to files the build
    writes and renames -- checked by nothing at all.
    """
    problems = []
    for doc in sorted(ROOT.rglob("*.md")):
        if ".git" in doc.parts or "tmp" in doc.parts:
            continue
        for written, target in doc_links(doc):
            if Path(target).is_absolute():
                problems.append(f"{doc.relative_to(ROOT)} links to {written}, "
                                "which is outside the repository")
            elif not (ROOT / target).exists():
                problems.append(f"{doc.relative_to(ROOT)} links to {written}, "
                                "which does not exist")
    return problems


def main() -> int:
    paths = sheets()
    if not paths:
        raise SystemExit("no sheets found; run tools/generate_diagrams.py")

    total = 0
    for path in paths:
        svg = path.read_text()
        page_w = float(re.search(r'width="([\d.]+)mm"', svg).group(1))
        page_h = float(re.search(r'height="([\d.]+)mm"', svg).group(1))
        # The zone markings live in the strip between the trim line and the
        # drawing frame, by design, so the bound is the trim line.
        trim = style.TRIM_MARGIN
        items = boxes(svg)
        svg_lines = list(lines(svg))
        rules = vertical_rules(all_lines(svg))

        problems: list[str] = []
        for i, a in enumerate(items):
            if a[5] < MIN_TEXT_MM:
                problems.append(f"text {a[4]!r} is {a[5]:.2f} mm, under the "
                                f"{MIN_TEXT_MM} mm floor")
            if a[0] < trim or a[2] > page_w - trim \
                    or a[1] < trim or a[3] > page_h - trim:
                problems.append(f"text {a[4]!r} at ({a[0]:.1f},{a[1]:.1f}) "
                                f"lies outside the drawing frame")
            for b in items[i + 1:]:
                ov = overlap(a, b)
                if ov > OVERLAP_TOL:
                    problems.append(
                        f"text {a[4]!r} and {b[4]!r} overlap by {ov:.2f} mm "
                        f"near ({max(a[0], b[0]):.1f},{max(a[1], b[1]):.1f})")
                    continue
                gap = side_gap(a, b, rules)
                if gap is not None and gap < MIN_WORD_GAP:
                    problems.append(
                        f"text {a[4]!r} and {b[4]!r} are {gap:.2f} mm apart "
                        f"and read as one word, near "
                        f"({max(a[0], b[0]):.1f},{max(a[1], b[1]):.1f})")
        for a in items:
            for seg in svg_lines:
                run = box_hits_line(a[:4], seg, tol=0.5)
                if run > 1.0:
                    problems.append(
                        f"a line runs {run:.2f} mm through the text {a[4]!r} "
                        f"at ({a[0]:.1f},{a[1]:.1f})")
                    break

        name = rel(path)
        if problems:
            total += len(problems)
            print(f"{name}: {len(problems)} problem(s)")
            for line in problems[:14]:
                print(f"    {line}")
            if len(problems) > 14:
                print(f"    ... and {len(problems) - 14} more")
        else:
            print(f"{name}: clean ({len(items)} text elements)")
    names = check_drawing_names()
    for line in names:
        print(f"names: {line}")
    total += len(names)
    readme = check_readme_previews() + check_doc_links()
    for line in readme:
        print(f"docs: {line}")
    total += len(readme)

    print(f"\n{total} problem(s) across {len(paths)} sheets")
    # A non-zero exit, so `make check` actually fails.  Printing the problems
    # and exiting 0 meant a build could go green with fifty collisions on it.
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
