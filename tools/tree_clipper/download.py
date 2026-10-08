"""Download every public Tree Clipper asset (data + preview) from tree-clipper.com."""
import json, os, urllib.request, urllib.parse

BASE = "https://tree-clipper.com"
# Downloads are a rebuildable cache (gitignored), not part of the library.
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cache")

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tree-clipper-library-export"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

entries, offset = [], 0
while True:
    page = json.loads(get(f"{BASE}/api/entries?limit=100&offset={offset}"))
    entries += page
    if len(page) < 100:
        break
    offset += 100

os.makedirs(os.path.join(HERE, "images"), exist_ok=True)
assets = []
for e in entries:
    a, s = e["author"], e["slug"]
    full = json.loads(get(f"{BASE}/api/asset/{urllib.parse.quote(a)}/{urllib.parse.quote(s)}"))
    full.pop("user_id", None)
    img = full.get("image_data")
    if img:
        ext = os.path.splitext(urllib.parse.urlparse(img).path)[1] or ".jpg"
        path = os.path.join(HERE, "images", f"{a}--{s}{ext}")
        try:
            with open(path, "wb") as f:
                f.write(get(img))
            full["image_file"] = path
        except Exception as ex:
            print(f"image failed for {a}/{s}: {ex}")
    assets.append(full)
    print(f"ok {a}/{s}")

with open(os.path.join(HERE, "assets.json"), "w") as f:
    json.dump(assets, f, indent=1)
print(f"downloaded {len(assets)} assets")
