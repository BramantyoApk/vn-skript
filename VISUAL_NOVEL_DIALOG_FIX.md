# Visual Novel Dialogue, Studio Sync, Custom HUD & Font Rendering Reference

Dokumentasi lengkap deep analysis perbaikan bug pergeseran teks, standarisasi koordinat tetap (`align: left, offset: center`), font primer drop-shadow 2-layer, sinkronisasi compiler, dan penambahan fitur Custom HUD di Story Studio.

---

## 0. Lokasi Client Instance, Server & Kontrol Konsol
- **Server Root Directory**: `C:\Users\Edia\Documents\Project-mc\server`
- **Server Startup Script**: `C:\Users\Edia\Documents\Project-mc\server\start.bat`
- **Server Live Console Port (RCON)**: `127.0.0.1:25575` (Password: `storydev`, tools: `tools/send_rcon.py`)
- **Client Minecraft Instance (ATLauncher)**: `C:\ATLauncher\instances\262`
- **Cache Server Resource Pack Client**: `C:\ATLauncher\instances\262\downloads\` (Folder ini menyimpan file zip hash pack dari server)
- **Local Resource Packs Client**: `C:\ATLauncher\instances\262\resourcepacks\`
- **Server BetterHUD Assets**: `C:\Users\Edia\Documents\Project-mc\server\plugins\BetterHud\`
- **Server RSPM Output**: `C:\Users\Edia\Documents\Project-mc\server\plugins\ResourcePackManager\output\ResourcePackManager_RSP.zip`
- **Server Resource Pack URL**: `http://127.0.0.1:25566/rspm.zip`

### Cara Eksekusi Perintah Konsol Server:
```bash
python tools/send_rcon.py "<perintah>"
# Contoh:
# python tools/send_rcon.py "list"
# python tools/send_rcon.py "sk reload story/story_core"
```

---

## 1. Deep Analisis & Akar Masalah: Kenapa Teks Masih Berpindah?

### A. Akar Masalah di Bytecode BetterHUD (`LayoutComponentContainer.class`)
Pada file `vn-dialog-layout.yml` sebelumnya digunakan:
```yaml
vn_dialog_layout:
  align: center   # <--- BIANG KEROK UTAMA
  offset: center
```
Di dalam bytecode `LayoutComponentContainer`:
```java
switch (align) {
    case LEFT:
        offset = 0;
        break;
    case CENTER:
        offset = (max_layout_width - element_width) / 2;
        break;
    case RIGHT:
        offset = max_layout_width - element_width;
        break;
}
```
1. `max_layout_width` dihitung dari elemen gambar terlebar (yaitu `dialog_box` = 255px).
2. Ketika layout diatur ke `align: center`, BetterHUD menghitung perataan dinamis:
   $$\text{offset} = \frac{255 - \text{element\_width}}{2}$$
3. Untuk gambar, lebarnya konstan. **TETAPI UNTUK TEKS DINAMIS** (`custom_variable:skript_2`):
   - `element_width` dihitung dari **panjang string kalimat yang sedang ditampilkan**.
   - **Kalimat Pendek** ("Halo! Mau membuka..."): `element_width` kecil (misal 90px) $\rightarrow \text{offset} = (255 - 90)/2 = +82\text{px}$ (teks bergeser ke kanan).
   - **Kalimat Panjang** ("Tolong bawakan aku 5 Fresh Cabbage..."): `element_width` besar (misal 180px) $\rightarrow \text{offset} = (255 - 180)/2 = +37\text{px}$ (teks terlempar ke kiri sejauh 45px menimpa kepala karakter Luna).

### B. Solusi Pasti: Mengubah ke `align: left, offset: center`
Dengan mengubah root layout ke:
```yaml
vn_dialog_layout:
  align: left
  offset: center
```
1. Karena `align: left`, nilai `offset` formula dinamis menjadi `0` secara mutlak (`iload_2 = 0`).
2. Teks dialog dan nama speaker **TIDAK AKAN PERNAH BERGESER 1 PIKSEL PUN**, berapa pun panjang pendeknya kalimat.
3. Karena `offset: center`, seluruh kesatuan kotak dialog tetap terpusat di tengah layar Minecraft.
4. Semua koordinat horizontal elemen dihitung relatif terhadap sisi kiri `dialog_box` (`x: 0`).

---

## 2. Standarisasi Koordinat Baru (Satu Lokasi Tetap)

Semua koordinat elemen dialog telah disatukan dan dikunci di `data/hud_config.yml` dan `vn-dialog-layout.yml`:

