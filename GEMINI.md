# Workspace Rules: Minecraft Story & Quest Script Development (Paper 26.2)

> **Directives: Lihat `.agent-directives.md` untuk aturan token-constrained, anti-loop (maksimal 2x fail), compact diff, zero-chitchat, dan integrasi vault.**

---

## 1. Environment & Tech Stack
- **Server Platform**: Paper 26.2 (Java 25)
- **Scripting Engine**: Skript v2.16.2
- **Addon Pendukung**:
  - **SkBee v3.25.4**: Display entities (text, item, block), interaction hitboxes, particles, sounds, vectors.
  - **FancyNpcs v2.12.1**: NPC spawning, skins, player-interaction triggers via commands/actions.
- **Root Skrip Produksi**: `server/plugins/Skript/scripts/`
- **Development Directory**: `plugins/story/`

---

## 2. Aturan Kritis Pemrograman Skript (Paper 26.2 & Minecraft 1.20.5+ / 1.21+)

### A. Identifikasi Item & Data Components
- **DILARANG** memakai `nbt compound of item` atau `tag "..." of nbt compound of item` karena sistem Data Components modern Minecraft memblokir NBT item lama.
- **WAJIB** menggunakan kombinasi **`name of item`** dan **`custom model data of item`** untuk memeriksa custom quest item atau story item.

### B. List Literal Inline Syntax
- **WAJIB** menyertakan kata hubung `'and'` atau `'or'` sebelum elemen terakhir dalam setiap list literal.
  - *Benar*: `set tab completions for position 1 to "start", "progress" and "reset"`
  - *Salah*: `set tab completions for position 1 to "start", "progress", "reset"` (Warning: *List is missing 'and' or 'or'*).

### C. Debounce Interaksi & Event Hand
- **DILARANG** menggunakan `event-hand` dalam `on click:` atau `on right click:`.
- **WAJIB** menerapkan cooldown tick (*debounce*) untuk mencegah eksekusi ganda (main-hand + off-hand):
  ```skript
  set {_waited} to difference between {story::cooldown::%uuid of player%} and now
  if {_waited} is less than 5 ticks:
      stop
  set {story::cooldown::%uuid of player%} to now
  ```

### D. Pencegahan Log Spam Console (Zero-Spam Policy)
- **DILARANG** mengeksekusi `execute console command` (seperti `effect`, `attribute`, `data merge`) di dalam loop/timer berulang (`every 1 second`, `every 2 ticks`).
- **WAJIB** mengeksekusi perintah eksternal hanya saat **state change/transisi** terjadi (misal: saat quest dimulai, bab selesai, cutscene aktif).
- Gunakan native Skript effects (`apply potion ...`, `teleport ...`, `play sound ...`) untuk animasi berkala.

### E. Tab Completion Syntax
- **DILARANG** menggunakan `position of player` di dalam `on tab complete`.
- **WAJIB** memakai `tab arg-1`, `tab arg-2`, atau `set tab completions for position X to ...`.

### F. Sintaks Experience Points (EXP)
- **DILARANG** menggunakan `give X of exp to player` karena kata "of exp" dianggap kuantitas entitas experience orb.
- **WAJIB** menggunakan `give X experience to player` atau `add X to player's experience`.

### G. Larangan Item Kustom sebagai Alias Tipe Vanilla
- **DILARANG** memperlakukan item custom sebagai tipe item vanilla (misal: `1 of cabbage` adalah invalid karena cabbage bukan item Minecraft).
- **WAJIB** memanggil fungsi factory resmi seperti `1 of getVDSCrop("cabbage")`.

### H. Sintaks Written Book Modern
- **DILARANG** menggunakan sintaks deprecated `book title of {_item}`.
- **WAJIB** menggunakan `title of {_item}`.

