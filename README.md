# 🍃 LeafScan

A browser-based plant health analysis tool. Upload leaf images, tune HSV thresholds interactively, and export per-leaf disease statistics as CSV — no installation required.

**Live app:** https://leonlenzo.github.io/leaf-scan

---

## Features

- **Batch processing** — select multiple images and cycle through them with Prev / Next
- **Per-image settings** — slider values are saved per image so each photo can be tuned independently
- **Live preview** — preprocessed input and colour-coded analysis result update in real time as you adjust sliders
- **Analysis overlay** — healthy tissue shown in dark green, necrotic lesions in brown-red, chlorotic tissue in yellow
- **Accumulating results table** — leaves from all processed images appear in a single table, newest first
- **CSV export** — one row per leaf, including all slider values used, ready for downstream analysis
- **TIFF support** — accepts `.jpg`, `.png`, and `.tif`/`.tiff` files

---

## Usage

1. Open the app in a browser
2. Click **Choose Files** and select one or more leaf images (or Ctrl+click to pick several from a folder)
3. Adjust the sliders until the analysis overlay correctly identifies healthy, necrotic, and chlorotic tissue
4. Use **Next ▶** to move to the next image — settings from the current image are saved automatically
5. Click **Download CSV** when done

---

## Parameters

| Parameter | Description |
|---|---|
| Temperature Correction | Shifts red/blue balance to correct for camera white balance |
| Contrast | Stretches pixel values around the midpoint — helps separate lesions from healthy tissue |
| Necrosis (Brown) Max | Upper HSV hue limit for necrotic tissue (dead/brown lesions). Typically 10–25 |
| Chlorosis (Yellow) Max | Upper hue limit for chlorotic (yellowing) tissue. Typically 30–40 |
| Healthy (Green) Max | Upper hue limit for healthy tissue — also defines the leaf mask boundary. Keep below the hue of your background (e.g. ~75 for cyan paper) |
| Min Leaf Size | Minimum pixel area to be counted as a leaf — increase to filter out debris |

---

## Background colour

The tool works best with a uniform, distinct background. A bright cyan/turquoise paper works well — set **Healthy (Green) Max** to ~75 to exclude it from the leaf mask.

---

## Citation

If you use this tool in your research, please cite:

```
Lenzo, L., John, E., Bradley, J., Thomas, G., Bennett, D. and Tan, K.C., 2026.
Fair-weather friends. Sequential co-infection demonstrates priority effects in the
outcome of Parastagonospora nodorum and Pyrenophora tritici-repentis polymicrobial
foliar disease of wheat. Plant Disease.
```

---

## Legacy Python version

The original Python desktop application (CLI and GUI) is in the [`python/`](python/) directory.