| Elemen | Local X | Local Y | Scale | Layer | Align | Deskripsi Visual |
|---|---|---|---|---|---|---|
| `bottom_cinematic_fade` | `-139` | `-65` | `1.29` | 1 | left | Layar fade gelap bawah layar (di `vn-fade-layout.yml`) |
| `dialog_box` | `50` | `-3` | `1.0` | 2 | left | Kotak dialog utama di tengah layar |
| `portrait` | `-39` | `-57` | `0.78` | 3 | left | Potret NPC Luna / Bob di sisi kiri box |
| `nameplate` | `-21` | `35` | `1.0` | 4 | left | Pita banner nama NPC |
| `speaker_text` (Shadow) | `-12` | `42` | `0.52` | 4 | left | Drop shadow nama NPC `<#111111>` |
| `speaker_text` (Main) | `-13` | `41` | `0.52` | 5 | left | Teks nama NPC `<#FFFFFF>` di dalam banner |
| `dialog_text` (Shadow) | `55` | `3` | `0.46` | 4 | left | Drop shadow isi dialog `<#111111>` |
| `dialog_text` (Main) | `54` | `2` | `0.46` | 5 | left | Teks isi dialog `<#F0F0F0>` di dalam kotak biru |

---

## 3. Fitur Custom HUD Dialog di Story Studio

Story Studio (`tools/story_studio.py`) telah diperluas dengan fitur Custom HUD lengkap:

1. **Tombol "+ Buat Custom HUD Dialog"**:
   - Menambahkan elemen HUD baru kapan saja langsung dari UI Story Studio.
   - Pilihan tipe: **Image (Gambar PNG)** atau **Text (Pola Teks BetterHUD)**.
   - Pilihan file gambar otomatis menyalin file ke folder aset tekstur.
   - Mengatur layer (1-10), skala, dan posisi awal.
2. **Kontrol Visual Lengkap**:
   - **Dipindahkan**: Klik & drag langsung di visual canvas atau atur via spinbox X & Y / tombol panah keyboard.
   - **Dibesarkan / Dikecilkan**: Slider skala (0.1x hingga 3.0x) atau spinbox skala.
   - **Dihapus**: Pilih elemen dari dropdown lalu klik tombol "Hapus".
   - **Ganti Texture Pack**: Dropdown tekstur `dialogue_box` & `nameplate` dengan tombol **"+ Import Tekstur Baru"** untuk memasang texture pack kustom.
3. **Editor Alur Dialog (Tab Penulis Dialog)**:
   - Tambah baris dialog baru, edit kalimat, ganti emosi potret.
   - Hapus baris dialog, duplikasi baris, naik/turunkan urutan percakapan.
   - Tombol "Lihat di HUD" untuk menguji langsung di canvas pratinjau.
4. **1-Click Sync**:
   - Otomatis mengompilasi seluruh elemen (termasuk custom HUD) ke `vn-dialog-layout.yml`, `dialog-images.yml`, dan Skript router.

---

## 4. Prosedur Reload In-Game

Setelah mengubah konfigurasi di Story Studio atau compiler:
1. Di server Minecraft, jalankan:
   ```text
   /vn reload
   ```
2. Di client Minecraft, tekan tombol:
   ```text
   F3 + T
   ```
3. Ajak bicara NPC Luna:
   - Teks dialog dan nama pembicara selalu diam di satu posisi tetap.
   - Font bersih, tajam, dengan shadow natural persis seperti HUD atas "Update Baru!".

---

## 5. Deep Analisis & Solusi Bug Studio: Import Tekstur & Custom HUD Tidak Muncul / Koordinat 0,0

### A. Gejala Bug yang Ditemukan
1. **Custom HUD Baru Tidak Muncul**: Ketika pengguna membuat custom HUD dialog baru (tombol `+ Buat Custom HUD Dialog`), elemen tidak muncul di canvas Story Studio dan tidak bisa diklik / digeser.
2. **Lokasi Terkunci / Stuck di 0,0 & Skala Tidak Berubah**: Saat mencoba memperbesar/memperkecil skala atau mengubah X, Y di spinbox/slider, elemen tetap berada di (0, 0) dan kembali ke default saat compiler berjalan.
3. **Import Tekstur Tidak Berubah di Canvas**: Setelah mengimpor file PNG melalui `+ Import Tekstur Baru`, tekstur tidak langsung diterapkan ke `dialog_box` atau `nameplate`, dan canvas tetap menampilkan tekstur lama.

---

### B. Akar Masalah Mendalam (Root Cause Analysis)

