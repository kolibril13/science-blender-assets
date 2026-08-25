# science-blender-assets

A [remote asset library](https://docs.blender.org/manual/en/5.2/files/asset_libraries/remote_asset_libraries.html)
for Blender 5.2+, published to GitHub Pages.

## Using the library

In Blender, go to **Preferences → Asset Libraries**, add a remote library, and paste:

```
https://kolibril13.github.io/science-blender-assets/
```

Assets then show up in the Asset Browser and Asset Shelf, and are downloaded on
demand (right-click → *Download Asset*, or the download button on the asset).

## Layout

| Path | Committed? | What it is |
| --- | --- | --- |
| `assets/` | yes | The library root — this directory is what gets published |
| `assets/*.blend` | yes | The assets themselves |
| `assets/blender_assets.cats.txt` | yes | Catalog definitions |
| `assets/_asset-library-meta.json` | yes | Library name + contact details |
| `assets/index.html` | yes | Landing page shown when the URL is opened in a browser |
| `assets/_v1/` | no | Generated listing (asset index + pages) |
| `assets/*_thumbnails/` | no | Generated WebP preview images |

The generated files are rebuilt by CI on every push and never committed.

## Adding an asset

1. Add a `.blend` file under `assets/`, with its data-blocks marked as assets
   and assigned to a catalog.
2. **Pack all external dependencies** into the `.blend` (*File → External Data →
   Pack Resources*). Each file must be usable on its own — remote libraries
   download one `.blend` at a time and will not fetch linked files.
3. Give each asset a preview image, so it is not a blank square in the browser.
4. Commit and push to `main`. CI regenerates the listing and redeploys.

## Building locally

```bash
blender -b --factory-startup -c asset_listing generate assets
python3 .github/scripts/verify_listing.py assets
```

To serve it and point Blender at `http://127.0.0.1:8000/`:

```bash
python3 -m http.server --directory assets
```

Re-run the generator whenever an asset or catalog changes — including a plain
re-save, since the listing records a hash of every file.

## How CI works

[`.github/workflows/build-asset-library.yml`](.github/workflows/build-asset-library.yml)
runs on every push to `main`, on pull requests, and on manual dispatch:

1. Installs Blender 5.2.
2. Runs `asset_listing generate` over `assets/`.
3. Verifies the result with `.github/scripts/verify_listing.py`, which re-hashes
   every referenced `.blend` and thumbnail, checks the index and page counts
   agree, and fails if the library is empty or the contact details are still the
   generator's placeholders.
4. Uploads `assets/` as a Pages artifact and deploys it.

Pull requests run steps 1–3 but do not deploy.

### One-time setup

Under **Settings → Pages**, set **Source** to **GitHub Actions**.

GitHub Pages satisfies what Blender requires of the server: it sends
`Content-Length`, ignores query strings (Blender requests files as
`grid.blend?hash=…`), and supports `ETag`/`Last-Modified` so the periodic
listing sync usually costs a `304`.
