"""Minimal reader for a STEP assembly, for boards that publish no board file.

TUL publish the PYNQ-Z2 as a SolidWorks STEP and nothing else machine-readable,
so its numbers have to come out of solids rather than out of footprints.  What
a mechanical drawing needs from such a model is small: the board slab and its
top face, the holes bored through that slab, and the placed bounding box of
each named part.  That is all this reads.

Built on OCP, the OpenCascade binding cadquery ships, which is the only free
STEP reader that keeps the assembly's part names.  Run whatever imports this
with ``uv run --with cadquery``.  Loading a 16 MB assembly takes a minute, so
callers should load once and ask everything they need of the result.

Coordinates come back in the model's own frame, millimetres, untransformed;
mapping them onto a board's lower-left origin is the extractor's job.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Solid:
    """One placed solid: the part name it came from, its volume and box."""

    name: str
    volume: float
    x0: float
    y0: float
    z0: float
    x1: float
    y1: float
    z1: float

    @property
    def box(self) -> tuple[float, float, float, float]:
        return self.x0, self.y0, self.x1, self.y1


@dataclass(frozen=True)
class Cylinder:
    """A vertical cylindrical face: a hole, or the outside of a post."""

    x: float
    y: float
    dia: float
    z0: float
    z1: float


class Model:
    def __init__(self, path: str) -> None:
        # Imported here, so that listing the module costs nothing and only
        # loading a model needs the 400 MB of OpenCascade behind it.
        from OCP.Bnd import Bnd_Box
        from OCP.BRepBndLib import BRepBndLib
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.STEPCAFControl import STEPCAFControl_Reader
        from OCP.TCollection import TCollection_ExtendedString
        from OCP.TDataStd import TDataStd_Name
        from OCP.TDF import TDF_Label, TDF_LabelSequence
        from OCP.TDocStd import TDocStd_Document
        from OCP.TopAbs import TopAbs_SOLID
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopLoc import TopLoc_Location
        from OCP.XCAFDoc import XCAFDoc_DocumentTool

        doc = TDocStd_Document(TCollection_ExtendedString("doc"))
        reader = STEPCAFControl_Reader()
        reader.SetNameMode(True)
        if reader.ReadFile(path) != IFSelect_RetDone:
            raise SystemExit(f"{path}: not a STEP file OpenCascade can read")
        reader.Transfer(doc)
        tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

        def name(label) -> str:
            attr = TDataStd_Name()
            if label.FindAttribute(TDataStd_Name.GetID_s(), attr):
                return attr.Get().ToExtString()
            return ""

        # Walk the assembly tree, accumulating each instance's placement, so
        # that a part used twice comes out twice at its two positions.
        placed: list[tuple[str, object]] = []

        def walk(label, loc) -> None:
            if tool.IsReference_s(label):
                ref = TDF_Label()
                tool.GetReferredShape_s(label, ref)
                here = loc.Multiplied(tool.GetLocation_s(label))
                parts = TDF_LabelSequence()
                tool.GetComponents_s(ref, parts)
                if parts.Length() == 0:
                    placed.append((name(ref), tool.GetShape_s(ref).Moved(here)))
                    return
                for i in range(1, parts.Length() + 1):
                    walk(parts.Value(i), here)
            elif tool.IsAssembly_s(label):
                parts = TDF_LabelSequence()
                tool.GetComponents_s(label, parts)
                for i in range(1, parts.Length() + 1):
                    walk(parts.Value(i), loc)
            else:
                placed.append((name(label), tool.GetShape_s(label).Moved(loc)))

        roots = TDF_LabelSequence()
        tool.GetFreeShapes(roots)
        for i in range(1, roots.Length() + 1):
            walk(roots.Value(i), TopLoc_Location())

        self._shapes: list[object] = []
        self.solids: list[Solid] = []
        for part_name, shape in placed:
            walker = TopExp_Explorer(shape, TopAbs_SOLID)
            while walker.More():
                solid = walker.Current()
                props = GProp_GProps()
                BRepGProp.VolumeProperties_s(solid, props)
                box = Bnd_Box()
                BRepBndLib.Add_s(solid, box, False)
                x0, y0, z0, x1, y1, z1 = box.Get()
                self.solids.append(Solid(part_name, props.Mass(),
                                         x0, y0, z0, x1, y1, z1))
                self._shapes.append(solid)
                walker.Next()

    def named(self, part_name: str) -> list[Solid]:
        return [s for s in self.solids if s.name == part_name]

    def largest(self) -> Solid:
        """The board: nothing else in a board assembly comes close."""
        return max(self.solids, key=lambda s: s.volume)

    def top_face(self, solid: Solid) -> tuple[float, tuple[float, float, float, float]]:
        """The largest Z-normal planar face of *solid*: its height and box.

        For a board slab that is the top or bottom surface, and its box is the
        board outline's bounding box.
        """
        from OCP.Bnd import Bnd_Box
        from OCP.BRepAdaptor import BRepAdaptor_Surface
        from OCP.BRepBndLib import BRepBndLib
        from OCP.BRepGProp import BRepGProp
        from OCP.GeomAbs import GeomAbs_Plane
        from OCP.GProp import GProp_GProps
        from OCP.TopAbs import TopAbs_FACE
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS

        shape = self._shapes[self.solids.index(solid)]
        best = None
        walker = TopExp_Explorer(shape, TopAbs_FACE)
        while walker.More():
            face = TopoDS.Face_s(walker.Current())
            surf = BRepAdaptor_Surface(face)
            if surf.GetType() == GeomAbs_Plane \
                    and abs(surf.Plane().Axis().Direction().Z()) > 0.99:
                props = GProp_GProps()
                BRepGProp.SurfaceProperties_s(face, props)
                if best is None or props.Mass() > best[0]:
                    best = (props.Mass(), face)
            walker.Next()
        if best is None:
            raise SystemExit(f"{solid.name}: no horizontal planar face")
        box = Bnd_Box()
        BRepBndLib.Add_s(best[1], box, False)
        x0, y0, z0, x1, y1, z1 = box.Get()
        return z0, (x0, y0, x1, y1)

    def outline_edges(self, solid: Solid) -> list[tuple]:
        """The straight edges bounding the top face, as ``(x1, y1, x2, y2)``.

        Only straight edges: a curved edge stops the extraction, because a
        board with rounded corners needs its arcs resolved and this reader
        has not had to do that yet.
        """
        from OCP.BRep import BRep_Tool
        from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
        from OCP.BRepGProp import BRepGProp
        from OCP.BRepTools import BRepTools
        from OCP.GeomAbs import GeomAbs_Line, GeomAbs_Plane
        from OCP.GProp import GProp_GProps
        from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
        from OCP.TopExp import TopExp, TopExp_Explorer
        from OCP.TopoDS import TopoDS, TopoDS_Vertex

        shape = self._shapes[self.solids.index(solid)]
        best = None
        walker = TopExp_Explorer(shape, TopAbs_FACE)
        while walker.More():
            face = TopoDS.Face_s(walker.Current())
            surf = BRepAdaptor_Surface(face)
            if surf.GetType() == GeomAbs_Plane \
                    and abs(surf.Plane().Axis().Direction().Z()) > 0.99:
                props = GProp_GProps()
                BRepGProp.SurfaceProperties_s(face, props)
                if best is None or props.Mass() > best[0]:
                    best = (props.Mass(), face)
            walker.Next()
        out = []
        edges = TopExp_Explorer(BRepTools.OuterWire_s(best[1]), TopAbs_EDGE)
        while edges.More():
            edge = TopoDS.Edge_s(edges.Current())
            if BRepAdaptor_Curve(edge).GetType() != GeomAbs_Line:
                raise SystemExit(f"{solid.name}: the outline has a curved "
                                 "edge, which this reader does not resolve")
            a, b = TopoDS_Vertex(), TopoDS_Vertex()
            TopExp.Vertices_s(edge, a, b)
            pa, pb = BRep_Tool.Pnt_s(a), BRep_Tool.Pnt_s(b)
            out.append((pa.X(), pa.Y(), pb.X(), pb.Y()))
            edges.Next()
        return out

    def cylinders(self, solid: Solid) -> list[Cylinder]:
        """Every vertical cylindrical face of *solid*, deduplicated.

        A drilled hole is one of these that runs the full thickness of the
        slab; so is the outside of a modelled post, which is why the caller
        filters on height as well as diameter.
        """
        from OCP.Bnd import Bnd_Box
        from OCP.BRepAdaptor import BRepAdaptor_Surface
        from OCP.BRepBndLib import BRepBndLib
        from OCP.GeomAbs import GeomAbs_Cylinder
        from OCP.TopAbs import TopAbs_FACE
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS

        shape = self._shapes[self.solids.index(solid)]
        found: dict[tuple, Cylinder] = {}
        walker = TopExp_Explorer(shape, TopAbs_FACE)
        while walker.More():
            face = TopoDS.Face_s(walker.Current())
            surf = BRepAdaptor_Surface(face)
            if surf.GetType() == GeomAbs_Cylinder \
                    and abs(surf.Cylinder().Axis().Direction().Z()) > 0.99:
                cyl = surf.Cylinder()
                box = Bnd_Box()
                BRepBndLib.Add_s(face, box, False)
                _, _, z0, _, _, z1 = box.Get()
                key = (round(cyl.Location().X(), 3), round(cyl.Location().Y(), 3),
                       round(2 * cyl.Radius(), 3), round(z0, 2), round(z1, 2))
                found[key] = Cylinder(*key)
            walker.Next()
        return sorted(found.values(), key=lambda c: (c.x, c.y, c.dia))

    def slab(self, solid: Solid) -> tuple[float, float]:
        """The bottom and top of the board slab: its two largest flat faces.

        Not the solid's own Z extent.  TUL's PYNQ-Z2 model fuses something
        14.5 mm tall into the board solid, so its bounding box says nothing
        about where the laminate ends; the two largest horizontal faces do.
        """
        from OCP.BRepAdaptor import BRepAdaptor_Surface
        from OCP.BRepGProp import BRepGProp
        from OCP.GeomAbs import GeomAbs_Plane
        from OCP.GProp import GProp_GProps
        from OCP.TopAbs import TopAbs_FACE
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS

        shape = self._shapes[self.solids.index(solid)]
        faces: list[tuple[float, float]] = []
        walker = TopExp_Explorer(shape, TopAbs_FACE)
        while walker.More():
            face = TopoDS.Face_s(walker.Current())
            surf = BRepAdaptor_Surface(face)
            if surf.GetType() == GeomAbs_Plane \
                    and abs(surf.Plane().Axis().Direction().Z()) > 0.99:
                props = GProp_GProps()
                BRepGProp.SurfaceProperties_s(face, props)
                faces.append((props.Mass(), surf.Plane().Location().Z()))
            walker.Next()
        faces.sort(reverse=True)
        if len(faces) < 2:
            raise SystemExit(f"{solid.name}: fewer than two horizontal faces")
        z = sorted((faces[0][1], faces[1][1]))
        return z[0], z[1]

    def through_holes(self, solid: Solid, dia_min: float, dia_max: float
                      ) -> list[Cylinder]:
        """Cylindrical faces that run the whole thickness of the slab."""
        lo, hi = self.slab(solid)
        return [c for c in self.cylinders(solid)
                if dia_min <= c.dia <= dia_max
                and c.z0 <= lo + 0.01 and c.z1 >= hi - 0.01]


def load(path: str) -> Model:
    return Model(path)