#### 1. Canvas Renderer `_redraw_hud_canvas` Melewatkan Elemen Kustom
- Di dalam method `_redraw_hud_canvas(self)` di `tools/story_studio.py`, perulangan rendering elemen hanya memeriksa 6 kunci hardcoded:
  ```python
  if key == "portrait": ...
  elif key == "dialog_box": ...
  elif key == "nameplate": ...
  elif key == "speaker_text": ...
  elif key == "dialog_text": ...
  elif key == "counter_text": ...
  ```
- Tidak ada blok `else:`! Akibatnya, setiap elemen di luar 6 kunci tersebut (seperti custom HUD element yang baru dibuat) **dilewati begitu saja** tanpa digambar.
- Karena tidak digambar, elemen tersebut juga tidak didaftarkan ke `self._hud_canvas_items[key]`, sehingga event klik mouse canvas (`_on_hud_canvas_click`) tidak pernah mendeteksi bounding box elemen kustom tersebut (tidak bisa dipilih atau digeser).

#### 2. Ketiadaan Sinkronisasi Antara `elements` dan `custom_elements` serta `save_hud_config()`
- Ketika koordinat atau skala diubah via spinbox atau slider:
  `_on_hud_val_change` hanya mengubah `self.hud_cfg["elements"][cur]`, tetapi **TIDAK mengubah** `self.hud_cfg["custom_elements"][cur]`.
- Yang lebih parah: `save_hud_config(self.hud_cfg)` **tidak pernah dipanggil** di dalam `_on_hud_val_change` maupun di `_on_hud_canvas_release`.
- Akibatnya, perubahan nilai X, Y, dan scale hanya tersimpan sementara di memori RAM objek `elements`. Pada file konfigurasi `data/hud_config.yml`, objek `custom_elements` tetap menyimpan nilai awal (0, 0).
- Ketika compiler `tools/compiler.py` dijalankan, ia membaca `custom_elements` dari disk yang masih bernilai `0, 0`.

#### 3. Caching Tekstur RAM Tidak Di-reset dan Tidak Ada Dialog Auto-Assign Tekstur
- `tools/story_studio.py` menggunakan cache memori `self._texture_ram_cache = {}` untuk menyimpan objek PhotoImage yang sudah di-resize.
- Pada fungsi `_on_import_custom_texture`, file PNG hanya disalin ke direktori `font`, lalu menampilkan alert dialog "Silakan pilih dari dropdown".
- Fungsi tersebut **tidak pernah membersihkan** `self._texture_ram_cache` dan `self._hud_image_refs`. Akibatnya, canvas tetap merender gambar lama yang tersangkut di cache RAM.
- Pengguna juga tidak diberi opsi untuk langsung menerapkan tekstur baru tersebut ke `dialog_box`, `nameplate`, atau sebagai Custom HUD baru.

---

### C. Solusi dan Koreksi Kode yang Telah Diterapkan

#### 1. Menambahkan Blok Rendering Custom HUD di `_redraw_hud_canvas`
Menambahkan penanganan `else:` lengkap di `_redraw_hud_canvas`:
- Untuk elemen tipe `image`: Membaca file gambar PNG (resolusi otomatis via PIL), merender ke canvas dengan ukuran terskala, menampilkan outline kuning saat dipilih, dan mendaftarkan bounding box ke `self._hud_canvas_items[key] = (cx, cy, rw, rh)`. Jika gambar belum ada, digambar kotak placeholder styling modern.
- Untuk elemen tipe `text`: Merender teks pattern dengan font Minecraft terskala dan mendaftarkan bounding box.
- Sekarang custom HUD element langsung terlihat, bisa diklik, diseleksi, dan digeser di canvas.

#### 2. Sinkronisasi Penuh Dua Arah & Auto-Save Disk
- Di `_on_hud_val_change`:
  ```python
  if "custom_elements" in self.hud_cfg and cur in self.hud_cfg["custom_elements"]:
      c_elem = self.hud_cfg["custom_elements"][cur]
      c_elem["x"] = x
      c_elem["y"] = y
      c_elem["scale"] = round(scale, 2)
      if "layer" in target:
          c_elem["layer"] = target["layer"]
  save_hud_config(self.hud_cfg)  # <--- Persist langsung ke disk!
  ```
- Di `_on_hud_canvas_release`:
  Saat selesai drag mouse, seluruh koordinat elemen kustom disinkronkan ke `custom_elements`, disimpan dengan `save_hud_config()`, dan otomatis dikompilasi ulang dengan `compile_portraits_and_betterhud()`.
