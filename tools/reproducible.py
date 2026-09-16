"""Make generated files reproduce byte for byte.

Everything under a family's ``output/`` directory is build product, and this
repository commits it so that cloning is enough to print from.  That only pays
off if rebuilding is a no-op.  If ``make diagrams`` dirties seventeen files
whose drawings are identical, ``git status`` stops meaning anything, every
rebuild has to be inspected by hand before it can be discarded, and the
committed artefacts start looking like a liability rather than a deliverable.

Two of the four formats stamp themselves:

* cairo writes a ``/CreationDate`` into every PDF Inkscape produces, and
  both tools write their version numbers into ``/Producer`` and ``/Creator``;
* ezdxf writes creation and update times, a "time in drawing" counter and two
  freshly generated GUIDs into every DXF, and emits the CLASSES section in an
  order that varies between runs.

None of that carries information.  Git already records when a file changed,
and it records it more accurately than a timestamp written into a file that is
rewritten whether or not anything in it changed; and which point release of
Inkscape drew a sheet is no more a property of the drawing than the day it was
drawn on, as long as the drawing came out the same, which the byte comparison
in ``tools/check_pdfs.py`` is there to say.

So the timestamps are pinned to one arbitrary instant, the tool strings to
the tools' bare names, and the GUIDs are left to ezdxf, whose fixed-metadata
mode writes them as all zeros.  The instant is
deliberately neither "now" nor ``SOURCE_DATE_EPOCH``: reading an environment
variable would mean two people building the same commit get different bytes,
which is the exact problem this module exists to remove.

This module once carried two GUID constants of its own, derived by ``uuid5``
over the repository's URL.  They were never written to anything -- ezdxf's
option had already dealt with the GUIDs -- so they sat for several commits
looking load-bearing, and a URL that mattered to nothing was documented as a
thing that must not be changed.  The check for that class of mistake is
whether a constant has a reader, not whether its derivation is elegant.
"""

from __future__ import annotations

import datetime
import subprocess
from collections import OrderedDict
from pathlib import Path

#: The one arbitrary instant.  Any fixed value would do; a round one makes it
#: obvious at a glance that it was chosen rather than recorded.
EPOCH = datetime.datetime(2000, 1, 1, 0, 0, 0)

#: The same instant in the two formats that want it.
PDF_CREATION_DATE = "D:20000101000000Z"

#: What a sheet's PDF says drew it, with no version number.  Inkscape 1.4 and
#: 1.4.3 on the same cairo 1.18.4 write byte-identical content streams and
#: differ only in "Inkscape 1.4" against "Inkscape 1.4.3" in /Creator, so a
#: rebuild on the second machine changed every PDF in the repository while
#: changing no drawing.  /Producer was "cairo 1.18.4" on both and is pinned
#: alongside so that the next cairo release cannot do the same.
PDF_CREATOR = "Inkscape"
PDF_PRODUCER = "cairo"

#: What a bound copy says: pypdf writes it, and pypdf writes its name without
#: a version to begin with.  It has no /Creator, because no drawing tool
#: made it; stamping the sheets' tool on it would be a claim about a file
#: that tool never saw.
BUNDLE_PRODUCER = "pypdf"

#: This repository's URL, for anything that needs to cite where the drawings
#: came from.  Nothing in the output carries it today.
REPO_URL = "https://github.com/fpgas-online/fpgas.online-mechanical"


