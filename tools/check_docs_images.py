#!/usr/bin/env python3
"""Prove the committed docs pictures are the ones the committed sheets make.

``tools/docs_images.py`` writes each listed sheet's pictures for the docs
site from the SVG on disk.  This holds what is staged against what that
writes from the staged SVG, byte for byte, the way ``check_pdfs.py`` holds
the PDFs, and for the same reason: the working tree is whatever `make
diagrams` wrote moments ago and agrees with itself whatever the repository
holds, and HEAD would mean a new picture could not go green until after it
was committed.  So a picture is stale against its sheet, missing, or left
over from a sheet no longer pictured, and each says so.

Writing them again also runs every rule ``docs_images.py`` keeps: the palette
against its own contrast floors, every colour on the sheet in the palette,
and no panel edge through anything drawn.

Run: uv run --no-project --with pillow --with pypdf python tools/check_docs_images.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.docs_images import (DOCS_SHEETS, SHEET_PNG_ONLY,  # noqa: E402
                               kept, panels_by_sheet, write)
from tools.layout import FAMILY_DIRS, docs_dir_for, rel  # noqa: E402

WORK = ROOT / "tmp" / "check-docs-images"


def blob(path: str) -> bytes | None:
    """The staged bytes of *path*, or None if it is not in the index."""
    out = subprocess.run(["git", "show", f":{path}"], cwd=ROOT,
                         capture_output=True)
    return out.stdout if out.returncode == 0 else None


def staged_docs() -> set[str]:
    """Every file staged under any family's ``output/docs/``."""
    dirs = [rel(docs_dir_for(d / "x.svg")) for d in FAMILY_DIRS.values()]
    out = subprocess.run(["git", "ls-files", "--", *dirs], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return set(out.stdout.split())


def main() -> int:
    bad: list[str] = []
    expected: set[str] = set()
    shutil.rmtree(WORK, ignore_errors=True)
    try:
        for path, (panels, furniture) in panels_by_sheet().items():
            svg_bytes = blob(path)
            if svg_bytes is None:
                bad.append(f"{path}: listed in DOCS_SHEETS and not staged")
                continue
            scratch = WORK / path
            scratch.parent.mkdir(parents=True, exist_ok=True)
            scratch.write_bytes(svg_bytes)
            out_dir = WORK / "docs"
            png_only = path in SHEET_PNG_ONLY
            write(svg_bytes.decode("utf-8"), scratch, panels, furniture,
                  out_dir, png_only)
            docs = docs_dir_for(ROOT / path)
            for fresh in kept(scratch, out_dir, png_only):
                name = rel(docs / fresh.name)
                expected.add(name)
                staged = blob(name)
                if staged is None:
                    bad.append(f"{name}: not staged; run make diagrams "
                               "and stage it")
                elif staged != fresh.read_bytes():
                    bad.append(f"{name}: not what the staged {path} "
                               "makes; run make diagrams and stage both")
        for name in sorted(staged_docs() - expected):
            bad.append(f"{name}: staged, and no sheet in DOCS_SHEETS makes "
                       "it")
    finally:
        shutil.rmtree(WORK, ignore_errors=True)

    for line in bad:
        print(f"  {line}")
    print(f"docs pictures: {len(DOCS_SHEETS)} sheets, "
          f"{len(expected)} files, {len(bad)} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