- Di `_update_hud_editor_fields` & `_refresh_hud_elements_combo`:
  Menjamin seluruh entri di `custom_elements` selalu memiliki mirroring data di `elements`, mencegah nilai ter-reset ke 0, 0.
- Di `scale_slider`:
  Batas skala diperluas hingga `3.0x` (range `0.1 - 3.0`), dan event `<ButtonRelease-1>` di-bind ke `_on_scale_slider_release` untuk langsung menyimpan perubahan skala ke disk.

#### 3. Smart Import Tekstur dengan Modal Auto-Assign & Cache Flush
Method `_on_import_custom_texture` diperbarui secara total:
- Membersihkan cache RAM `self._texture_ram_cache.clear()` dan `self._hud_image_refs.clear()` secara instan saat import.
- Membuka jendela dialog interaktif dengan 4 pilihan 1-klik:
  1. **🖼️ Terapkan ke Kotak Dialog (`dialog_box`)**: Langsung mengganti tekstur background dialog box, menyimpan config, auto-compile, dan me-refresh canvas.
  2. **🏷️ Terapkan ke Pelat Nama (`nameplate`)**: Langsung mengganti tekstur pita nama speaker.
  3. **✨ Jadikan Elemen Custom HUD Baru**: Otomatis membuka Custom HUD Builder dengan field file dan ID yang sudah terisi nama tekstur tersebut.
  4. **💾 Hanya Simpan (Pilih Manual)**: Menyimpan ke direktori aset font untuk dipilih manual nanti.
- Pada `_on_hud_texture_selected` (saat user ganti tekstur dari dropdown), cache RAM juga otomatis di-clear dan layout langsung di-recompile.

---

## 4. Deep Analisis Masalah `bottom_cinematic_fade` & Teks Hilang di Minecraft

### A. Gejala yang Ditemukan
Setelah user menambahkan elemen Custom HUD `bottom_cinematic_fade` (gambar cinematic hitam transparan berukuran 480x140 px, scale 1.29 = 619x180 px):
1. **Di Minecraft**: Teks dialog (`speaker_text` dan `dialog_text`) **hilang total** tidak muncul sama sekali.
2. **Posisi Berantakan**: Tampilan visual di Minecraft bergeser sangat jauh dibanding posisi di Story Studio.

### B. Akar Masalah Teknis

#### 1. Bug Shader Clipping `layer: 0` & Depth Fighting Teks vs Gambar
- Pada file konfigurasi `data/hud_config.yml`:
  `speaker_text` dan `dialog_text` memiliki nilai konfigurasi `layer: 1`.
- Logika compiler sebelumnya menghasilkan layer teks shadow:
  `layer: spk_layer - 1` = `1 - 1 = 0`.
- Di dalam kode bytecode BetterHUD `ShaderManagerImpl.class`:
  ```java
  345: invokevirtual kr/toxicity/hud/shader/HudShader.getLayer:()I
  348: ifeq          367
  351: // tulis 'layer = ...;' ke dalam GLSL shader
  367: // SKIP!
  ```
  Jika `layer == 0`, instruksi GLSL pengatur `layer` dilewati! Default nilai variabel `layer` di GLSL shader adalah `500.0`. Nilai depth z `500.0` berada di luar viewport render Minecraft (ke-cull atau terlempar ke luar layar).
- Sedangkan layer teks foreground bernilai `layer: 1`, depth z-nya sama persis dengan `dialog_box`, `nameplate`, dan `bottom_cinematic_fade` (semua `layer: 1`). Akibat z-buffer depth-fighting pada layer yang sama, poligon font tertutup oleh quad background.

#### 2. Kontainer Layout Bounding Box Shift (`LayoutComponentContainer.class`)
- Di BetterHUD bytecode `PopupElement.class` baris 445-505 dan `LayoutComponentContainer.class`:
  BetterHUD menghitung `max = max(ir.max() for ir in images)`.
  Dengan setting `offset: center`, titik awal render kontainer digeser sejauh `-max / 2`.
- Sebelumnya, elemen gambar terlebar adalah `dialog_box` (lebar 255px), sehingga offset kontainer adalah `-255 / 2 = -127px`.
- Ketika `bottom_cinematic_fade` (lebar 480px * 1.29 = 619px) digabungkan ke dalam layout yang sama (`vn_dialog_layout`), BetterHUD menghitung `max = 619px`.
- Akibatnya, seluruh kontainer digeser sejauh `-619 / 2 = -309px` (bergeser sejauh **182 piksel ke kiri**!). Seluruh kotak dialog, portrait, dan nama ikut terlempar ke kiri, berbeda total dari Story Studio yang merender kanvas dengan pivot origin tetap.

