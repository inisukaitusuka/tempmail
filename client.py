"""Akses ke API mail.tm dan temp.tf."""

import random
import re

import httpx

from config import API, TF_API, TF_PRESETS, log
from state import save
from utils import is_tf, rand

http = None  # httpx.AsyncClient, dibuat saat bot start (start_http)


async def start_http():
    global http
    http = httpx.AsyncClient(timeout=20)


async def close_http():
    if http:
        await http.aclose()


# ------------------------------------------------------------ error
class MailError(Exception):
    pass


class AccountGone(MailError):
    pass


class RateLimited(MailError):
    def __init__(self, wait=30):
        super().__init__("Terlalu banyak permintaan, tunggu sebentar lalu coba lagi.")
        self.wait = wait


# ------------------------------------------------------------ mail.tm
def members(data):
    """Ambil daftar item dari respon mail.tm (format hydra atau list biasa)."""
    if isinstance(data, dict):
        return data.get("hydra:member", [])
    return data or []


async def get_domain():
    r = await http.get(f"{API}/domains")
    r.raise_for_status()
    active = [d["domain"] for d in members(r.json()) if d.get("isActive", True)]
    if not active:
        raise MailError("Belum ada domain yang tersedia, coba lagi nanti.")
    return random.choice(active)


async def get_token(address, password):
    r = await http.post(f"{API}/token", json={"address": address, "password": password})
    if r.status_code == 401:
        raise AccountGone("Email ini sudah tidak aktif.")
    r.raise_for_status()
    return r.json()["token"]


async def create_account(username=None, password=None):
    domain = await get_domain()
    address = f"{username or rand(10)}@{domain}"
    password = password or rand(16)
    r = await http.post(f"{API}/accounts", json={"address": address, "password": password})
    if r.status_code == 422:
        raise MailError("Username itu sudah dipakai atau tidak valid, coba yang lain.")
    if r.status_code == 429:
        raise RateLimited()
    r.raise_for_status()
    acc = r.json()
    token = await get_token(address, password)
    return {
        "id": acc["id"],
        "address": address,
        "password": password,
        "token": token,
        "seen": [],
    }


async def authed(u, method, path, **kw):
    """Request dengan Bearer token; kalau token kadaluarsa, ambil token baru."""
    r = None
    for attempt in range(2):
        r = await http.request(
            method, API + path, headers={"Authorization": f"Bearer {u['token']}"}, **kw
        )
        if r.status_code == 401 and attempt == 0:
            u["token"] = await get_token(u["address"], u["password"])
            save()
            continue
        break
    return r


# ------------------------------------------------------------ temp.tf
def tf_raise(r):
    if r.status_code == 429:
        try:
            wait = int(r.headers.get("Retry-After", 30))
        except Exception:
            wait = 30
        raise RateLimited(wait)


def tf_norm(m):
    """Ubah format pesan temp.tf supaya sama dengan format mail.tm."""
    frm = m.get("from")
    if isinstance(frm, dict):
        sender = {"address": frm.get("address") or frm.get("email") or "?", "name": frm.get("name")}
    else:
        s = str(frm or "?")
        mt = re.match(r'\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$', s)
        if mt:
            sender = {"address": mt.group(2), "name": mt.group(1).strip() or None}
        else:
            sender = {"address": s, "name": None}
    body = m.get("body") or ""
    is_html = (m.get("bodyContentType") or "html").lower() == "html"
    return {
        "id": str(m.get("id")),
        "subject": m.get("subject"),
        "from": sender,
        "text": "" if is_html else body,
        "html": [body] if is_html else [],
        "hasAttachments": bool(m.get("attachments")),
        "createdAt": m.get("date") or "",
    }


async def tf_new_address(kind):
    r = await http.get(f"{TF_API}/account", params=TF_PRESETS[kind])
    tf_raise(r)
    r.raise_for_status()
    email = r.json().get("email")
    if not email:
        raise MailError("temp.tf tidak memberikan alamat email, coba lagi.")
    return email


async def tf_check(address):
    r = await http.post(f"{TF_API}/check", json={"email": address})
    tf_raise(r)
    r.raise_for_status()
    msgs = [tf_norm(m) for m in (r.json().get("data") or [])]
    msgs.sort(key=lambda m: m["createdAt"], reverse=True)  # terbaru di atas
    return msgs


# ------------------------------------------------- inbox (dua jenis)
async def list_messages(u):
    if is_tf(u):
        return await tf_check(u["address"])
    r = await authed(u, "GET", "/messages?page=1")
    r.raise_for_status()
    return members(r.json())


async def get_message(u, msg_id):
    if is_tf(u):
        for m in await tf_check(u["address"]):
            if m["id"] == msg_id or m["id"][:55] == msg_id:
                return m
        return None
    r = await authed(u, "GET", f"/messages/{msg_id}")
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


async def delete_remote(u):
    if is_tf(u):
        return  # temp.tf tidak punya fitur hapus
    try:
        await authed(u, "DELETE", f"/accounts/{u['id']}")
    except Exception:
        log.warning("Gagal hapus akun di mail.tm", exc_info=True)