### I. Standar Domain Arena & Struktur Prosedural
- **Presisi Geometri Lingkaran**: Gunakan rumus Euclidean presisi `round(sqrt(({_dx} * {_dx}) + ({_dz} * {_dz}))) is R` untuk membentuk perimeter lingkaran yang mulus dan solid.
- **Prinsip Non-Destruktif Terrain**: Seluruh blok asli non-air di dalam rongga interior arena atau lantai yang diganti wajib disimpan dalam map persisten (`{story::domain::terrain_backup::*}`) dan dipulihkan kembali saat Domain dibersihkan/dihapus (`storyClearDomain`).
- **Pencahayaan Mandiri**: Arena tertutup wajib memiliki lantai datar dengan pencahayaan mandiri terintegrasi (seperti ornamen Sea Lantern berjarak teratur) untuk mencegah kegelapan total dan menjaga visibilitas pertarungan.
- **Kontrol Admin Lengkap**: Setiap sistem prosedural wajib menyediakan perintah pembangun dan pembersih eksplisit (`/storyadmin builddomain` dan `/storyadmin cleardomain`) serta toggle dinamis pada GUI.

### J. Standar Pemanggilan FancyNpcs 2.12.1 & Fallback Entitas
- **DILARANG** menggunakan flag koordinat manual yang tidak didukung (`--x`, `--y`, `--z`) via console command saat membuat NPC di posisi pemain.
- **WAJIB** mengeksekusi `execute player command "npc create <Name>"` (atau `make player execute "/npc create <Name>"`) agar FancyNpcs secara akurat merekam world, posisi, yaw, dan pitch orientasi pemain tanpa error argument flag.
- **Sintaks Action Resmi & Larangan Nested Quotes**:
  - **DILARANG** menggunakan tanda petik pembungkus `""` di dalam string argumen action FancyNpcs karena argumen `player_command` atau `console_command` bersifat *greedy string* dan akan menyimpan tanda kutip secara literal, memicu error `Unknown command /"command"`.
  - **WAJIB** menuliskan perintah secara langsung tanpa tanda kutip pembungkus:
  ```skript
  execute player command "npc action <Name> ANY_CLICK clear"
  execute player command "npc action <Name> ANY_CLICK add player_command story interact <nama_npc>"
  ```
  *(DILARANG menggunakan `npc action add <Name> ...` atau `add player_command ""..."""`)*.
- **Dukungan Dual-Spawning**: Sediakan opsi fallback entitas Villager No-AI fisik (`/storyadmin spawnnpc <npc> villager`) untuk kompatibilitas trigger klik kanan native Skript, dan **WAJIB** membatalkan event (`cancel event`) pada interaksi klik kanan entitas story agar window trading vanilla tidak terbuka.

### K. Standar Kekebalan Entitas (Entity Invulnerability)
- **DILARANG** menggunakan sintaks `set invulnerable of {_e} to true` karena tidak didukung oleh Skript.
- **WAJIB** menerapkan 3 lapis perlindungan untuk entitas NPC fisik:
  1. Eksekusi NBT Vanilla saat spawn: `execute console command "data merge entity %uuid of {_e}% {NoAI:1b,Invulnerable:1b,Silent:1b,PersistenceRequired:1b}"`
  2. Native Skript Potion: `apply resistance 5 to {_e} for 999 days`
  3. Native Damage Guard: `on damage of villager:` dengan `cancel event` jika nama entitas adalah NPC cerita.

### L. Standar Kompatibilitas Cross-Platform (Java & Bedrock / Geyser-Floodgate)
- **DILARANG** menggunakan tag clickable tellraw atau tooltip mentah (`<tooltip:...><command:...>`) di chat karena bocor sebagai teks kode dan tidak dapat diakses oleh pemain Bedrock Edition (ponsel/konsol).
- **WAJIB** menyediakan mekanisme **Dual-Interface (Chest GUI + Short Chat Input)** untuk setiap pilihan cerita, percabangan, atau voting:
  1. **Interactive Chest GUI**: Buka menu inventori dengan opsi visual jelas (misal: Balok Hijau Slot 11 untuk Pilihan 1, Balok Merah Slot 15 untuk Pilihan 2) yang ramah layar sentuh Bedrock.
  2. **Short Chat Input**: Tangkap input chat super singkat pada `on chat:` (seperti `1`, `2`, `ya`, `tidak`, `mercy`, `kill`) tanpa mewajibkan pemain mengetik perintah panjang.

