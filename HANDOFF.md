# Terrain Press: handoff

## Goal
Generate stylized map and topography assets of real Southeast Asian provinces. The look is based on a mood board reference: a sage green textured map with contour lines, a lime pill label ("Flower Found"), mono coordinate microtext, halftone and grid motifs. Output is for Project Pluto brand and client work.

## Current state (v1, browser artifact)
A single file, `terrain-press.html` (about 1.6 MB, boundaries embedded), is published as a claude.ai artifact: https://claude.ai/artifact/WyM6pbShrD2XpHU9Pww5or

The source is `template.html`, with a `__DATA__` placeholder that `prep_data.py` fills.

**Stack:**
* d3 7.9.0 via cdnjs, used for geoMercator, geoPath and contours.
* geotiff 2.1.3 via jsDelivr `dist-browser`, which exposes the global `GeoTIFF`.

**Features:**
* **Region pickers:** country, then province or "whole country". Covers 11 countries and 384 ADM1 regions.
* **5 styles:**
  * Atlas: land fill, dot pattern, contours with every 5th as an index line.
  * Contour.
  * Halftone: hex dot grid, radius driven by hillshade and elevation.
  * Ridges: occluding ridgelines.
  * Bands: hypsometric fills, interpolated in Lab color.
* **Palettes:** 7 presets from the Pluto token file (Plutonium, Cryogenic, Starlight, Scarlet, Cyber night, Ultraviolet) plus "Field", which matches the reference. Each preset has four colors: paper, land, ink and chip.
* **Controls:** resolution, line count, smoothing, relief exaggeration, dot or row gap, padding, and artboard ratio (1:1, 4:5, 16:9, 3:4).
* **Overlays:** outline, neighbouring provinces, pin label, coordinates plus elevation range plus contour interval, a scale bar in km, grid, grain and transparent background.
* **Export:**
  * Copy SVG to the clipboard, ready to paste into Figma.
  * Render a 2x PNG in a modal; the user right-clicks to save it. Artifact sandboxes block downloads, so there is no download button.

**Elevation pipeline:**
1. The user loads a GeoTIFF in EPSG:4326.
2. The page samples it with bilinear interpolation, 4 subsamples per grid cell.
3. Cells outside the region are masked using a canvas rasterization of the province path.
4. Optional box blur.
5. d3.contours over the grid.

The page builds an OpenTopography `globaldem` download URL from the region bbox plus 0.08°. It uses COP90 for small areas and SRTM15Plus when the bbox is larger than 40 sq deg. A free API key is required; it is kept in localStorage.

**Fallback:** with no DEM loaded, the page generates "stylized relief" from a chamfer distance-to-edge field plus seeded fBm noise. It is labelled on the artboard as "STYLIZED RELIEF · NOT MEASURED". Do not remove this label, because it keeps fake terrain from being presented as real.

**Verified:**
* Headless Chrome render of every style.
* A synthetic GeoTIFF (zlib, EPSG:4326) loaded end to end.

**Not verified:** an actual OpenTopography download.

## Why it's an artifact and why to move
* **The artifact sandbox has two hard limits.** The CSP blocks all `fetch`, so elevation cannot be pulled automatically. Downloads are blocked, which is why export is clipboard plus image only.
* **The cloud workspace could not reach elevation tile hosts either.** AWS Terrarium tiles, NOAA and Zenodo were all blocked. Of the GitHub hosts, only raw.githubusercontent works, and geoBoundaries there is stored in git LFS, so only pointer files come back.
* **Claude Code on the Mac removes all of these limits.**

## Next steps (priority order)
1. **Fix Vietnam boundaries.** Natural Earth has the old 63 provinces; Vietnam has 34 since 1 July 2025. Either:
   * dissolve the old polygons using the official merger list (verify the list from a government source, not from memory), or
   * pull a current dataset.

   Indonesia is also stale: it shows 33 provinces, and there are 38 since 2022. The Philippines data mixes provinces and cities.
2. **Automatic elevation.** Fetch AWS Terrarium tiles at `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`, decoded as `height = R*256 + G + B/256 - 32768`. No key is needed. Options:
   * a Node or Python CLI, or
   * a local dev server, so the existing UI keeps working.
