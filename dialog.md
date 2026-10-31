# ==============================================================================
#                      VISUAL NOVEL DIALOGUE SCRIPT - CHAPTER 1
#                         Kisah Lembah Aethir & Penjaga Hantu
# ==============================================================================
# Panduan Tag Visual Novel:
# [speaker: <Nama>]                 -> Nama pembicara yang muncul di header dialog
# [portrait: <id_potret>]           -> ID gambar ekspresi karakter (default/happy/shock/thinking/angry)
# [delay: <detik>]                  -> Waktu jeda/pacing sebelum baris berikutnya (contoh: 2.5)
# [sound: <sound_key> | pitch: X]   -> Efek suara immersion Minecraft (contoh: entity.villager.ambient)
# [camera: freeze | letterbox]      -> Kunci pergerakan pemain & pasang mode sinematik
# [effect: darkness | shake | red]  -> Efek visual layar (kegelapan, getaran, kilatan merah)
# [choice: id | 1=Teks -> ACT1 | 2=Teks -> ACT2] -> Pilihan bercabang Dual-Interface (GUI + Chat)
# ==============================================================================

## CH1_PROLOGUE_MEET_LUNA
[camera: freeze | letterbox]
[speaker: Luna | portrait: happy | sound: minecraft:entity.villager.ambient | pitch: 1.2 | delay: 2.5]
Halo petualang! Namaku Luna. Senang akhirnya bisa bertemu seseorang di desa yang tenang ini.

[speaker: Luna | portrait: default | sound: minecraft:entity.villager.ambient | pitch: 1.0 | delay: 2.0]
Aku baru saja tiba dari perjalanan panjang dan sedang mendirikan perkemahan kecil di pinggir lembah.

[speaker: Luna | portrait: thinking | sound: minecraft:entity.villager.ambient | pitch: 1.1 | delay: 2.0]
Persediaanku mulai menipis... Maukah kamu membantuku mempersiapkan perbekalan desa?

[choice: CH1_START | 1=Tentu, aku siap membantu! -> TERIMA | 2=Maaf, aku sedang sibuk. -> TOLAK]


## CH1_QUEST_1_GATHER_WHEAT
# Status: Misi Gandum Aktif
[speaker: Luna | portrait: happy | sound: minecraft:entity.villager.yes | pitch: 1.2 | delay: 2.5]
Terima kasih banyak! Tugas pertamamu: bisakah kamu mengumpulkan 10 Gandum segar dari ladang?

[speaker: Luna | portrait: default | sound: minecraft:block.note_block.harp | pitch: 1.0 | delay: 2.0]
Gandum itu sangat penting untuk membuat roti perbekalan sebelum kita menjelajah lebih jauh.


## CH1_QUEST_1_SUBMIT_CHECK
# Dialog saat pemain kembali bicara ke Luna saat Quest 1 aktif
[speaker: Luna | portrait: default | sound: minecraft:entity.villager.ambient | pitch: 1.0 | delay: 2.0]
Bagaimana perkembangannya? Apakah kamu sudah membawakan 10 Gandum yang kuminta?

[choice: CH1_SUBMIT_WHEAT | 1=Serahkan 10 Gandum -> SUBMIT | 2=Belum, aku masih mengumpulkannya -> WAIT]


## CH1_QUEST_2_GATHER_APPLES
# Status: Gandum Diterima -> Penawaran Misi Apel
[speaker: Luna | portrait: happy | sound: minecraft:entity.player.levelup | pitch: 1.4 | delay: 2.5]
Wah, gandum yang sangat harum dan padat! Ini 5 Ruby dan hadiah pengalaman untukmu.

[speaker: Luna | portrait: default | sound: minecraft:entity.villager.ambient | pitch: 1.1 | delay: 2.0]
Selanjutnya, orang desa bilang kebun apel di sebelah barat sedang berbuah lebat.

[speaker: Luna | portrait: thinking | sound: minecraft:entity.villager.ambient | pitch: 1.0 | delay: 2.0]
Bisakah kamu memetik 5 Apel Merah segar untuk melengkapi ransum kita?

[choice: CH1_ACCEPT_APPLES | 1=Siap, aku akan petik apelnya! -> TERIMA | 2=Tunggu sebentar, aku butuh istirahat. -> NANTI]


## CH1_QUEST_2_SUBMIT_CHECK
# Dialog saat pemain kembali bicara ke Luna saat Quest 2 aktif
[speaker: Luna | portrait: default | sound: minecraft:entity.villager.ambient | pitch: 1.0 | delay: 2.0]
Apakah 5 Apel Merah manisnya sudah terkumpul?

[choice: CH1_SUBMIT_APPLES | 1=Serahkan 5 Apel -> SUBMIT | 2=Belum, sebentar lagi! -> WAIT]


