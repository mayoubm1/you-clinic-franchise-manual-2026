# YOU WELLNESS CLINIC — Global Standard Franchise Manual Portal

Interactive web portal + unified print document for the **V2.1.4 ELITE** manual (10 chapters).

## What this is

| Path | Purpose |
|---|---|
| `index.html` | **Interactive reader** (open directly — no server needed). Futuristic HUD: sidebar chapter nav, live search, Web Speech "Intercom" read-aloud, reading progress bar, Ctrl+K command palette, keyboard arrows, Print/PDF launcher. Dark UI around the manual's cream "paper" pages. |
| `master.html` | **Unified single document** for print / PDF export. All 10 chapters in one file, each starting on its own page. |
| `YOU_WELLNESS_CLINIC_PORTAL.pdf` | Pre-printed PDF built from `master.html` (34 pages). |
| `chapters/` | The 10 modular chapter files (`01-chapter.html` … `10-chapter.html`), cleaned sources for editing. |
| `chapters.json` | Chapters manifest (number / title / body) for other tooling. |
| `assets/reader_template.html` | Source template the build inks chapter content into. |
| `assets/js/viewer3d.js` | **Interactive Three.js as-built viewer** module (orbit / zoom, wireframe, auto-rotate, GLTF loader + procedural fallback tower). |
| `assets/models/` | Drop `.gltf`/`.glb` as-built models here; the viewer auto-loads them. |
| `build_portal.py` | Build script: cleans chapters, strips Gemini `[cite: N]` artifacts, scopes per-chapter CSS into `#chN` containers, and regenerates `index.html` + `master.html`. |
| `build.js` | Node shim for the build (runs `build_portal.py`) — used by CI. |
| `.github/workflows/deploy.yml` | GitHub Actions: compile on every push to `main`, deploy to GitHub Pages. |

## Rebuild

```
py build_portal.py        # or: node build.js
```

Rebuilds `master.html` and `index.html` from `chapters/`. Requires Python 3 only (no npm / node, no internet). `node build.js` wraps the same Python build for CI convenience.

## Interactive 3D as-built viewer

Every chapter can carry one or more interactive 3D widgets by adding this snippet anywhere in its HTML (a demo widget already ships in **Chapter 5**):

```html
<div class="asbuilt-3d-widget" data-gltf-src="assets/models/facility-as-built.gltf">
  <div class="hud-3d-overlay">
    <button class="hud-3d-btn" onclick="asBuiltManager.toggleWireframe(this)">Wireframe</button>
    <button class="hud-3d-btn" onclick="asBuiltManager.toggleAutoRotate(this)">Rotate</button>
    <button class="hud-3d-btn" onclick="asBuiltManager.resetCamera()">Reset View</button>
  </div>
  <div class="hud-3d-status">STATUS: <span class="status-text">INITIALIZING...</span></div>
</div>
```

- Drag to orbit, scroll to zoom, click the HUD buttons for wireframe / auto-rotate / reset.
- If `assets/models/<file>.gltf` exists it loads the real as-built model; otherwise a procedural low-poly "clinic tower" mock-up is shown (error-proof fallback).
- Uses Three.js from CDN via an import map (online required for the 3D canvas only; the rest of the portal works fully offline).
- Widgets are automatically hidden in `master.html` (print/PDF).

## GitHub Actions — auto deploy to GitHub Pages

The workflow `.github/workflows/deploy.yml` compiles and publishes on every push to `main`.

1. Push `manual-portal/` (or the whole repo) to a GitHub repository.
2. **Settings → Pages → Build and deployment → Source → GitHub Actions.**
3. Push to `main` → the Actions tab builds (`node build.js` → `build_portal.py`) and deploys.
4. Your live URL appears in the workflow summary: `https://<user>.github.io/<repo>/`.

## Print to PDF (browser)

1. Open `master.html`.
2. `Ctrl+P` → destination *Save as PDF* → print.

Headless Chrome:

```
chrome --headless --disable-gpu --no-pdf-header-footer ^
       --print-to-pdf=YOU_WELLNESS_CLINIC_PORTAL.pdf master.html
```

## Publish online

Fully static — no backend, all content is inlined (no `fetch`/CORS), works from `file://`.

- **GitHub Pages**: push to a repo, enable Pages (root or `/docs`), open `https://<user>.github.io/<repo>/`.
- **Vercel / Netlify**: drag-and-drop the folder (or point at the repo). No build command needed.
- **OneDrive / shared drive**: anyone can open `index.html` locally, or use any static file host.

## Interactive features

- **Voice / "It speaks"** — Web Speech API narration of the active chapter, section-by-section with live highlight and auto-scroll, voice & speed picker, pause/resume/stop.
- **Search** — live filter of all chapters by title or content; instant jump.
- **Command palette** — `Ctrl+K` to jump to any chapter or section.
- **Progress bar** — reading %, chapter chips, Next/Prev via `←` `→`.
- **HUD chrome** — telemetry counters (chapters / sections / words), animated status beacon, keyboard-first navigation.

## Next steps (ideas)

- Add **interactive hot-spot annotations** on the 3D models (label callouts for zones/equipment).
- Publish the sealed header/footer into the portal PDF's print pipeline for fully branded print-outs.
- Add a `docs/` release page with the 34-page PDF download.

© 2026 YOU WELLNESS CLINIC. All rights reserved.