# DOKUMEN DESAIN NARASI & ALUR CERITA (STORY BIBLE)
**Proyek**: Minecraft SMP Story & Quest Engine  
**Platform**: Paper 26.2 | Skript 2.16.2 | SkBee 3.25.4 | FancyNpcs  
**Penulis Ide**: Ediot [FIG]  

---

## 1. Premis Utama & "The Big Twist" (Pondasi Cerita)
Dunia petualangan Minecraft yang dijalani para pemain bukanlah dunia fantasi biasa, melainkan **simulasi realitas virtual (Digital Sanatorium / Memory Stasis)** yang dibangun oleh seorang ayah bernama **Bramanzero** untuk putrinya, **Ayarin Kusuma (Aya / Kimoyara)**.

### Latar Belakang Dibalik Layar:
- **Kiamat Virus**: Saat Aya berusia 8 tahun, wabah virus mematikan melanda bumi. 
- **Mesin Incubator**: Bramanzero memasukkan Aya ke dalam pod inkubator stasis agar tubuhnya selamat dari virus, dengan sistem realitas buatan yang menemani alam bawah sadarnya.
- **Kerusakan Mental & Distorsi Dunia**: Menunggu bertahun-tahun di dalam isolasi membuat mental Aya kritis. Dunia simulasi mulai membusuk, menghasilkan distorsi, monster buas, dan glitch programming bahasa C (`./a/.../am.c line 204`).
- **Kimoyara**: Manifestasi rasa sakit, trauma, dan kemarahan Aya yang memproyeksikan dirinya sebagai penguasa akhir dunia simulasi.
- **Bramanzero sebagai Sistem**: Bramanzero menyusupkan dirinya ke dalam kode inti sistem sebagai "bug pelindung" untuk menenangkan putrinya di saat-saat terakhir.

---

## 2. Rincian Alur per Chapter

### Chapter 1: Pertemuan, Teror Sumur Tua & Penjaga Hantu
* **Karakter Baru**: **Luna** (NPC petualang dengan heart system / friendship bar).
* **Alur Quest Utama**:
  1. **Quest 1 (Perbekalan Gandum)**: Kumpulkan 10 Gandum untuk Luna (Reward: 5 Ruby + 100 EXP + 1 Hati).
  2. **Quest 2 (Kebun Apel)**: Petik 5 Apel Merah dari kebun desa (Reward: 5 Ruby + 150 EXP + 1 Hati).
  3. **Quest 3 (Misteri Sumur Tua)**: Selidiki Sumur Tua di perbatasan desa (`ch1_village`).
     * Di lokasi sumur, pemain menemukan **jejak kaki misterius** yang mengarah masuk ke dalam **Goa Bawah Tanah**.
     * Pemain tidak melapor ke Luna dulu, melainkan langsung menelusuri jejak masuk ke kedalaman goa.
* **Klimaks Chapter 1: Goa Bawah Tanah & Boss Battle**:
  * Tiba di sarang goa (`ch1_boss`), atmosfer meredup pekat (*Darkness Fade*).
  * **Pre-Boss Monologue**: Penjaga Hantu menyampaikan monolog 3 babak dari kegelapan.
  * **Domain Expansion (Domain Arena)**:
    * Mengurung area silinder melingkar presisi (**Radius 32 blok**, **Tinggi 100 blok**) menggunakan Crying Obsidian & Deepslate Tiles.
    * Lantai arena dibuat datar penuh dengan perpaduan Deepslate Tiles dan **Sea Lantern** berpola simetris untuk pencahayaan mandiri.
    * Seluruh blok rintangan di dalam arena dikosongkan dan disimpan ke dalam cache rollback.
    * Titik respawn / spawnpoint seluruh pemain diatur otomatis di dalam arena (`Y = lantai + 1`).
    * Dinding Domain tidak dapat dihancurkan pemain (`unbreakable`), namun pemain bebas menaruh blok pertahanan taktis.
  * **Boss Battle: Penjaga Hantu (Ghost Guardian)**:
    * Blind HP (500 HP tanpa BossBar).
    * Serangan berkala: Hembusan Es (Freeze Slowness AoE 12 blok) & Shadow Teleport di belakang pemain.
  * **Pilihan Moral & Chat Voting (Zero Spoiler)**:
    * Saat boss mencapai 1 HP, boss berlutut/stun dan pemain diinstruksikan mengetik **`mercy`** atau **`kill`** langsung di chat dalam 25 detik tanpa membocorkan hadiah.
    * **MERCY**: Mendapatkan *Buku Katulise* (Kisah anak yang diselamatkan ayahnya dari akhir dunia lewat portal dimensi).
    * **KILL**: Mendapatkan *Ice Book* (Senjata sihir es: Klik Kanan = Ice Throw 3x3; Shift + Klik Kanan = Frost Nova AoE 10x10).
    * Domain arena runtuh total dan seluruh medan dunia dipulihkan 100%.
