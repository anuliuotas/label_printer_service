# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the generator CLI
uv run python generator.py "Your Text" --width 600 --cut-marks

# Run the web app (http://localhost:5000)
uv run python web/app.py

# Run the test (generates label.png in test/ and POSTs to local endpoint)
uv run python test/test_post_label.py
```

## Architecture

The project has two entry points:

- `generator.py` — the core library and CLI. `generate_image()` is the main function; it creates a 64px-tall PNG with centered text. `draw_cut_marks()` draws dashed vertical lines at both horizontal edges.
- `test/test_post_label.py` — manual integration test that calls `generate_image()` directly, saves the result to `test/label.png`, and POSTs the raw PNG bytes to `http://localhost:8080/image/brother` (Brother label printer endpoint).

## Hardware

- Printer: **Brother PT-P300BT**
- Resolution: **180 × 180 DPI**
- Tape widths and corresponding image heights:
  - 12mm → **64px**
  - 9mm → **64px**
  - 6mm → **32px**
- **1 cm ≈ 71px** along the label length

## Requirements

- Multiline text is supported by splitting on `\n`. Font size is auto-fitted so all lines fill the image height equally. Lines are vertically centered as a block with `LINE_SPACING = 2px` between them.
- `width` is optional — omitting it makes the image fit the text width. An optional `padding` (px per side) adds horizontal space in this mode.
- `create_label()` in `generator.py` returns a PIL `Image` directly (used by the web app). `generate_image()` wraps it and saves to disk.
- Tape width is selectable (12mm/9mm/6mm); this sets the image `height` passed to `create_label`. The mapping lives in `TAPE_SIZES` in `generator.py`.
- The web app shows a cm ruler (SVG, 71px = 1cm) below each label preview and the combined image. Preview is shown at 3× scale, combined at 2×.
- When combining, an optional spacing (mm) is converted to px (×7.1) and inserted as white gaps between labels.

## Key constants

- `IMAGE_HEIGHT` in `generator.py` defaults to **64px** (12mm tape) — must match the loaded tape width.
- Default width is **256px**; the test uses **600px**.
- Fonts live in `fonts/` (currently `DejaVuSans.ttf`). Font size is auto-fitted to `IMAGE_HEIGHT` via binary search.
- Cut marks are dashed: 4px dash, 4px gap.
