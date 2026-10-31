# HUD & Layout Coordinate Registry

## Layout Formula
- `align: left` -> `align.offset = 0.0` (Anti-jitter text width).
- `offset: center` -> Center container ke root layar (`-max / 2 = -126px` untuk `dialogue_box.png` lebar 253px).
- Vertical baseline formula: `oy + vh - int(88 * sc)` (mengompensasi `pixel.y = -78` dan vertex shader `DEFAULT_OFFSET = 10`).
- Portrait trimming: BetterHUD `removeEmptySide` memotong alpha transparan menjadi 98x127 glyph dengan `xOffset = 20`. Story Studio menghitung bounding box dan seleksi visual identik pada `sel_x, sel_y, sel_w, sel_h`.

## Source of Truth
- File konfigurasi paten: `data/hud_config.yml`.
- Generated BetterHUD layout:
  - `server/plugins/BetterHud/layouts/vn-dialog-layout.yml`
  - `server/plugins/BetterHud/layouts/vn-fade-layout.yml`
  - `server/plugins/BetterHud/popups/vn-dialog-popup.yml`

## Bitmap IDs di `popup_vn_dialog_image.json`
- `\U000ce002`: `bottom_cinematic_fade.png` (ascent: -8433520, height: 170)
- `\U000ce003`: `dialogue_box.png` (ascent: -8441774, height: 59)
- `\U000ce004` - `\U000ce008`: Portrait Bob (`biasa`, `bahagia`, `marah`, `sedih`, `unique`)
- `\U000ce009` - `\U000ce00d`: Portrait Luna (`biasa`, `bahagia`, `marah`, `sedih`, `unique`)
- `\U000ce00e`: `nameplate.png`
