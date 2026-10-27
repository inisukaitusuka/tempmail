"""Pengaturan bot: baca .env, konstanta, dan logging."""

import logging
import os
from pathlib import Path

from telegram import LinkPreviewOptions

BASE_DIR = Path(__file__).resolve().parent


def load_env():
    """Baca file .env di folder script (format: NAMA=nilai). Variabel environment tetap diutamakan."""
    path = BASE_DIR / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


load_env()

# ====================== PENGATURAN ======================
# Token bot diambil dari environment variable / file .env (JANGAN ditulis langsung di sini
# kalau kodenya mau di-push ke GitHub).
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "ISI_TOKEN_BOT_DISINI"
CHECK_INTERVAL = 15  # detik, jeda cek inbox
MAX_EMAILS = 10  # maksimal email per user
# ========================================================

API = "https://api.mail.tm"
TF_API = "https://temp.tf/api"
# parameter GET /account di temp.tf untuk tiap jenis alias
TF_PRESETS = {
    "gmail": {"dot": 1, "plus": 1, "providers": "gmail"},
    "outlook": {"plus": 1, "providers": "outlook"},
    "hotmail": {"plus": 1, "providers": "hotmail"},
}
DATA_FILE = BASE_DIR / "tempmail_data.json"
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("tempmail")