## CH1_QUEST_3_OLD_WELL
# Status: Apel Diterima -> Penugasan Selidiki Sumur Tua
[speaker: Luna | portrait: happy | sound: minecraft:entity.player.levelup | pitch: 1.4 | delay: 2.5]
Apelnya segar sekali, renyah dan manis! Terima kasih atas bantuanmu, kawan.

[speaker: Luna | portrait: thinking | sound: minecraft:entity.villager.ambient | pitch: 0.9 | delay: 2.5]
Sebenarnya... ada satu hal aneh yang kudengar dari warga desa tadi pagi.

[speaker: Luna | portrait: default | sound: minecraft:entity.villager.ambient | pitch: 1.0 | delay: 2.5]
Di ujung desa ada Sumur Tua kuno yang konon mengeluarkan hawa dingin yang ganjil.

[speaker: Luna | portrait: default | sound: minecraft:block.note_block.bell | pitch: 1.0 | delay: 2.0]
Bisakah kamu memeriksanya? Berhati-hatilah dan amati sekitar sumur itu ya.


## CH1_DISCOVER_STRANGE_TRACKS
# Terpicu otomatis saat pemain berada di dekat Sumur Tua (ch1_village)
[camera: freeze | letterbox]
[effect: darkness 2s | sound: minecraft:block.sculk_sensor.clicking | pitch: 0.7 | delay: 2.5]
Kamu mendekati bibir Sumur Tua... Hawa dingin menusuk tulang merayapi kakimu.

[effect: sound: minecraft:entity.warden.heartbeat | pitch: 0.8 | delay: 3.0]
Tunggu! Di atas lumut basah sekitar sumur... terdapat jejak langkah kaki hitam yang aneh!

[effect: sound: minecraft:block.beacon.ambient | pitch: 0.6 | delay: 3.0]
Jejak itu tidak mengarah kembali ke desa, melainkan meluncur turun menuju sebuah celah Goa Bawah Tanah yang gelap gulita...

[speaker: Batin Petualang | portrait: shock | delay: 2.0]
(Aku harus menelusuri goa ini sekarang sebelum jejaknya memudar!)


## CH1_PRE_BOSS_ENCOUNTER
# Terpicu saat pemain mendekati sarang goa bawah tanah (ch1_boss)
[camera: freeze | letterbox]
[effect: darkness 4s | sound: minecraft:entity.warden.emerge | pitch: 0.5 | delay: 3.5]
Ruangan goa bawah tanah mendadak sunyi senyap... Suhu ruangan anjlok drastis hingga membekukan nafasmu.

[speaker: Suara Misterius | portrait: shadow | sound: minecraft:entity.wither.ambient | pitch: 0.5 | delay: 3.5]
Siapa... yang berani mengusik kuburan dingin ini setelah sepuluh tahun terlelap...?

[effect: shake | sound: minecraft:entity.warden.roar | pitch: 0.6 | delay: 3.5]
[speaker: Penjaga Hantu | portrait: ghost_angry]
Kalian membawa aroma desa itu... Aroma kepalsuan dan waktu yang membusuk!

[effect: darkness 2s | sound: minecraft:block.respawn_anchor.charge | pitch: 0.8 | delay: 3.0]
[speaker: Penjaga Hantu | portrait: ghost_angry]
Tidak ada yang boleh pergi dari sini dengan membawa rahasia masa lalu...

[effect: shake | sound: minecraft:entity.warden.sonic_boom | pitch: 0.7 | delay: 2.0]
[speaker: Penjaga Hantu | portrait: ghost_angry]
RASAKAN MURKA ABAD KEGELAPAN! DOMAIN EXPANSION!


## CH1_BOSS_DEFEATED_MERCY
# Terpicu saat voting MERCY menang
[speaker: Penjaga Hantu | portrait: ghost_calm | sound: minecraft:block.beacon.deactivate | pitch: 0.8 | delay: 3.0]
Kalian... memilih untuk membiarkanku hidup...? Sungguh hati yang aneh di dunia yang kejam ini...

[speaker: Penjaga Hantu | portrait: ghost_calm | sound: minecraft:ui.toast.challenge_complete | pitch: 1.0 | delay: 3.0]
Ambillah buku catatan tua ini... Ini adalah 'Kisah Katulise'. Bacalah, dan pahami mengapa dunia ini terkunci...


## CH1_BOSS_DEFEATED_KILL
# Terpicu saat voting KILL menang
[effect: shake | sound: minecraft:entity.generic.explode | pitch: 0.7 | delay: 2.5]
[speaker: Penjaga Hantu | portrait: ghost_angry]
Kutukan es ini... tidak akan pernah... padam...!

