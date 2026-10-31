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

---

## 8. Laporan Investigasi Visual In-Game (Screenshot 1, 2, 3)

### A. Temuan Masalah & Ketidaksesuaian Visual
1. **Kotak Dialog Terlempar Jauh ke Kanan Bawah**:
   - Kotak dialog (`dialogue_box.png`) merender di pojok kanan bawah layar pemain, menabrak tangan/item pemain, alih-alih berada tepat di tengah bawah layar.
   - **Akar Masalah**:
     Di `data/hud_config.yml`, `dialog_box` memiliki offset `x: 50`. Ditambah dengan `popup_pixel_x = -126`, kotak bergeser ke kanan. Selain itu, layout BetterHUD menggunakan `align: left` dan `offset: left`, di mana `LayoutComponentContainer` menghitung:
     $$\text{container\_offset} = 0$$
     Sedangkan seluruh kalkulasi koordinat di `hud_config.yml` berasumsi titik tengah layar dengan `dialog_box` bergeser relatif terhadap anchor.
2. **Potret Karakter Terlempar Jauh ke Kiri Bawah**:
   - Potret Luna (`portrait_luna_*`) merender terpisah di pojok kiri bawah layar dekat tepi kiri GUI, terputus jauh dari kotak dialog.
   - **Akar Masalah**:
     Di `hud_config.yml`, potret memiliki `x: -39`, namun karena container di-offset ke kiri pada anchor popup `x: -126`, potret merender di posisi layar $-126 - 39 = -165$ (terlalu jauh ke kiri dari dialog box yang berada di $-126 + 50 = -76$). Potret dan kotak tidak berada dalam satu kesatuan bounding box yang pas.
3. **Teks Dialog & Nameplate Tidak Muncul**:
   - Di ketiga screenshot, area teks di dalam kotak dialog kosong (tidak ada nama pembicara maupun isi dialog).
   - **Akar Masalah**:
     Teks memiliki `split-width: 202` dan `line: 4`. Karena font atau layer z-index (`layer: 5` dan `6`), atau evaluasi placeholder Skript string kosong, teks tersembunyi atau terlempar di luar viewport/tertutup background dialog.
4. **Cinematic Fade**:
   - Fade hitam bawah sudah aktif tanpa tofu BossBar, namun perataan horizontal dialog box dan portrait belum menyatu dengan proporsi fade.

### B. Solusi yang Diperlukan di Linux/Compiler
1. Konfigurasi `data/hud_config.yml` atau formula compiler untuk container `vn_dialog_layout`:
   - Gunakan `offset: center` atau kunci basis kalkulasi relatif terhadap pusat kotak dialog (`dialog_box` berpusat di $X=0$).
   - Hubungkan portrait relatif ke sisi kiri kotak dialog: $X_{\text{portrait}} = X_{\text{box}} - \text{margin}$.
2. Verifikasi font provider `dialog_font` dan mapping variabel `skript_1` (speaker) serta `skript_2` (pesan) agar teks langsung terlihat di layer atas kotak.

---

## 9. Laporan Hasil Uji Pemisahan & Anomali In-Game (`bc7242f` & `3a4f56e`)

### A. Ringkasan Pengujian di Server Windows & Client 26.2
- **Commit yang Diuji**: `bc7242f` (perubahan `layout_offset: center` dan `pixel.x: 0`) dan `3a4f56e` (uji isolasi `speaker_text`, disable `dialog_text`).
- **Langkah Eksekusi**:
  1. `git pull` -> ditarik commit `bc7242f`.
  2. `python tools/compiler.py` dijalankan di server Windows.
  3. Reload Skript & BetterHud via `/vn reloadhud`.
  4. Reload resource pack di client Minecraft (F3+T).
  5. Pengujian dialog via `/vn testdialog` pada player `Bramanzero`.

### B. Temuan Masalah Baru di In-Game
1. **Kotak Dialog Terlempar ke Sudut Paling Kiri Bawah**:
   - Kotak dialog (`dialogue_box.png`) kini berpindah dari yang sebelumnya di pojok kanan bawah menjadi **terjepit di sudut paling kiri bawah layar** (`X ≈ 0, Y ≈ bottom`), dengan sisi kiri kotak terpotong oleh tepi layar.
   - Potret karakter dan nameplate tidak terlihat sama sekali (terlempar keluar batas kiri layar / off-screen karena koordinat negatif relatif terhadap origin kiri).
   - **Penyebab**: Perubahan `layout_offset: center` dengan `pixel.x: 0` pada container dengan `align: left` di Minecraft 26.2 menyebabkan titik acuan kontainer jatuh tepat di tepi kiri GUI (`0.5 * ui.x` shader offset tidak mengompensasi perataan kontainer saat `align: left`).

2. **Karakter Tofu Tetap Muncul Meski `dialog_text` Dimatikan (`enabled: false`)**:
   - Pada commit `3a4f56e`, `dialog_text` dinonaktifkan (`enabled: false`), `line: 1`, dan `split_width` dihilangkan sepenuhnya dari `vn-dialog-layout.yml`. Hanya `speaker_text` (`[custom_variable:skript_1]`) yang aktif di dalam layout.
   - **Hasil**: Karakter tofu tetap muncul di pojok kiri bawah kotak dialog berupa dua simbol pengganti (`[≡] [▶]`).
   - **Analisis**:
     - Tofu **bukan** disebabkan oleh multiline text splitting (`split-width` / `line-width`), karena `dialog_text` sudah di-strip total dari file layout.
     - Karakter tofu tersebut berasal dari:
       1. Glyphs `speaker_text` (`Luna`) pada font `betterhud:popup_vn_dialog_text_2_1_1` yang gagal dipetakan oleh client (client log mencatat `[WARN]: Resource pack file/BetterHud_Pack.zip is not compatible with font atlas resizing. Temporarily disabling font atlas resizing`).
       2. Atau karakter PUA (`\U000ce00*`) dari image provider (`portrait` / `nameplate`) yang gagal melewati kondisi Skript (`skript_1 == 'Bob'`, dll.) sehingga BossBar tetap mengirimkan spasi/karakter fallback yang tidak ter-offset oleh shader.

### C. Panduan Fix untuk Lingkungan Linux
1. **Perbaikan Koordinat / Centering**:
   - Kembalikan anchoring popup layout agar kotak dialog berada di tengah layar secara visual. Bila menggunakan `offset: center`, periksa lebar kontainer `LayoutComponentContainer` agar tidak menarik layout ke sudut kiri `0`.
2. **Debug Font vs Image PUA**:
   - Lakukan tes layout tanpa elemen `texts` sama sekali (`texts: {}`) untuk memastikan apakah kedua tofu tersebut berasal dari teks atau dari karakter bitmap image yang gagal evaluasi kondisi.
   - Periksa kompatibilitas shader `text.vsh` / `rendertype_text.vsh` terhadap format atlas font di Minecraft 26.2 (terkait warning atlas resizing).




