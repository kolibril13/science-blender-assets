"""Run in background Blender after staging the asset library."""
import hashlib
import json
import os
from pathlib import Path
import sys

import bpy

sys.path.insert(0, os.environ["GALLERY_PACKAGES"])
from nodebpy.export import to_python
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

root = Path(os.environ["SITE_DIR"]).resolve()
output = root / "nodebpy"
output.mkdir(exist_ok=True)
formatter = HtmlFormatter(style="friendly")
styles = formatter.get_style_defs(".highlight")
supported = {"GeometryNodeTree", "ShaderNodeTree", "CompositorNodeTree"}


def trees(asset):
    if isinstance(asset, bpy.types.NodeTree):
        yield asset
    elif isinstance(asset, bpy.types.Material):
        yield asset.node_tree
    else:
        for modifier in asset.modifiers:
            yield getattr(modifier, "node_group", None)
        for slot in asset.material_slots:
            if slot.material:
                yield slot.material.node_tree


entries = []
for path in sorted(root.rglob("*.blend")):
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
    for collection in (bpy.data.node_groups, bpy.data.materials, bpy.data.objects):
        for asset in collection:
            if not asset.asset_data or asset.library:
                continue
            sources = []
            for tree in dict.fromkeys(trees(asset)):
                if tree and tree.bl_idname in supported:
                    try:
                        source = to_python(tree, format=False)
                        compile(source, tree.name, "exec")
                    except Exception as exc:
                        print(f"Skipping {path.name} / {asset.name} / {tree.name}: {exc}", flush=True)
                        break
                    sources.append(source.rstrip())
            else:
                if sources:
                    code = "\n\n".join(sources) + "\n"
                    digest = hashlib.sha256(code.encode()).hexdigest()
                    (output / f"{digest}.py").write_text(code, encoding="utf-8")
                    preview = highlight(code, PythonLexer(), formatter)
                    (output / f"{digest}.html").write_text(
                        '<meta charset="utf-8"><style>body{background:white;color:#222}pre{line-height:1.5}'
                        + styles + "</style>" + preview, encoding="utf-8")
                    entries.append([path.relative_to(root).as_posix(), asset.id_type, asset.name, digest])

(output / "index.json").write_text(json.dumps(entries), encoding="utf-8")
print(f"Exported nodebpy source for {len(entries)} assets")