### M. Standar Progresi Quest & Anti Auto-Complete
- **DILARANG** langsung memeriksa dan memotong inventori pemain untuk menyelesaikan quest di dalam trigger percakapan pertama saat quest baru diberikan.
- **WAJIB** memisahkan siklus hidup quest menjadi 3 tahapan jelas:
  1. **ACCEPT**: Pemain secara sadar menerima tugas (state berpindah ke `QUEST_..._ACTIVE`).
  2. **GATHERING**: Progres dicatat secara dinamis sejak misi diterima, bukan langsung otomatis selesai dengan stok lama.
  3. **EXPLICIT TURN-IN**: Penyerahan barang wajib melalui konfirmasi dialog eksplisit (misal: `[1] Serahkan Barang` / `[2] Belum Siap`) atau klik tombol GUI penyerahan, sehingga pemain selalu sadar kapan barang diserahkan dan quest dituntaskan.

### N. Standar Orientasi Kamera & Rigid Facing NPC (Yaw & Pitch Anti-Mendongak)
- **DILARANG** menggunakan `execute console command "teleport ... facing ..."` untuk menghadapkan pemain ke NPC karena Minecraft menghitung sudut pandang dari koordinat kaki (feet), yang menyebabkan kamera pemain otomatis mendongak tajam ke atas (ke langit) saat berdiri dekat dengan NPC.
- **DILARANG** menggunakan `slowness 10` dan `jump boost 250` pada dialog interaktif karena memicu distorsi FOV (*zoom aneh*) yang memusingkan layar pemain.
- **WAJIB** menggunakan native Skript/SkBee vector calculation dari posisi mata pemain (`1.6 blocks above location of player`) ke kepala NPC (`1.5 blocks above {_npcLoc}`).
- **WAJIB** mengunci `pitch` pada nilai `0` (lurus mendatar / eye-level) dan menyimpan orientasi ke anchor lokasi (`{story::dialogue::%{_uuid}%::anchor}`).
- **WAJIB** mengunci rotasi mouse dan langkah kaki pemain secara mutlak selama dialog aktif via `on player move:` dengan menteleportasikan pemain kembali ke anchor lokasi:
  ```skript
  on player move:
      if {story::dialogue::%uuid of player%::active} is true:
          teleport player to {story::dialogue::%uuid of player%::anchor}
          cancel event
  ```

### O. Standar Manajemen Proximity Trigger & Pencegahan Flag Macet
- **DILARANG** membiarkan flag eksplorasi (misal `{story::ch1::explored_well::%uuid%}`) berstatus permanen tanpa siklus reset saat stage cerita berpindah atau saat admin menguji skenario.
- **WAJIB** mereset flag eksplorasi dan entitas boss setiap kali tahapan terkait diaktifkan kembali (`storySetServerStage` / callback investigasi) serta menyediakan tombol reset eksplorasi khusus pada Admin GUI.
- **WAJIB** menggunakan radius deteksi yang memadai ($\ge 15$ blok) antara posisi pemain dan target lokasi (`{story::loc::*}`) agar pemain tidak perlu berdiri tepat di piksel koordinat yang kaku.

### P. Standar Custom Texture Font Overlay (Visual Novel HUD) & MalamSMP-PACK
- **Kompatibilitas Lintas Platform**: Tampilan Visual Novel HUD modern tidak boleh bergantung pada mod client-side (seperti FancyMenu) agar pemain Bedrock (via Geyser) tetap dapat menikmatinya.
- **Font Bitmap Provider**: Gunakan pemetaan karakter unicode privat (misal `\uE101` untuk kotak dialog, `\uE102` untuk nameplate, `\uE110` untuk potret Luna) di dalam `assets/minecraft/font/default.json` yang merujuk pada file tekstur di `assets/minecraft/textures/font/`.
- **Standar MalamSMP-PACK**: Paket resource pack resmi bernama **`MalamSMP-PACK`** (tersedia sebagai folder langsung dan `MalamSMP-PACK.zip`).
- **Ikon Resmi**: Wajib menggunakan ikon pixel art bulan (`pack.png` 128x128 pixel art).
- **Path Deployment Otomatis**: Setiap kali tekstur atau font dimodifikasi, **WAJIB** mengeksekusi script deployment ke:
  `C:\ATLauncher\instances\262\resourcepacks\MalamSMP-PACK`
  (via `plugins/story/resourcepack/deploy_malamsmp_pack.ps1`).

