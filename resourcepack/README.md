# Visual Novel Dialogue HUD Resource Pack Guide (Java & Bedrock)

Folder ini adalah template Resource Pack untuk menampilkan **Custom Visual Novel Dialogue Box & Potret Karakter 2D** seperti contoh screenshot referensi.

---

## 1. Pemetaan Karakter Unicode (Glyph Mapping)
| Karakter Unicode | Deskripsi Tekstur | Nama File | Ukuran Rekomendasi |
| :---: | :---: | :---: | :---: |
| `\uE001` | Background Kotak Dialog Melengkung | `textures/font/dialogue_box.png` | 256x64 px (Transparan/Frame) |
| `\uE002` | Plat Nama Pembicara (Nameplate) | `textures/font/nameplate.png` | 96x20 px |
| `\uE010` | Potret Anime Luna | `textures/font/portrait_luna.png` | 64x64 px (PNG transparan) |
| `\uE011` | Potret Bob si Petani | `textures/font/portrait_bob.png` | 64x64 px (PNG transparan) |
| `\uE012` | Potret Penjaga Hantu | `textures/font/portrait_ghost.png` | 64x64 px (PNG transparan) |

---

## 2. Cara Kerja di Skript
Ketika sistem dialog mengirimkan teks:
- **Jika Resource Pack Aktif**: Skript mengirimkan string font custom via Title/Subtitle atau Actionbar dengan karakter unicode di atas.
- **Jika Resource Pack Belum Dipasang**: Skript secara otomatis mendeteksi dan beralih ke mode **Auto Fallback (Cinematic Title/Subtitle + Sound Pacing)** tanpa menampilkan karakter rusak atau box kosong.

---

## 3. Kompatibilitas Bedrock Edition (Geyser / Floodgate)
Agar pemain Bedrock (HP/Konsol) dapat melihat tekstur yang sama persis:
1. Konversi folder resource pack ini menjadi format `.mcpack` atau masukkan ke dalam folder `plugins/Geyser-Spigot/packs/`.
2. Geyser akan secara otomatis menyinkronkan font custom ke klien Bedrock yang terhubung ke server.
