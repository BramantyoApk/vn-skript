# Session State Checkpoint

| Key | Status | Catatan |
|---|---|---|
| **Server State** | Online | Paper 26.2 running (RCON port 25575 aktif) |
| **Fade Hitam (Layer 1)** | Fixed | Resolusi dibuat aman 256x64 (trimmed 256x62), scale 2.5, anti atlas drop |
| **Layer Hierarchy** | Fixed | Fade=1, Box=2, Port=3, Name=4, Text=5 (anti depth-fighting) |
| **RSPM Self-Host** | Fixed | Port 25566 live, `/rspm reload` aktifkan `/rspm.zip` (HTTP 200) |
| **Client Resource Pack** | Synced | 577 asset di `BetterHud_Pack.zip` (fade 256px terkompilasi) |
| **Story Studio GUI** | Synced | `bottom_cinematic_fade` terdaftar di combo list, drag-and-drop canvas, & layer 1 |
| **In-Game Rendering** | Issue | Box/portrait shifted ke kiri, nameplate tertutup, teks terlempar ke kanan, tofu di BossBar |

## Task Selanjutnya (Untuk Claude)
1. Perbaiki offset koordinat `vn_dialog_layout` di `tools/compiler.py` dan `data/hud_config.yml` agar dialog box & portrait kembali centered di layar seperti Story Studio.
2. Sinkronkan posisi X `dialog_text` dan `speaker_text` agar tertata di dalam bounding box `dialog_box`.
3. Telusuri dan eliminasi karakter missing glyph pada BossBar popup `vn_dialog` yang memicu tofu (`▯`).
4. Pastikan `nameplate` terlihat di layer depan (`layer: 4` di atas `dialog_box` layer 2).