* **Penyelesaian Chapter 1 & Laporan ke Luna**:
  * Pemain kembali ke desa dan melaporkan temuan teror Goa Bawah Tanah kepada Luna.
  * Luna lega dan bersyukur -> **Chapter 1 Resmi SELESAI (`CH1_COMPLETED`)**.
  * Luna membuka **Papan Daily Quest Luna** (3 misi acak: Easy, Normal, Hard, reset otomatis 23:59 WIB).
* **Side Mission Pasca-Bab 1 (Secret Memory Trigger: Kubis Segar)**:
  * Kapan saja setelah Bab 1 selesai, jika pemain berinteraksi dengan Luna sambil memegang **Kubis Segar**:
  * Aroma kubis memicu ingatan tersembunyi Luna (Glitch pusing):
    > *"Tunggu... aroma sayuran itu... Kubis Segar... Ada sebuah foto tua... 'Piece of Photo'... Aku pernah mendengarnya dari Bob si Petani."*
  * Pemain menemui **Bob si Petani**: Bob lapar dan meminta barter **Vegetable Sandwich** untuk ditukar dengan **Kepingan Foto [1/4]**.
  * Saat pecahan foto diserahkan ke Luna, muncul error glitch memori C-Compiler:
    > `"Benda ini..... ZYZYVWIWROIA: ERROR: Variable DON not found in . . ./a/1-1110-3/i.c line 54"`  
    > `Luna: "Bertemu. CD7F32 . 38. Sedih."`
  * Foto dikembalikan ke pemain, menjadi artefak pembuka misteri menuju Chapter 2 (Nether)!

---

### Chapter 2: Nether - Piglin Prison Break
* **Karakter Baru**: **Jaka Bawa Golok** & adiknya **Vivian**.
* **Alur Cerita**:
  * Jaka panik di desa meminta tolong menyelamatkan Vivian yang tersesat di Nether.
  * Pemain memasuki portal Nether, dipukul pingsan dari belakang.
  * Pemain terbangun di dalam penjara Piglin dengan tangan kosong (inventori tersita).
* **Teka-Teki & Misi Penjara**:
  * Menyelesaikan misi dari para tahanan lain untuk mencari jalan kabur.
  * Menyelamatkan Vivian.
