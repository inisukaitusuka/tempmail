"""Data user + simpan/muat tempmail_data.json."""

import json

from config import DATA_FILE, log

# {"<user_id>": {"active": "<id email aktif>", "accounts": [
#     {"id", "provider" ("tf" atau kosong = mail.tm), "address", "password",
#      "token", "seen": [...]}, ...]}}
#
# PENTING: dict ini jangan diganti dengan dict baru (users = {...}), cukup diubah isinya
# (clear/update), karena modul lain meng-import objek yang sama.
users = {}


def load():
    users.clear()
    if DATA_FILE.exists():
        try:
            users.update(json.loads(DATA_FILE.read_text()))
        except Exception:
            log.warning("File data rusak, mulai dari kosong")
            users.clear()
    # ubah format lama (1 email per user) ke format baru (banyak email)
    migrated = False
    for key, v in list(users.items()):
        if "accounts" not in v:
            users[key] = {"active": v.get("id"), "accounts": [v]}
            migrated = True
    if migrated:
        save()
    total = sum(len(v["accounts"]) for v in users.values())
    log.info("Data dimuat dari %s: %d user, %d email", DATA_FILE, len(users), total)


def save():
    DATA_FILE.write_text(json.dumps(users, indent=2))


def get_active(uid):
    """Email yang sedang aktif milik user (atau None)."""
    rec = users.get(str(uid))
    if not rec or not rec["accounts"]:
        return None
    for a in rec["accounts"]:
        if a["id"] == rec.get("active"):
            return a
    return rec["accounts"][-1]


def add_account(uid, acc):
    rec = users.setdefault(str(uid), {"active": None, "accounts": []})
    rec["accounts"].append(acc)
    rec["active"] = acc["id"]
    save()


def drop_account(rec, acc):
    """Buang satu email dari daftar; kalau itu yang aktif, pindah ke email terakhir."""
    if acc in rec["accounts"]:
        rec["accounts"].remove(acc)
    if rec.get("active") == acc["id"]:
        rec["active"] = rec["accounts"][-1]["id"] if rec["accounts"] else None
    save()
