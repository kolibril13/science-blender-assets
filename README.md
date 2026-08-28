# science-blender-assets

A [remote asset library](https://docs.blender.org/manual/en/5.2/files/asset_libraries/remote_asset_libraries.html)
for Blender 5.2+, published to GitHub Pages.

## Using the library

1. In **Preferences → System → Network**, enable **Allow Online Access**
   (off by default — downloads silently do nothing without it).
2. In **Preferences → Asset Libraries**, press **+** and choose
   **Add Remote Asset Library**.
3. Paste this into the **URL** field:

```
https://kolibril13.github.io/science-blender-assets/
```

Assets then show up in the Asset Browser and Asset Shelf, and are downloaded on
demand (right-click → *Download Asset*, or the download button on the asset).
Online libraries cannot be linked, so the import method is Append or Pack.

Opening that URL in a browser shows a landing page with the same instructions.

**When new assets are published**, Blender will not pick them up on its own:
select this library in the Asset Browser and use **Library → Refresh Remote
Listing**. The ⟳ button next to the library dropdown is a different action — it
only rereads the locally cached copy and never re-downloads.

## Layout

`assets/` holds the library and nothing else. Everything needed to publish it —
including the landing page, written inline by the workflow — lives under
`.github/`. Blender and browsers both read from the same site root
(`<url>/_asset-library-meta.json` and `<url>/index.html`), so the workflow
assembles that root at build time.

| Path | Committed? | What it is |
| --- | --- | --- |
| `assets/` | yes | The asset library, and nothing else |
| `assets/*.blend` | yes | The assets themselves |
| `assets/blender_assets.cats.txt` | yes | Catalog definitions |
| `assets/_asset-library-meta.json` | yes | Library name + contact details |
| `.github/workflows/build-asset-library.yml` | yes | The build; also contains the landing page, written out during the *Stage site* step |
| `.github/scripts/verify_listing.py` | yes | Pre-publish check run by CI |
| `_site/` | no | `assets/` + the landing page + the generated listing — this is what gets published |

`assets/` is never written to by a build: the generator rewrites its metadata
file and drops `_v1/` and `*_thumbnails/` beside the `.blend` files, so it runs
against the throwaway `_site/` copy instead.

## Adding an asset

1. Add a `.blend` file under `assets/`, with its data-blocks marked as assets
   and assigned to a catalog.
2. **Pack all external dependencies** into the `.blend` (*File → External Data →
   Pack Resources*). Each file must be usable on its own — remote libraries
   download one `.blend` at a time and will not fetch linked files.
3. Give each asset a preview image, so it is not a blank square in the browser.
4. Commit and push to `main`. CI regenerates the listing and redeploys.

## Building locally

Normally you do not need to — pushing to `main` rebuilds and redeploys. To check
the library itself before pushing:

```bash
mkdir -p _site
cp -R assets/. _site/
blender -b --factory-startup -c asset_listing generate _site
python3 .github/scripts/verify_listing.py _site
```

Then serve it and point Blender at `http://127.0.0.1:8000/`:

```bash
python3 -m http.server --directory _site
```

That gives you a working library without the landing page, which only CI writes.
To preview the page too, copy it out of the *Stage site* step in the workflow.

Note that `blender` has to be the actual executable — on macOS that is
`/Applications/Blender.app/Contents/MacOS/Blender`.

## How CI works

[`.github/workflows/build-asset-library.yml`](.github/workflows/build-asset-library.yml)
runs on every push to `main`, on pull requests, and on manual dispatch:

1. Installs Blender 5.2.
2. Stages `assets/` into `_site/` and writes `index.html` alongside it.
3. Runs `asset_listing generate` over `_site/`.
4. Verifies the result with `.github/scripts/verify_listing.py`, which re-hashes
   every referenced `.blend` and thumbnail, checks the index and page counts
   agree, and fails if the library is empty or the contact details are still the
   generator's placeholders.
5. Uploads `_site/` as a Pages artifact and deploys it.

Pull requests build and verify but do not deploy.

### One-time setup

Under **Settings → Pages**, set **Source** to **GitHub Actions**.

GitHub Pages satisfies what Blender requires of the server: it sends
`Content-Length`, ignores query strings (Blender requests files as
`grid.blend?hash=…`), and supports `ETag`/`Last-Modified` so the periodic
listing sync usually costs a `304`.

