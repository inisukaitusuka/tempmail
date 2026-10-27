# 📧 TempMail Telegram Bot

Bot Telegram untuk membuat **email sementara** dan membaca inbox-nya langsung dari chat. Kode OTP dan link verifikasi yang masuk dikirim otomatis ke Telegram.

> English: a Telegram bot that creates disposable email addresses (via mail.tm and temp.tf) and forwards incoming mail to your chat.

## Fitur

- **Dua sumber email**
  - [mail.tm](https://mail.tm): domain acak, punya password, bisa pilih username dan password sendiri.
  - [temp.tf](https://temp.tf): alias Gmail, Outlook, atau Hotmail (hanya untuk menerima pesan, tanpa password).
- **Banyak email per pengguna** (maksimal 10), ganti email aktif kapan saja lewat `/me`. Email lama tidak dihapus saat membuat yang baru.
- **Notifikasi otomatis**: pesan baru di semua emailmu dikirim ke Telegram (dicek tiap 15 detik).
- **Tampilan email rapi**: link panjang (misalnya link tracking) disingkat tapi tetap bisa di-tap, dan email yang panjang dipecah jadi beberapa pesan, bukan dipotong begitu saja.
- **Sederhana**: kode dipisah per modul (lihat [Struktur project](#struktur-project)), data disimpan di satu file JSON, tanpa database.

## Perintah

| Perintah | Fungsi |
|---|---|
| `/start` | Menu utama |
| `/new` | Pilih jenis email yang mau dibuat (mail.tm / Gmail / Outlook / Hotmail) |
| `/new nama` | mail.tm dengan username sendiri |
| `/new nama password` | mail.tm dengan username dan password sendiri (password 6-64 karakter) |
| `/gmail` `/outlook` `/hotmail` | Langsung buat alias dari temp.tf |
| `/me` | Daftar semua emailmu, tap salah satu untuk dijadikan email aktif |
| `/inbox` | Pesan masuk di email aktif (tap untuk membaca) |
| `/delete` | Hapus email aktif |

Bot hanya merespons di chat pribadi (bukan di grup).

## Instalasi

Yang dibutuhkan: **Python 3.10 atau lebih baru** dan token bot dari [@BotFather](https://t.me/BotFather) (kirim `/newbot`).

```bash
git clone https://github.com/USERNAME/tempmail-telegram-bot.git
cd tempmail-telegram-bot

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
nano .env                       # isi BOT_TOKEN dengan token dari BotFather

python main.py
```

Ganti `USERNAME` dengan nama akun GitHub tempat repo ini berada. Di Ubuntu/Debian, kalau `python3 -m venv` gagal, pasang dulu: `sudo apt install python3 python3-venv`.

Kalau di log muncul baris `Bot jalan...`, bot sudah aktif. Buka bot kamu di Telegram lalu kirim `/start`.

## Menjalankan di background

**Opsi A: screen** (paling mudah)

```bash
sudo apt install screen
screen -S tempmail
source venv/bin/activate
python main.py
# lepas dengan Ctrl+A lalu D; buka lagi dengan: screen -r tempmail
```

**Opsi B: systemd** (otomatis hidup lagi setelah server restart)

1. Pindahkan project ke `/opt/tempmail-telegram-bot` (atau sesuaikan path di file service).
2. Salin dan aktifkan service:

```bash
sudo cp deploy/tempmail-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tempmail-bot
sudo systemctl status tempmail-bot      # cek statusnya
journalctl -u tempmail-bot -f           # lihat log
```

## Konfigurasi

- `BOT_TOKEN` dibaca dari environment variable atau file `.env` (lihat `.env.example`).
- Pengaturan lain ada di bagian `PENGATURAN` dekat bagian atas `config.py`:
  - `CHECK_INTERVAL`: jeda cek inbox dalam detik (default 15)
  - `MAX_EMAILS`: maksimal email per pengguna (default 10)
- Data pengguna disimpan di `tempmail_data.json` (di folder yang sama dengan script).

## Struktur project

| File | Isi |
|---|---|
| `main.py` | Titik masuk: menyalakan bot, mendaftarkan perintah, menjalankan tugas latar belakang |
| `config.py` | Baca `.env`, pengaturan (`BOT_TOKEN`, `CHECK_INTERVAL`, `MAX_EMAILS`), konstanta API, logging |
| `state.py` | Data user di memori + simpan/muat `tempmail_data.json` |
| `client.py` | Akses API mail.tm dan temp.tf (buat email, baca inbox, hapus) |
| `handlers.py` | Handler perintah (`/start`, `/new`, ...) dan tombol inline |
| `actions.py` | Logika tiap aksi: buat email, ganti email aktif, inbox, baca pesan, hapus |
| `jobs.py` | Tugas latar belakang yang mengecek pesan baru dan mengirimnya ke Telegram |
| `render.py` | Ubah isi email (HTML/teks) jadi pesan Telegram yang rapi |
| `keyboards.py` | Tombol inline yang tampilannya tetap |
| `texts.py` | Teks statis (sambutan, menu, dll) |
| `utils.py` | Fungsi kecil bersama + helper kirim pesan |

## Cara kerja singkat

- **mail.tm**: bot mengambil domain yang tersedia, membuat akun, mengambil token, lalu membaca pesan lewat [API mail.tm](https://docs.mail.tm).
- **temp.tf**: bot meminta alamat alias (`GET /account`) dan membaca inbox-nya (`POST /check`).
- Satu tugas latar belakang mengecek semua email setiap beberapa detik dan mengirim pesan yang belum pernah dikirim. Untuk temp.tf, bot menghormati batas permintaan layanan (60 per menit per IP) dan menunggu sesuai `Retry-After` kalau kena batas.

## Keamanan dan privasi

- **Jangan commit `.env` dan `tempmail_data.json`.** Keduanya sudah ada di `.gitignore`. File data berisi token dan password email sementara serta ID Telegram pengguna.
- Kalau token bot pernah terlanjur terpublikasi, buat token baru lewat @BotFather (`/revoke`), lalu perbarui `.env`.
- Email sementara sebaiknya **tidak dipakai untuk akun penting atau data sensitif**. Inbox alias temp.tf dan layanan sejenis bersifat sementara dan dikelola pihak ketiga.
- Proyek ini tidak berafiliasi dengan mail.tm maupun temp.tf. Layanan mereka bisa berubah atau berhenti kapan saja, dan temp.tf saat ini masih berlabel beta. Patuhi ketentuan layanan masing-masing dan ketentuan situs tempat kamu mendaftar.

## Batasan

- Lampiran email belum bisa diunduh lewat bot (bot hanya memberi tahu kalau ada).
- Alias temp.tf tidak bisa dihapus dari server mereka; menghapusnya di bot hanya membuangnya dari daftar.
- Email yang sangat panjang dipecah maksimal menjadi 3 pesan Telegram, sisanya dipotong.

## Lisensi

[MIT](LICENSE)