### C. Solusi dan Koreksi yang Diterapkan

1. **Pemisahan Layout Background (`vn_fade_layout`)**:
   - `bottom_cinematic_fade` dipisahkan secara otomatis oleh compiler ke sub-layout tersendiri: `vn_fade_layout`.
   - `vn_dialog_layout` mempertahankan `max` murni dari kotak dialog (255px), sehingga posisi elemen dialog di Minecraft 100% konsisten dengan Story Studio tanpa mengubah koordinat `elements`.
   - File popup `vn-dialog-popup.yml` mendaftarkan kedua layout:
     ```yaml
     vn_dialog:
       duration: 999999
       key-mapping: false
       triggers:
         1:
           class: custom
           name: vn_dialog
       layouts:
         1:
           name: vn_fade_layout
           gui: {x: 50, y: 100}
           pixel: {x: 0, y: -78}
         2:
           name: vn_dialog_layout
           gui: {x: 50, y: 100}
           pixel: {x: 0, y: -78}
     ```

2. **Garansi Layer Teks (Anti-Cull & Anti-Occlusion)**:
   - Compiler memvalidasi layer teks:
     - Text Shadow selalu minimum `layer: 3` (tidak pernah bernilai 0, mencegah bug `ifeq 367` shader clipping).
     - Text Foreground selalu minimum `layer: 4` (selalu berada di depan gambar layer 1-3).
   - Teks dijamin muncul jelas dengan outline/drop-shadow tajam di atas semua background.

---

## 5. Standarisasi Shader ID, Single Layout & Sinkronisasi Client 26.2

### A. Eliminasi Duplikasi Config Stale (Penyebab Utama Divergensi Shader ID)
Sebelumnya terdapat config sisa pengujian terdahulu di direktori BetterHUD server:
- `popups/dialog-popup.yml` (`dialog_vn`)
- `layouts/dialog-layout.yml`
- `layouts/dialog-backdrop-layout.yml`

Config lama ini menyebabkan BetterHUD mendaftarkan font switch case terpisah dan memecah alokasi ID shader GLSL:
- `dialogue_box` terdaftar di `id=7`
- `nameplate` terdaftar di `id=10`
- `text_1` & `text_3` (shadow) terlempar ke `id=10`
- `text_2` & `text_4` (foreground) terlempar ke `id=11`
Akibatnya layer depth dan offset vertikal di `text.vsh` tidak cocok, menyebabkan teks tidak muncul di atas kotak dialog.

**Solusi:**
File stale dihapus secara permanen. BetterHUD di-recompile bersih sehingga hanya menghasilkan satu hierarki popup `vn_dialog`:
- `id=6`: `bottom_cinematic_fade` (layer 1)
- `id=7`: `dialogue_box` (layer 2)
- `id=8`: `portrait` (layer 3)
- `id=9`: `nameplate` & text shadow (layer 4)
- `id=10`: text foreground (layer 5)

### B. Sinkronisasi Otomatis Client Pack (`BetterHud_Pack.zip`)
- Compiler langsung mengekspor build zip terkompilasi ke file `C:\ATLauncher\instances\262\resourcepacks\BetterHud_Pack.zip`.
- Shader MC 26.2 (`betterhud_26_2/assets/minecraft/shaders/core/text.*`) otomatis disalin ke root `assets/minecraft/shaders/core/` untuk kompatibilitas penuh engine rendering client.
- Injeksi shader root juga diterapkan otomatis ke `ResourcePackManager/mixer/BetterHUD_resource_pack.zip`, `ResourcePackManager/output/ResourcePackManager_RSP.zip`, dan direktori cache client `instances/262/downloads/`.
- Folder unzipped `BetterHud_Pack` otomatis dibersihkan agar tidak menimpa file zip.

### C. Shader Program GPU Cache & Reload Client
- Minecraft Fabric (dengan ModernFix, Sodium, Iris) mengompilasi core shaders GLSL (`text.vsh`) ke GPU program saat startup atau saat event reload resource pack lengkap.
- Server dynamic pack prompt tidak selalu memicu re-kompilasi shader core GLSL pada GPU memory, sehingga client tetap menjalankan shader lama dengan switch ID lama (menyebabkan fallback `xGui = 0` dan elemen bergeser ke tepi kiri layar).
- **Prosedur Refresh Client:** Tekan `F3 + T` di in-game client untuk memuat ulang seluruh resource pack dan memaksa re-kompilasi OpenGL shader programs, atau restart client bila ModernFix menahan file lock pada shader cache.



