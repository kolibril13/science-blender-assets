"""Convert downloaded Tree Clipper assets into a Blender asset library.

Run download.py first, then:
  blender --background --factory-startup --python tools/tree_clipper/build_library.py
Rewrites assets/tree_clipper/*.blend (one per asset) and the Tree Clipper
entries in assets/blender_assets.cats.txt; other catalogs are left untouched.
Needs the Tree Clipper extension installed in Blender 5.2.
"""
import base64, gzip, json, os, re, sys, traceback, uuid
from pathlib import Path

import bpy
import numpy as np

EXT = Path.home() / "Library/Application Support/Blender/5.2/extensions/blender_org/tree_clipper"
sys.path.insert(0, str(EXT))
from _vendor.tree_clipper.import_nodes import ImportIntermediate, ImportParameters  # noqa: E402
from _vendor.tree_clipper.specific_handlers import BUILT_IN_IMPORTER  # noqa: E402

SOURCE = Path(__file__).resolve().parent / "_cache"
REPO = Path(__file__).resolve().parents[2]
CATS_FILE = REPO / "assets" / "blender_assets.cats.txt"
LIBRARY = REPO / "assets" / "tree_clipper"
PREVIEW = 256

CATALOGS = {
    "geonodes": "Tree Clipper/Geometry Nodes",
    "shader": "Tree Clipper/Shader",
    "compositor": "Tree Clipper/Compositor",
    None: "Tree Clipper/Other",
}
NS = uuid.UUID("7a1b2c3d-0000-4000-8000-74726565636c")
def catalog_id(path):
    return str(uuid.uuid5(NS, path))

def write_catalogs():
    paths = set()
    for p in CATALOGS.values():
        parts = p.split("/")
        paths.update("/".join(parts[: i + 1]) for i in range(len(parts)))
    ours = {f"{catalog_id(p)}:{p}:{p.replace('/', '-')}" for p in paths}
    # Keep every catalog line that isn't ours, then append ours in sorted order.
    kept = [l for l in CATS_FILE.read_text().splitlines() if l.split(":", 1)[0] not in {o.split(":", 1)[0] for o in ours}]
    while kept and not kept[-1].strip():
        kept.pop()
    CATS_FILE.write_text("\n".join(kept + sorted(ours, key=lambda l: l.split(":")[1])) + "\n")

def set_preview(idblock, image_file):
    img = bpy.data.images.load(image_file, check_existing=False)
    try:
        w, h = img.size
        if not w or not h:
            return
        s = PREVIEW / max(w, h)
        nw, nh = max(1, round(w * s)), max(1, round(h * s))
        img.scale(nw, nh)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(nh, nw, 4)
        canvas = np.zeros((PREVIEW, PREVIEW, 4), dtype=np.float32)
        y0, x0 = (PREVIEW - nh) // 2, (PREVIEW - nw) // 2
        canvas[y0 : y0 + nh, x0 : x0 + nw] = px
        prev = idblock.preview_ensure()
        prev.image_size = (PREVIEW, PREVIEW)
        prev.image_pixels_float = canvas.ravel()
    finally:
        bpy.data.images.remove(img)

def build(asset):
    intermediate = ImportIntermediate(string=asset["asset_data"])
    externals = []
    for ext_id, item in intermediate.get_external().items():
        if item["description"] is None:
            continue
        # Scene references need a real scene; everything else is left unassigned.
        externals.append((int(ext_id), bpy.context.scene if item.get("scene_id") is not None else None))
    intermediate.set_external(iter(externals))

    report = intermediate.import_all(ImportParameters(specific_handlers=BUILT_IN_IMPORTER, debug_prints=False))

    datablocks = {bpy.data.node_groups[n] for n in report.renames_node_group.values()}
    if report.rename_material is not None:
        root = bpy.data.materials[report.rename_material[1]]
        datablocks.add(root)
    else:
        root = report.last_getter()

    root.name = asset["title"]
    root.asset_mark()
    meta = root.asset_data
    meta.author = asset["author"]
    meta.description = (asset.get("description") or "") + f"\n\nhttps://tree-clipper.com/{asset['author']}/{asset['slug']}"
    meta.catalog_id = catalog_id(CATALOGS.get(asset.get("node_type"), CATALOGS[None]))
    meta.tags.new(asset["author"], skip_if_exists=True)
    if asset.get("node_type"):
        meta.tags.new(asset["node_type"], skip_if_exists=True)
    if asset.get("image_file"):
        set_preview(root, asset["image_file"])

    out = LIBRARY / f"{asset['author']}--{asset['slug']}.blend"
    bpy.data.libraries.write(str(out), datablocks, path_remap="NONE", fake_user=True, compress=True)

    for db in datablocks:
        (bpy.data.node_groups if isinstance(db, bpy.types.NodeTree) else bpy.data.materials).remove(db)
    return report

LIBRARY.mkdir(parents=True, exist_ok=True)
for stale in LIBRARY.glob("*.blend"):
    stale.unlink()
write_catalogs()
assets = json.loads((SOURCE / "assets.json").read_text())
failed = []
for a in assets:
    key = f"{a['author']}/{a['slug']}"
    try:
        r = build(a)
        print(f"OK   {key}  ({r.imported_trees} trees, {r.imported_nodes} nodes)" + (f"  warnings: {r.warnings}" if r.warnings else ""))
    except Exception as ex:
        failed.append(key)
        print(f"FAIL {key}: {type(ex).__name__}: {ex}")
        traceback.print_exc(limit=3)
print(f"\nDONE: {len(assets) - len(failed)}/{len(assets)} converted. Failed: {failed}")
