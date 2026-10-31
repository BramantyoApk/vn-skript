# vn-skript

Visual Novel Dialogue & Story Engine untuk Minecraft Paper 26.2 (Skript + BetterHUD).

## Struktur Project
- `data/`: Konfigurasi karakter, alur dialog, dan `hud_config.yml`.
- `textures/`: Asset grafis VN (dialog box, portrait, fade, nameplate).
- `tools/`:
  - `story_studio.py`: Editor GUI visual novel.
  - `compiler.py`: Compiler layout, potret, Skript router, & sync pack.
- `build.bat`: Script 1-klik untuk kompilasi dan sync ke client pack.
- `story_core.sk`: Engine dialog in-game.

## Cara Menggunakan
1. Jalankan `build.bat` setelah mengubah konfigurasi atau dialog.
2. Di client Minecraft, tekan `F3 + T`.
3. Di server Minecraft, ketik `/vn reloadhud`.