def normalise_pdf(path: Path, *, bound: bool = False) -> Path:
    """Pin *path*'s creation date and tool strings, in place.

    A sheet is stamped as drawn by Inkscape on cairo; a *bound* copy, which
    pypdf assembled from finished sheets, as made by pypdf.

    Rewritten through pypdf rather than patched in the bytes, because cairo
    puts the date inside a compressed object stream: the four bytes that
    differ between two runs are deflate output, not a date anyone can find and
    replace.  The page content stream, the page size and the resources come
    through untouched -- checked, not assumed, by ``tools/check_pdfs.py``.
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(path))
    writer = PdfWriter(clone_from=reader)
    meta = dict(reader.metadata or {})
    meta["/CreationDate"] = PDF_CREATION_DATE
    if bound:
        meta["/Producer"] = BUNDLE_PRODUCER
        meta.pop("/Creator", None)
    else:
        meta["/Creator"] = PDF_CREATOR
        meta["/Producer"] = PDF_PRODUCER
    meta.pop("/ModDate", None)
    writer.add_metadata(meta)
    with open(path, "wb") as handle:
        writer.write(handle)
    return path


def configure_dxf() -> None:
    """Put ezdxf into fixed-metadata mode.  Call *before* ``ezdxf.new()``.

    ``write_fixed_meta_data_for_testing`` pins the four timestamps, both GUIDs
    and the "written by ezdxf" marker string.  Its name says testing, but
    reproducible output is the same requirement, and it happens to pin to
    2000-01-01, which is where EPOCH above comes from.

    Before ``ezdxf.new()`` because one of those marks, CREATED_BY_EZDXF, is
    written when the document is created rather than when it is saved: setting
    the option later leaves exactly one line of the file still moving.
    """
    import ezdxf

    ezdxf.options.write_fixed_meta_data_for_testing = True


def normalise_dxf(doc) -> None:
    """Settle the CLASSES section into a fixed order.  Call before saving.

    The option above does not touch this one.  ezdxf holds the classes a DXF
    version requires in a ``set`` of names and registers them by iterating it,
    and iteration order for a set of strings depends on PYTHONHASHSEED, which
    is different in every process.  So the section comes out in one of two
    orders about half the time each -- which is why this looked fixed the
    first time it was measured and was not.

    Registering them here and sorting afterwards is what settles it.  The
    export registers them again, but ``add_class`` ignores a name it already
    holds, so nothing is added the second time and the sorted order survives.
    """
    doc.classes.add_required_classes(doc.dxfversion)
    doc.classes.classes = OrderedDict(sorted(doc.classes.classes.items()))


# -- what version of the source a sheet was drawn from ----------------------

#: Everything that is not build product.  A commit that touches only a
#: family's output/ does not change what the drawings say, so it must not
#: change the version they carry.
SOURCE_ONLY = (".", ":(exclude)*/output/*")

#: When there is no git to ask: a tarball, an export, a clone with no history.
UNVERSIONED = "no-git"

#: Appended when source files are modified but not committed.  A single
#: character because the title block cell has 38.05 mm of room and
#: "-dirty" does not fit -- the sheet would refuse to render, which would
#: block the ordinary edit-and-rebuild loop rather than catch a mistake.
DIRTY_MARK = "+"


def _git(root, *args: str) -> str | None:
    """Run git in *root*, or None if git or the repository is not there."""
    try:
        out = subprocess.run(("git",) + args, cwd=root,
                             capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def source_version(root=None) -> str:
    """``git describe`` of the last commit that changed anything but output.

    The sheets carry this where they used to carry the date they were
    rendered.  A date meant every sheet in the repository changed whenever
    anyone rebuilt on a different day, which made `git status` noise rather
    than signal -- and it did not even answer the question a reader has, which
    is which version of the data a drawing was made from.

    It describes the last commit to touch a *source* path rather than HEAD,
    and that distinction is what makes it converge.  The output is committed,
    so stamping HEAD would mean: render at X, commit the sheets as Y, rebuild
    and every sheet now says Y, commit that as Z, and so on for as long as
    anyone keeps rebuilding.  Committing output does not change the last
    source commit, so a rebuild after it reproduces the same bytes.
    """
    root = root or Path(__file__).resolve().parent.parent
    commit = _git(root, "log", "-1", "--format=%H", "--", *SOURCE_ONLY)
    if not commit:
        return UNVERSIONED
    described = _git(root, "describe", "--tags", "--always", commit)
    if not described:
        return UNVERSIONED
    dirty = _git(root, "status", "--porcelain", "--", *SOURCE_ONLY)
    return described + (DIRTY_MARK if dirty else "")