[effect: sound: minecraft:block.glass.break | pitch: 0.5 | delay: 2.5]
Tubuh Penjaga Hantu hancur menjadi serpihan es abadi, meninggalkan Kitab Es Kuno di atas tanah...


## CH1_REPORT_TO_LUNA
# Pemain kembali ke desa dan melapor ke Luna setelah Boss selesai
[camera: freeze | letterbox]
[speaker: Luna | portrait: shock | sound: minecraft:entity.villager.ambient | pitch: 1.4 | delay: 3.0]
Kamu kembali! Wajahmu pucat sekali... Apa yang sebenarnya terjadi di bawah sana?!

[speaker: Luna | portrait: thinking | sound: minecraft:entity.villager.ambient | pitch: 0.9 | delay: 3.0]
Goa tersembunyi... Penjaga Hantu... dan ruang kutukan Domain?! Mengerikan sekali...

[speaker: Luna | portrait: happy | sound: minecraft:ui.toast.challenge_complete | pitch: 1.0 | delay: 3.0]
Kamu benar-benar pahlawan sejati Lembah Aethir. Desa ini berhutang budi padamu!

[speaker: Luna | portrait: happy | sound: minecraft:entity.player.levelup | pitch: 1.2 | delay: 2.5]
Mulai sekarang, aku akan tinggal di sini dan membuka Papan Misi Harian setiap hari. Datanglah kapan pun kamu butuh tugas baru!
# Event: CH1_COMPLETED -> Buka Daily Quest Board Luna


## CH1_SIDEQUEST_CABBAGE_GLITCH
# Terpicu saat pemain memegang KUBIS SEGAR dan berbicara ke Luna (Pasca-Ch1)
[camera: freeze | letterbox]
[effect: sound: minecraft:block.beacon.ambient | pitch: 0.7 | delay: 2.0]
[speaker: Luna | portrait: shock]
Tunggu... aroma sayuran itu... Kubis Segar...

[effect: darkness 1s | sound: minecraft:entity.warden.heartbeat | pitch: 0.6 | delay: 2.5]
[speaker: Luna | portrait: shock]
Argh... kepalaku mendadak pusing sekali... seperti ada potongan memori yang dipaksa keluar dari pikiranku...

[speaker: Luna | portrait: thinking | sound: minecraft:entity.villager.ambient | pitch: 0.8 | delay: 2.5]
Ada sebuah foto tua... 'Piece of Photo'... Aku pernah mendengar Bob si Petani membicarakannya.

[speaker: Luna | portrait: default | sound: minecraft:entity.villager.ambient | pitch: 1.0 | delay: 2.0]
Tolong temui Bob di ladang seberang dan tanyakan tentang foto itu untukku!


## CH1_SIDEQUEST_BOB_SANDWICH
# Interaksi dengan Bob si Petani
[speaker: Bob si Petani | portrait: default | sound: minecraft:entity.villager.ambient | pitch: 0.9 | delay: 2.5]
Kepingan foto tua? Ya, aku menemukannya saat mencangkul tanah kemarin! Tapi perutku keroncongan sekali...

[speaker: Bob si Petani | portrait: happy | sound: minecraft:entity.villager.yes | pitch: 1.1 | delay: 2.5]
Buatkan aku 1 Sandwich Segar yang renyah (Roti + Kubis + Tomat), baru kuberikan foto itu padamu!

[choice: CH1_SUBMIT_SANDWICH | 1=Serahkan Sandwich Segar -> SUBMIT | 2=Tunggu, aku buatkan dulu! -> WAIT]


## CH1_SIDEQUEST_LUNA_GLITCH_FINALE
# Penyerahan Foto #1 ke Luna
[camera: freeze | letterbox]
[speaker: Luna | portrait: shock | sound: minecraft:entity.villager.ambient | pitch: 1.1 | delay: 2.0]
Kamu berhasil membawanya?! Coba kulihat kepingan itu...

[effect: darkness 3s | shake | sound: minecraft:entity.warden.heartbeat | pitch: 0.5 | delay: 2.5]
[speaker: Luna | portrait: glitch]
Benda ini.....

[effect: sound: minecraft:entity.elder_guardian.curse | pitch: 1.5 | delay: 3.5]
[speaker: SYSTEM_ERROR | portrait: glitch]
ZYZYVWIWROIA: ERROR: Variable DON not found in . . ./a/1-1110-3/i.c line 54
[CD7F32] Bertemu. CD7F32 . 38. Sedih.

[effect: sound: minecraft:block.beacon.deactivate | pitch: 0.8 | delay: 3.0]
[speaker: Luna | portrait: default]
M-maafkan aku... pandanganku mendadak kabur seketika. Simpanlah foto ini baik-baik. Misteri ini terasa jauh lebih besar dari yang kita duga...
