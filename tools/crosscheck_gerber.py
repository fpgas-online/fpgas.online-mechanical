#!/usr/bin/env python3
"""Cross-check an extracted board outline against the upstream gerber.

The gerber is produced by KiCad's own plotter from the same board file, so it
is an independent artefact: if the outline recovered by ``tools/kicad_pcb.py``
matches it, the whole s-expression parsing and coordinate handling path is
confirmed by something that did not come from this repository.

Needs network access, so it is not part of the normal build.

Run: uv run --no-project python tools/crosscheck_gerber.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tinytapeout.boards import BOARDS  # noqa: E402

#: Which archived gerbers correspond to which extracted revision.  Only the
#: TT01/02/03 board has an Edge_Cuts gerber archived in its own repository at a
#: revision that matches what is extracted here.
CASES = [
    ("tt123-v2.2.6", "TinyTapeout/tt123-demo-pcb",
     "pcba/gerber/v2p2p6/mpw-mb1-Edge_Cuts.gbr"),
]


def fetch(repo: str, path: str) -> str:
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}", "--jq", ".content"],
        capture_output=True, text=True, check=True).stdout
    import base64
    return base64.b64decode(out).decode("utf-8", "replace")


def gerber_extent(text: str) -> tuple[float, float]:
    """Extent of the segment endpoints in a gerber, in millimetres.

    Arc bulges are not followed, so this is the extent of the straight-line
    endpoints.  For a rounded rectangle that is the same as the overall size,
    because the arcs are corner fillets tangent to the edges.
    """
    fmt = re.search(r"%FSLAX(\d)(\d)Y(\d)(\d)\*%", text)
    dec = int(fmt.group(2)) if fmt else 6
    xs, ys = [], []
    for m in re.finditer(r"X(-?\d+)Y(-?\d+)D0[123]\*", text):
        xs.append(int(m.group(1)) / 10 ** dec)
        ys.append(int(m.group(2)) / 10 ** dec)
    if not xs:
        raise SystemExit("no coordinates found in the gerber")
    return max(xs) - min(xs), max(ys) - min(ys)


def main() -> None:
    bad = 0
    for key, repo, path in CASES:
        spec = BOARDS[key].outline
        gw, gh = gerber_extent(fetch(repo, path))
        ok = abs(gw - spec.width) < 0.01 and abs(gh - spec.height) < 0.01
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {key}: gerber {gw:.3f} x {gh:.3f} mm, "
              f"extracted {spec.width:.3f} x {spec.height:.3f} mm")
        print(f"      {repo}/{path}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
