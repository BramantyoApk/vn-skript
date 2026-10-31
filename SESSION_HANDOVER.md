# Handover Dokumen: Perbaikan Visual Novel Dialogue BetterHUD

Dokumen status teknis, investigasi akar masalah, perbaikan sistemik, dan instruksi sesi baru.

---

## 1. Ringkasan Eksekutif

| Komponen | Status Sebelum | Status Akhir |
|---|---|---|
| **Eksekusi RCON `/hud reload`** | Gagal / no-op | Teratasi via bridge Skript `/vn reloadhud` |
| **Generasi Font Popup** | Terpotong / abort di tengah loop | Bersih, 5.697MB pack terkompilasi penuh |
| **Layer `bottom_cinematic_fade`** | Tidak muncul | Masuk font `popup_vn_dialog_image.json` & render |
| **Alignment Dialog** | Jitter akibat pergeseran text width | Stabil (`align: left`, `offset: center`) |
| **Sinkronisasi Client** | Pack usang / desync | Ter-pack di `BetterHud_Pack.zip` & RSPM live |

---

## 2. Investigasi & Akar Masalah (Root Causes)

### A. RCON Command Failure (`/hud reload`)
* **Penyebab**: Class dispatcher command BetterHUD melakukan `instanceof` eksplisit terhadap `CraftConsoleCommandSender` (tipe `0`) dan `Player` (tipe `1`). Koneksi RCON mengirimkan `RemoteConsoleCommandSender`, dipetakan ke `null` sehingga eksekusi diabaikan tanpa pesan error.
* **Solusi**: Dibuat bridge command di `story_core.sk`:
  ```skript
  command /vn reloadhud:
      permission: op
      trigger:
          execute console command "hud reload"
  ```
  Pemanggilan via RCON dialihkan ke `vn reloadhud`.

### B. Font Generator Abort (Fade Layer Hilang)
* **Penyebab**: File `layouts/fade-solo.yml` memakai sintaks `[TEST]`. Method `PopupManagerImpl.reload` mengevaluasi tag placeholder dan melempar `RuntimeException: this placeholder not found: TEST`. Exception ini memutus iterasi registrasi popup alfabetis berikutnya sebelum font fade selesai dikompilasi ke zip.
* **Solusi**: Hapus sintaks invalid dari `fade-solo.yml` dan re-run pipeline.

### C. Text Width Jitter & Pergeseran Koordinat
* **Penyebab**: Formula internal `LayoutComponentContainer`:
  $$\text{offset} = (\text{width} - \text{maxWidth}) \times \text{align.offset}$$
  Bila `align: center`, variabel `align.offset` bernilai $0.5$. Setiap perubahan panjang karakter string dialog mengubah nilai `width`, memicu pergeseran horizontal dinamis pada elemen box dan portrait.
* **Solusi**: Konfigurasi layout dikunci ke:
  * `align: left` $\to$ nilai `align.offset` $= 0.0$ (menghilangkan jitter lebar teks).
  * `offset: center` $\to$ posisi root container tetap di tengah layar pemain.

---

## 3. Topologi File & Direktori Penting

* **Dokumentasi Detail Renderer**: `VISUAL_NOVEL_DIALOG_FIX.md`
* **Authoritative Coordinate Registry**: `data/hud_config.yml`
* **Layout Generator & Pack Sync Tool**: `tools/compiler.py`
* **RCON Execution Tool**: `tools/send_rcon.py`
* **Bridge Script Konsol**: `../../server/plugins/Skript/scripts/story/story_core.sk`
* **Compiled Layouts**:
  * `../../server/plugins/BetterHud/layouts/vn-dialog-layout.yml`
  * `../../server/plugins/BetterHud/layouts/vn-fade-layout.yml`
  * `../../server/plugins/BetterHud/popups/vn-dialog-popup.yml`
* **Distribution Targets**:
  * Server pack: `../../server/plugins/BetterHud/build.zip`
  * RSPM Host: `http://127.0.0.1:25566/rspm.zip`
  * Client pack: `C:\ATLauncher\instances\262\resourcepacks\BetterHud_Pack.zip`

---

## 4. Isi Terverifikasi Font `popup_vn_dialog_image.json`

Entry bitmap yang terdaftar dan terpetakan di `build.zip`:
1. `betterhud:image_dialog_bottom_cinematic_fade.png` (ascent: -8433520, height: 170)
2. `betterhud:image_dialog_dialogue_box.png` (ascent: -8441774, height: 59)
3. `betterhud:image_dialog_portrait_bob_*` (`biasa`, `bahagia`, `marah`, `sedih`, `unique`)
4. `betterhud:image_dialog_portrait_luna_*` (`biasa`, `bahagia`, `marah`, `sedih`, `unique`)
5. `betterhud:image_dialog_nameplate.png`

---

## 5. Prosedur Operasional Sesi Baru

Bila membuka sesi baru, gunakan urutan verifikasi berikut:

1. **Sinkronisasi Client Resource Pack:**
   * Di client Minecraft (ATLauncher 1.26.2): Buka menu `Options` $\to$ `Resource Packs` $\to$ klik `Done` (reload pack dari disk).
2. **Uji Coba Dialog Tunggal:**
   ```bash
   python tools/send_rcon.py "dialog send Bramanzero Luna Halo selamat datang di lembah!"
   ```
   *Periksa visual*: Cinematic fade hitam di layer bawah, dialogue box abu/transparan, portrait Luna di kiri, nameplate di atas box, dan teks dialog.
3. **Uji Coba Interaktif NPC:**
   ```bash
   python tools/send_rcon.py "vn test"
   # atau
   python tools/send_rcon.py "dialog changelog me"
   ```
4. **Bila Ada Perubahan Koordinat/Aset:**
   * Edit konfigurasi di `data/hud_config.yml`.
   * Jalankan compiler:
     ```bash
     python tools/compiler.py
     ```
   * Trigger reload via bridge console:
     ```bash
     python tools/send_rcon.py "vn reloadhud"
     ```
   * Jalankan sinkronisasi pack client:
     ```bash
     python -c "import sys; sys.path.insert(0, 'tools'); from compiler import sync_client_pack; print(sync_client_pack())"
     ```