3. **Swap in better boundaries:** geoBoundaries via its API or GitHub releases, which avoids the LFS problem, or GADM. This also opens up ADM2 (district) level.
4. **Real file export:** SVG, PNG and layered SVG with named groups (paper, land, contours, overlays) for Figma or Affinity.
5. **Optional:** a batch mode that renders every province of a country with one palette and style.
6. **Polish:** halftone looks harsh on the stylized relief, which may not matter with real data. Ridges row spacing interacts with relief exaggeration. The hillshade aspect math is approximate.

## Files
* `template.html`: the full app (UI, rendering, export) with the `__DATA__` placeholder.
* `prep_data.py`: Natural Earth 10m admin1 to compact JSON. It keeps 3 decimals, rewinds rings for d3, and injects the data into the template.
* `terrain-press.html`: the built page.

## Constraints and preferences
* Brand palette source: `project-pluto-brand-colors.tokens.json`, kept in the claude.ai Project.
* Copy in the UI is plain, with no em dashes.
* Keep the measured vs stylized distinction visible on every output.

## v2 changes (2026-11-08)
* **Vietnam is now 34 provinces.** Source: github.com/ThangLeQuoc/vietnamese-provinces-database `json/geojson/*/*.geojson`, derived from the official sapnhap.bando.com.vn map. `prep_data.py` takes that folder as a 4th argument and replaces the Natural Earth VNM rows. Names are NFC-normalized. Indonesia (33 vs 38) and the Philippines are still stale.
* **Automatic elevation.** AWS Terrarium tiles are fetched in the browser (the bucket sends CORS `*`). Zoom is picked so that 48 tiles or fewer cover the bbox (z9 to z10 for a province). Sampling is Mercator aware. Toggle: "Fetch automatically". A loaded GeoTIFF still works. The DEM name is printed on the artboard.
* **Land cover layers:** cities (WorldCover class 50, built-up), plant density (stipple weighted by class: tree and mangrove 1, shrub .6, wetland .5, grass and crop .35; a land cover proxy, not NDVI), and water (class 80). The source is the ESA WorldCover 2021 COGs on S3, read with geotiff.js. That bucket sends no CORS headers, so `serve.py` proxies range requests to it (allowlisted to that one host). SVG groups: `#plants`, `#water`, `#cities`.
* `<meta charset="utf-8">` was added; without it, local copies decoded as Windows-1252.
* Run: `python3 serve.py`, then open http://localhost:8787/terrain-press.html. In the claude.ai artifact, fetches are blocked, so v2 only works locally.
* **Draw area** (v2.1): drag a box on the map to render any rectangle (e.g. around a river) instead of a province. Microtext shows the box bounds.
* **v2.2:** lasso (freehand polygon) replaces the box; drag to pan, wheel or +/− to zoom, Fit resets. Zooming in refetches finer DEM, land cover and imagery for the visible area. New styles: Heat (topo gradient with hillshade), Outline, Photo (Esri World Imagery, Sentinel-2 cloudless 2016, OSM, OpenTopoMap via serve.py). Ramps section: topo low/high, plants low/high, water color; plants as heat map, solid bands or dots. Water now has a darker shoreline and ripple lines.
* **Live:** GitHub Pages deploys `terrain-press.html` as `index.html` on every push to main (`.github/workflows/pages.yml`). Land cover and Photo go through the Cloudflare Worker in `worker/proxy.js` (host and origin allowlists); set its URL in `RELAY` in template.html. On localhost the page still uses serve.py.
* **v3:** look model is Fill (flat land, elevation, plant density, photo, none) × Fill type (gradient, solid bands) × Lines (contours, halftone dots, ridgelines, none), plus Water and Cities. The 9 preset buttons only set those three. Fill ramp and water derive from the palette; "Custom fill and water colors" overrides them. Pan and zoom preview with a CSS transform and re-render 260 ms after input stops. Lasso points are thinned and Chaikin-smoothed.
* **v3.1 brand colors:** `brand-colors.json` holds the Pluto token sets (2026 first, then 2024 core, 2024 legacy; 464 swatches) and is embedded at build via `__COLORS__`. All 7 color slots (paper, land, ink, chip, fill low, fill high, water) open a token-only picker. The 10 themes are built from tokens only (checked with console.assert at startup); clicking a theme also switches to the look it is tuned for.