### Q. Larangan Default Parameter pada Definisi Fungsi Skript
- **DILARANG** menuliskan nilai default di dalam deklarasi parameter fungsi (seperti `sound: text = "minecraft:..."`, `pitch: number = 1.0`, atau `loc: location = null`). Skript tidak mendukung syntax assignment default parameter dan akan melempar error kompilasi (*Can't understand this function's parameters*).
- **WAJIB** mendeklarasikan parameter secara murni (`function myFunc(p: player, sound: text, pitch: number):`) dan mengatur nilai default di dalam tubuh fungsi menggunakan pattern fallback:
  ```skript
  if {_sound} is not set:
      set {_sound} to "minecraft:entity.villager.ambient"
  if {_sound} is "":
      set {_sound} to "minecraft:entity.villager.ambient"
  if {_pitch} is not set:
      set {_pitch} to 1.0
  if {_pitch} <= 0:
      set {_pitch} to 1.0
  ```
- **WAJIB** menyediakan fungsi helper/wrapper atau mengirimkan argumen lengkap saat memanggil fungsi agar jumlah parameter selalu cocok secara presisi tanpa error parameter count mismatch.

### R. Larangan Kondisi Majemuk Inline pada Pengecekan Variabel (`is set` / `is not set`)
- **DILARANG** menggabungkan `is not set` atau `is set` dengan operator pembanding lain menggunakan inline `or` atau `and` dalam satu baris ekspresi (seperti `if {_var} is not set or {_var} is "":` atau `if {_cb} is set and {_cb} is not "":`). Skript v2.16+ gagal mem-parse kondisi majemuk ini dan akan melempar error kompilasi: `Can't understand this condition`.
- **WAJIB** memisahkan pengecekan menjadi baris terpisah atau nested `if`:
  ```skript
  if {_sound} is not set:
      set {_sound} to "minecraft:entity.villager.ambient"
  if {_sound} is "":
      set {_sound} to "minecraft:entity.villager.ambient"
  ```
  atau
  ```skript
  if {_cb} is set:
      if {_cb} is not "":
          vnTriggerCallback({_p}, {_cb})
  ```

### S. Larangan Pemakaian Opsi Bertanda Kutip di Dalam String Literal (`"{@option}"`)
- **DILARANG** menyematkan opsi skript yang bernilai string bertanda kutip (misal `opt: "abc"`) ke dalam string literal yang juga bertanda kutip (seperti `set {_x} to "{@opt}text"`). Penggantian teks harfiah oleh preprocessor Skript akan menghasilkan tanda kutip ganda/tiga (`""abc"text"`) yang memicu error kompilasi: `Can't understand this expression: '"""...'`.
- **WAJIB** menggunakan salah satu dari dua pendekatan:
  1. Definisikan string di fungsi getter resmi (seperti `vnGetGlyph("id")`) lalu gabungkan variabel lokalnya:
     ```skript
     set {_shift} to vnGetGlyph("shift_right")
     set {_hudLine} to "%{_shift}%%{_box}%"
     ```
  2. Atau definisikan option tanpa tanda kutip pembungkus jika murni teks preprocessor: `opt: abc`.

---


## 3. Konvensi Data Story & Quest (UUID-Based Storage)

Semua progres cerita pemain harus tersimpan dalam variabel persisten berbasis UUID dengan struktur berjenjang:

```skript
# Format Variabel
{story::quest::%uuid of player%::current_chapter}  # integer (misal: 1, 2, 3)
{story::quest::%uuid of player%::stage}            # text ("TALK_ELDER", "GATHER_ORE", "BOSS_FIGHT")
{story::quest::%uuid of player%::status}           # "NOT_STARTED", "IN_PROGRESS", "COMPLETED"
{story::dialogue::%uuid of player%::active}        # boolean (true jika sedang membaca dialog)
{story::dialogue::%uuid of player%::anchor}        # location (koordinat terkunci menghadap NPC)
{story::choice::%uuid of player%::awaiting}        # text ("CHOICE_ID" atau unset)
```