* **Trigger Rahasia (Glitch 2 & Foto #2)**:
  * Di dalam sel terdapat tahanan bernama **Alif**.
  * Bawa batu custom **"Sang Raja Batu"** ke Alif.
  * Dialog Glitch Alif:
    > `"Batu yang keren.. Jujur aku suka sekali batu mu... apa {ERROR} Notice : Undefined variable believe in . . ./a/(Bold)753273(Normal)/am.c line 204"`
  * Pemain menerima **Kepingan Foto #2**.
* **Hadiah Akhir**:
  * Jaka memberikan **Titanium Alloy** kepada pemain: *"Benda itu akan berguna untuk kalian nanti, simpan saja, jika ada yang datang nanti, tunjukan saja itu."*

---

### Chapter 3: Nether - Runtuhnya Entitas (Entity 303)
* **Distorsi Dunia**:
  * Bob menghilang misterius.
  * Seluruh mob berhenti spawn di sekitar desa. Dunia terasa sepi dan hampa.
* **Trigger Rahasia (Glitch 3 & Foto #3)**:
  * Sebelum masuk portal, pemain bisa menemui **Hana** dan membawakannya **Nasi Goreng**.
  * Dialog Glitch Hana:
    > `"Wahh baunya enak!.. aku suka banget masak nasi goreng!, dia {ERROR} Notice : Undefined variable believe in . . ./a/(Bold)5337(Normal)/am.c line 11"`
  * Pemain menerima **Kepingan Foto #3**.
* **Klimaks Battle**:
  * Pemain memasuki portal Nether.
  * Portal Nether tiba-tiba **meledak**, membentuk arena terisolasi.
  * Boss Battle: **Entity 303**.

---

### Chapter 4: Overworld - Gerbang Stronghold & Sang Enderman Agung
* **Tantangan**:
  * Portal End di Stronghold terkunci rapat oleh aura mistis. Pemain tidak diizinkan masuk tanpa izin **Sang Enderman Agung**.
  * Diperlukan crafting custom item berkekuatan dahsyat: **"Ticket"** (diberikan resep dalam bentuk Map Art):
    * 1x Beacon
    * 2x Nether Star
    * 2x Eye of Forge (Crafting: 8x Ender Pearl + 1x Netherite Ingot)
    * 4x Netherite Ingot
* **Trigger Rahasia (Glitch 4 & Foto #4)**:
  * Jika pemain memakai/membawa item **Hairpin**:
  * Dialog Glitch:
    > `"kamu... cantik sekali memakai itu ERROR: [she] Unable to find 'she' in line 167 ./a/(Bold)668366(Normal)/am.c line 204"`
  * Pemain mendapatkan **Kepingan Foto #4** (Foto kini lengkap 4/4).

---

### Chapter 5: The End - Ilusi Herobrine & Kemunculan Kimoyara
* **The False Battle**:
  * Di The End, bukan Ender Dragon yang menunggu, melainkan **Herobrine**.
  * Boss fight melawan Herobrine.
* **The True Awakening (Cutscene Transisi)**:
  * Jika pemain memiliki & menyerahkan **4 Potongan Foto Lengkap**:
  * Herobrine bergetar dan glitching:
    > `"Apa ini... kau.... Selamat Da.... "`
  * Herobrine lenyap menjadi partikel kode.
  * **TypeWriter Cinematic**: Dipicu oleh engine cerita (`/typewriter trigger ch5_awakening <player>`) untuk mengunci kamera sinematik, efek letterbox, dan animasi kemunculan **Kimoyara (Ayarin Kusuma)** dari langit dimensi The End.
  * Kimoyara: *"Siapa kamu... Kenapa kamu merusak duniaku..."*
  * Final Battle melawan Kimoyara.

---

### Epilogue: "Chapter More Goodbye" (The TypeWriter Master Cutscene)
* **Kamera & Visual Sinematik (TypeWriter Plugin)**:
  * Kamera bergerak perlahan (slow pan) melintasi void/ruang hampa yang mulai retak.
  * Layar menggelap (fade to black) dengan transisi teks ketikan mesin tik kuno (*typewriter text pacing*).
* **Monolog Batin Aya**:
  > *"Semuanya pergi, aku sendiri lagi..."*  
  > *"Kenapa sebuah cerita.. pasti diakhiri perpisahan...."*  
  > *"Namun ada orang aneh yang tidak mau pergi.. Bramanzero... dia tidak pergi... Kenapa..? Apa alasannya....? Dia.... Mengingatkanku kepada seseorang......"*  
  > *"Ayah...?"*  
  > *"Apa kamu ayah..?"*  
  > *"...."*  
  > **Bramanzero**: *"Selamat ulang tahun... Putriku."*
* **Pesan Rekaman Terakhir Bramanzero**:
  > *"Entah tidak tahu kapan berakhirnya virus ini, yang pasti aku ingin kamu tetap hidup. Meskipun ini egois, tapi aku ingin kamu tetap bisa tumbuh dewasa dan merasakan dunia luar yang lebih luas. Aku tidak tahu kapan, tapi tunggulah, pasti bumi akan kembali normal. Dan satu hal lagi... kamu tidak sendirian... aku akan selalu menemanimu di mana pun, kapan pun."*

---

## 3. Catatan Review Narasi & Rekomendasi Teknis
1. **Kekuatan Cerita**: Plot twist dari RPG fantasi menuju cyberpunk/ARG psychological horror sangat kuat dan berkesan emosional.
2. **Kesesuaian dengan Game Loop SMP**:
   - Karena ini server multiplayer, Chapter harus memiliki mekanisme agar pemain baru tidak ketinggalan event pemain lama.
   - Penjara Piglin (Chapter 2) memerlukan sistem penyimpanan inventori sementara yang aman agar barang survival pemain tidak hilang permanen saat pingsan.
   - Boss arena (Chapter 1, 3, 5) harus mendukung party atau instancing agar pemain tidak berebut boss.
