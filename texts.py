"""Teks statis yang dikirim bot."""

NO_EMAIL = "Kamu belum punya email aktif. Tekan 📧 Email Baru dulu."

START = (
    "👋 Halo! Aku bot email sementara (tempmail).\n\n"
    "Buat email, pakai untuk daftar di situs apa saja, lalu kode OTP / link "
    "verifikasi yang masuk otomatis dikirim ke sini.\n\n"
    "Perintah:\n"
    "/new - pilih jenis email (mail.tm / Gmail / Outlook / Hotmail)\n"
    "/new nama - mail.tm dengan username sendiri\n"
    "/new nama password - username & password sendiri (password min. 6 karakter)\n"
    "/gmail /outlook /hotmail - alias langsung dari temp.tf\n"
    "/me - daftar emailmu, pilih email aktif\n"
    "/inbox - lihat pesan masuk\n"
    "/delete - hapus email aktif"
)

NEW_MENU = (
    "Mau buat email jenis apa?\n\n"
    "• <b>mail.tm</b>: domain acak, punya password, bisa pilih username sendiri "
    "(ketik <code>/new nama password</code>).\n"
    "• <b>Gmail / Outlook / Hotmail</b>: alias dari temp.tf, cuma untuk menerima pesan "
    "(tanpa password). Layanan temp.tf masih beta."
)