> [!IMPORTANT]
> Selalu bersihkan temporary list dengan `clear {_temp::*}` di akhir fungsi/trigger untuk mencegah kebocoran memori (memory leak).

---

## 4. Standar Alur Dialog & Cutscene

1. **Typing / Sound Effect**: Setiap dialog yang muncul di chat atau subtitle harus disertai sound cue yang imersif (misal: `minecraft:entity.villager.ambient` atau `minecraft:block.note_block.harp` dengan pitch acak).
2. **Player Movement & Camera Lock (Freeze)**: Saat dialog penting berlangsung, kunci langkah kaki dan sudut pandang kamera pemain secara kaku (rigid facing) menggunakan anchor lokasi tanpa memberikan efek slowness/distorsi FOV.
3. **Pilihan Cerita Berantai (Interactive Choices & Dual-Interface)**:
   - Wajib menggunakan mekanisme Dual-Interface (Chest GUI interaktif dan Short Chat Input `1` / `2`).
   - Tampilkan teks chat yang bersih tanpa tag `<tooltip:...>`.
   - Jangan izinkan pemain mengeksekusi pilihan jika tidak sedang berada pada tahap cerita yang bersangkutan.

---

## 5. Struktur Format Skrip Story Standar

Setiap skrip story wajib mengikuti kerangka modular:
```skript
# ==============================================================================
#                       STORY SYSTEM - CHAPTER X
#              Target: Paper 26.2 | Skript 2.16+ | SkBee 3.25+
# ==============================================================================

options:
    prefix: &8[&6Kisah Aethir&8]&r
    perm_admin: aethir.story.admin
    no_perm: &cKamu tidak memiliki izin untuk mengelola alur cerita!

# [1] FUNCTIONS: Logika Dialog, Quest Progression, Reward
# [2] COMMANDS & TAB COMPLETIONS: /story, /quest
# [3] EVENTS & NPC HANDLERS: Interaksi NPC, Trigger Lokasi, Pilihan Percakapan
```

---

## 6. Integrasi Katalog Custom Items M-SMP (Cross-Module Standards)

Ketika alur cerita atau quest membutuhkan custom item (seperti bahan makanan, hasil kebun, kunci, atau mata uang), **DILARANG** mendefinisikan item baru secara duplikat jika item tersebut sudah ada di modul `plugins/skript/`.

### Referensi Fungsi Factory Resmi:
- **Mata Uang Ruby**:
  - Panggil `getMSMPRuby(amount)` atau `getVDSRuby(amount)`.
  - Hadiah quest Ruby: `give {_amount} of getMSMPRuby() to {_p}`.
- **Hasil Panen / Kebun (Farming)**:
  - Panggil `getVDSCrop(crop)` (contoh: `getVDSCrop("cabbage")` untuk Kubis Segar).
  - Panggil `getVDSSeed(crop)` untuk bibit kebun.
- **Masakan / Makanan Olahan (Meals)**:
  - Panggil `getVDSMeal(type)` (contoh: `getVDSMeal("fried_rice")` untuk Nasi Goreng Telur, `getVDSMeal("sandwich")` untuk Sandwich Segar, `getVDSMeal("burger")` untuk Burger).
- **Mineral, Kunci & Dokumen**:
  - Panggil `getVDSItem(id, amount)` (contoh: `getVDSItem("letter")`, `getVDSItem("wood_key1")`, `getVDSItem("silver_ingot")`).

### Standar Deduksi Item Aman (Anti-Duplikasi):
Saat mengambil item/mata uang dari tas pemain untuk menyelesaikan quest, gunakan pola loop bertahap yang aman dari bug *split-stack*:
```skript
set {_toRemove} to {_amount}
loop all items in {_p}'s inventory:
    if {_toRemove} <= 0:
        stop loop
    if name of loop-item is "{@target_name}":
        if custom model data of loop-item is {@target_cmd}:
            set {_amt} to item amount of loop-item
            if {_amt} <= {_toRemove}:
                remove {_amt} from {_toRemove}
                remove loop-item from {_p}'s inventory
            else:
                set item amount of loop-item to ({_amt} - {_toRemove})
                set {_toRemove} to 0
```

