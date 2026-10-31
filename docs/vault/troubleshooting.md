# Known Issues & Troubleshooting (Anti-Loop Memory)

## 1. RCON `hud reload` tidak merespon
- **Penyebab**: Class BetterHUD memetakan RCON sender ke null.
- **Solusi**: Pakai command bridge Skript `/vn reloadhud` di `story_core.sk`. Jangan coba RCON langsung lagi.

## 2. Popup font generator terpotong / file font tidak keluar
- **Penyebab**: File layout mengandung custom tag placeholder yang tidak terdaftar (contoh: `[TEST]` di `fade-solo.yml`), melempar `RuntimeException` dan menghentikan seluruh generator loop.
- **Solusi**: Cek file layout di folder `server/plugins/BetterHud/layouts/` dengan regex `\[.*?\]`. Hapus placeholder invalid.

## 3. Teks bergeser horizontal saat kalimat bertambah panjang
- **Penyebab**: Layout memakai `align: center`. Formula: `(width - maxWidth) * 0.5`.
- **Solusi**: Kunci `align: left` di layout YAML.
