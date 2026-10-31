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

---

## 6. Laporan Bug: Disparitas Visual In-Game vs Story Studio

### A. Gejala Visual (Screenshot In-Game vs Preview Studio)
1. **Kotak Dialog & Potret Luna Tergeser ke Kiri**:
   - In-game: Dialogue box dan portrait terdorong jauh ke tepi kiri layar hingga terpotong.
   - Studio: Dialogue box berada tepat di tengah bawah layar (di atas hotbar), portrait menempel rapi di sisi kiri kotak.
2. **Nameplate & Speaker Hilang / Tertutup**:
   - In-game: Tekstur nameplate tidak terlihat atau berada di luar frame / tertutup layer lain.
   - Studio: Nameplate terpasang rapi di atas kiri kotak dialog dengan nama pembicara "Luna".
3. **Teks Dialog Terlempar Keluar Kotak**:
   - In-game: Teks `"Halo dari testdialog manual!"` merender jauh ke sebelah kanan di luar kotak dialog.
   - Studio: Teks terbungkus rapi di dalam area teks kotak dialog.
4. **Tofu Glyph (`▯`) di BossBar Atas**:
   - In-game: Muncul kotak tofu (`▯`) tepat di tengah atas BossBar.
   - Analisis: Terdapat karakter (spasi / unmapped glyph) pada title BossBar popup `vn_dialog` yang gagal dipetakan oleh font provider `betterhud:popup_vn_dialog_image` atau shader `text.vsh`.

### B. Akar Masalah Teknis (Root Causes)
1. **Perbedaan Basis Titik Koordinat (Origin Mismatch)**:
   - Story Studio (`tools/story_studio.py`):
     `base_origin_x = mid_x - int((box_w // 2) * dlg_box_scale * sc)`
     Seluruh elemen (`dialog_box`, `portrait`, `nameplate`, `dialog_text`) dihitung relatif terhadap `base_origin_x`.
   - BetterHUD Container (`LayoutComponentContainer.class`):
     Ketika layout di-set `align: left` dengan `offset: center`, titik awal bergeser `-max / 2` (-127 px), namun elemen teks (`TextRenderer`) memproses `this.x` terpisah dari image layout, menghasilkan offset horisontal yang tidak sinkron antara gambar dan teks.
2. **BossBar Title Missing Glyph**:
   - Root title BossBar dari `HudPlayerImpl` menggunakan font `betterhud:space` dan font popup `betterhud:popup_vn_dialog_image`. Karakter tertentu yang dikirim dalam packet BossBar tidak memiliki glyph bitmap / advance di atlas sehingga Minecraft merender fallback `▯` di posisi `(screen_width/2, 12)`.

### C. Panduan Pengerjaan untuk Claude
1. **Sinkronisasi Koordinat Layout (`tools/compiler.py` & `data/hud_config.yml`)**:
   - Selaraskan kalkulasi anchor dan offset antara `compiler.py` dan `story_studio.py`.
   - Uji apakah layout popup lebih stabil menggunakan `align: center` murni seperti pada `layouts/test-box.yml` (yang terbukti centered 1:1), atau sesuaikan formula `pixel.x` di compiler agar elemen teks tidak keluar dari bounding box dialog.
2. **Perbaikan Nameplate & Teks Pembicara**:
   - Pastikan koordinat `nameplate` dan `speaker_text` memiliki layer z-index dan koordinat lokal yang berada di atas `dialog_box`.
3. **Pembersihan BossBar Tofu (`▯`)**:
   - Identifikasi karakter persis yang memicu tofu pada title BossBar di Paper 26.2. Pastikan font provider mendaftarkan spasi atau karakter default agar tidak melempar missing glyph.

---

## 7. Investigasi Ghost Portraits & Fade Transparan (Update)

### A. Akar Masalah Potret Bertumpuk (Ghost Portrait Bob di Belakang Luna)
* **Penyebab**:
  - BetterHUD mengevaluasi string literal di blok `conditions` menggunakan regex `stringPattern`:
    ```kotlin
    Pattern.compile("'\\'(?<content>[\\w|\\W]+)\\\\)'")
    ```
  - Pada commit `3f8b098`, tanda petik satu dihapus (`second: speaker_name` dan `second: em`), menghasilkan YAML unquoted string: `second: Bob`.
  - Ketika `parse0` dieksekusi, `PlaceholderManagerImpl.find("Bob", source)` gagal menemukan placeholder bernama `Bob` dan melempar `RuntimeException("Cannot find placeholder: Bob")`.
  - Exception ini ditangkap oleh `runCatching` di `Conditions.kt` (`handleFailure`), sehingga sub-kondisi diabaikan dan `ConditionBuilder` **gagal tertutup (default ke `ALWAYS_TRUE`)**.
  - Dampaknya: **Semua potret karakter (Bob, Luna) dan semua ekspresi dievaluasi sebagai valid/true secara simultan**. Potret Bob otomatis dirender di layer yang sama tepat di belakang potret Luna.
* **Solusi**:
  - Bungkus kembali operand kedua dalam string literal quoted di `tools/compiler.py`:
    ```python
    "second": f"'{speaker_name}'"
    "second": f"'{em}'"
    ```
  - Serialisasi YAML menghasilkan format yang dipahami regex BetterHUD, sehingga hanya 1 potret sesuai `skript_1` (speaker) dan `skript_4` (emotion) yang aktif.

### B. Cinematic Fade Transparan Tanpa Bug Layout & Tofu
* **Penyebab Bug Sebelumnya**:
  - Memasukkan `bottom_cinematic_fade` (lebar 480px) ke dalam layout yang sama (`vn_dialog_layout`) merusak bounding box container BetterHUD, menggeser kotak dialog dan potret secara drastis serta berisiko memicu tofu jika tinggi glyph melebihi 170px.
* **Solusi Arsitektural**:
  - Pisahkan `bottom_cinematic_fade` ke dalam layout mandiri: `vn-fade-layout.yml` dengan `align: center`, `offset: center`, `layer: 1`.
  - Daftarkan `vn_fade_layout` dan `vn_dialog_layout` secara bersamaan dalam satu popup `vn_dialog` di `vn-dialog-popup.yml`:
    ```yaml
    vn_dialog:
      layouts:
        1:
          name: vn_fade_layout
          gui: {x: 50, y: 100}
          pixel: {x: 0, y: -45}
        2:
          name: vn_dialog_layout
          gui: {x: 50, y: 100}
          pixel: {x: -178, y: -78}
    ```
  - `vn_dialog_layout` tetap terisolasi tanpa pergeseran lebar kontainer, dan fade transparan hitam (alpha gradien 0->220) dirender mulus di latar belakang.


