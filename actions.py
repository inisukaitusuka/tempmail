"""Aksi bot: buat email, ganti email aktif, inbox, baca pesan, hapus."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from client import (
    AccountGone,
    MailError,
    RateLimited,
    create_account,
    delete_remote,
    get_message,
    list_messages,
    tf_check,
    tf_new_address,
)
from config import MAX_EMAILS, TF_PRESETS, log
from keyboards import main_menu, new_menu
from render import message_parts
from state import add_account, drop_account, get_active, save, users
from texts import NEW_MENU, NO_EMAIL
from utils import creds, esc, rand, send, send_parts


async def at_limit(ctx, uid):
    rec = users.get(str(uid))
    if rec and len(rec["accounts"]) >= MAX_EMAILS:
        await send(
            ctx,
            uid,
            f"⚠️ Maksimal {MAX_EMAILS} email. Hapus salah satu dulu: buka 📋 Email Saya, "
            "pilih emailnya, lalu tekan 🗑 Hapus Email.",
            main_menu(),
        )
        return True
    return False


async def do_new_menu(ctx, uid):
    await send(ctx, uid, NEW_MENU, new_menu())


async def do_new(ctx, uid, username=None, password=None):
    if await at_limit(ctx, uid):
        return
    try:
        acc = await create_account(username, password)
    except MailError as e:
        await send(ctx, uid, f"⚠️ {esc(e)}")
        return
    except Exception:
        log.exception("create_account gagal")
        await send(ctx, uid, "⚠️ Gagal membuat email, coba lagi sebentar lagi.")
        return
    add_account(uid, acc)
    await send(
        ctx,
        uid,
        f"✅ Email baru siap (sekarang jadi email aktif):\n\n{creds(acc)}\n\n"
        "Tap untuk menyalin. Pesan yang masuk akan otomatis dikirim ke sini.",
        main_menu(),
    )


async def do_new_tf(ctx, uid, kind):
    if kind not in TF_PRESETS:
        return
    if await at_limit(ctx, uid):
        return
    try:
        address = await tf_new_address(kind)
        rec = users.get(str(uid))
        if rec and any(a["address"].lower() == address.lower() for a in rec["accounts"]):
            address = await tf_new_address(kind)  # dapat alamat yang sama, coba sekali lagi
        existing = []
        try:  # catat pesan yang sudah ada supaya tidak dikirim sebagai "pesan baru"
            existing = [m["id"] for m in await tf_check(address)]
        except Exception:
            log.warning("Cek awal inbox temp.tf gagal", exc_info=True)
    except MailError as e:
        await send(ctx, uid, f"⚠️ {esc(e)}")
        return
    except Exception:
        log.exception("tf_new_address gagal")
        await send(ctx, uid, "⚠️ Gagal membuat email dari temp.tf, coba lagi sebentar lagi.")
        return
    acc = {
        "id": "tf" + rand(10),
        "provider": "tf",
        "address": address,
        "password": None,
        "token": None,
        "seen": existing[-200:],
    }
    add_account(uid, acc)
    await send(
        ctx,
        uid,
        f"✅ Email {kind.capitalize()} siap (sekarang jadi email aktif):\n\n{creds(acc)}\n\n"
        "Email ini hanya untuk menerima pesan, tidak ada password. Tap alamatnya untuk "
        "menyalin. Pesan yang masuk akan otomatis dikirim ke sini.",
        main_menu(),
    )


async def do_me(ctx, uid):
    rec = users.get(str(uid))
    act = get_active(uid)
    if not rec or not act:
        await send(ctx, uid, NO_EMAIL, main_menu())
        return
    rows = []
    for a in rec["accounts"]:
        mark = "✅ " if a is act else ""
        rows.append(
            [InlineKeyboardButton((mark + a["address"])[:60], callback_data=f"use:{a['id']}")]
        )
    rows.append(
        [
            InlineKeyboardButton("📧 Email Baru", callback_data="new"),
            InlineKeyboardButton("📥 Inbox", callback_data="inbox"),
        ]
    )
    rows.append([InlineKeyboardButton("🗑 Hapus Email Aktif", callback_data="del")])
    await send(
        ctx,
        uid,
        f"📋 Kamu punya {len(rec['accounts'])} email. Tap salah satu untuk dijadikan email aktif.\n\n"
        f"Aktif:\n{creds(act)}",
        InlineKeyboardMarkup(rows),
    )


async def do_use(ctx, uid, acc_id):
    rec = users.get(str(uid))
    if not rec:
        await send(ctx, uid, NO_EMAIL, main_menu())
        return
    acc = next((a for a in rec["accounts"] if a["id"] == acc_id), None)
    if not acc:
        await send(ctx, uid, "Email itu sudah tidak ada di daftar.", main_menu())
        return
    rec["active"] = acc["id"]
    save()
    await send(ctx, uid, f"✅ Email aktif sekarang:\n\n{creds(acc)}", main_menu())


async def do_inbox(ctx, uid):
    rec = users.get(str(uid))
    u = get_active(uid)
    if not rec or not u:
        await send(ctx, uid, NO_EMAIL, main_menu())
        return
    try:
        msgs = await list_messages(u)
    except AccountGone:
        drop_account(rec, u)
        await send(
            ctx,
            uid,
            f"⚠️ Email <code>{esc(u['address'])}</code> sudah tidak aktif dan dibuang dari daftar. "
            "Buka 📋 Email Saya untuk pilih email lain, atau buat yang baru.",
            main_menu(),
        )
        return
    except RateLimited as e:
        await send(ctx, uid, f"⚠️ {esc(e)}")
        return
    except Exception:
        log.exception("list_messages gagal")
        await send(ctx, uid, "⚠️ Gagal mengambil inbox, coba lagi.")
        return
    bottom = [
        InlineKeyboardButton("🔄 Refresh", callback_data="inbox"),
        InlineKeyboardButton("📋 Email Saya", callback_data="me"),
    ]
    if not msgs:
        await send(
            ctx,
            uid,
            f"📭 Inbox kosong.\n<code>{esc(u['address'])}</code>",
            InlineKeyboardMarkup([bottom]),
        )
        return
    rows = []
    for m in msgs[:10]:
        frm = (m.get("from") or {}).get("address", "?")
        label = f"{m.get('subject') or '(tanpa subjek)'} — {frm}"
        rows.append([InlineKeyboardButton(label[:60], callback_data=f"read:{m['id'][:55]}")])
    rows.append(bottom)
    await send(
        ctx,
        uid,
        f"📥 Inbox <code>{esc(u['address'])}</code>\nTap pesan untuk membaca:",
        InlineKeyboardMarkup(rows),
    )


async def do_read(ctx, uid, msg_id):
    u = get_active(uid)
    if not u:
        await send(ctx, uid, NO_EMAIL, main_menu())
        return
    try:
        m = await get_message(u, msg_id)
    except RateLimited as e:
        await send(ctx, uid, f"⚠️ {esc(e)}")
        return
    except Exception:
        log.exception("get_message gagal")
        await send(ctx, uid, "⚠️ Gagal membuka pesan, coba lagi.")
        return
    if not m:
        await send(
            ctx,
            uid,
            "Pesan tidak ditemukan. Mungkin itu dari email lain, cek 📋 Email Saya "
            "untuk memastikan email yang aktif.",
        )
        return
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Inbox", callback_data="inbox")]])
    await send_parts(ctx, uid, message_parts(m), kb)


async def do_delete_confirm(ctx, uid):
    u = get_active(uid)
    if not u:
        await send(ctx, uid, NO_EMAIL, main_menu())
        return
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Ya, hapus", callback_data="delyes"),
                InlineKeyboardButton("Batal", callback_data="me"),
            ]
        ]
    )
    await send(
        ctx,
        uid,
        f"Hapus email aktif <code>{esc(u['address'])}</code>? Pesannya tidak bisa dibuka lagi lewat bot.",
        kb,
    )


async def do_delete(ctx, uid):
    rec = users.get(str(uid))
    u = get_active(uid)
    if not rec or not u:
        await send(ctx, uid, NO_EMAIL, main_menu())
        return
    drop_account(rec, u)
    await delete_remote(u)
    nxt = get_active(uid)
    extra = (
        f"\n\nEmail aktif sekarang: <code>{esc(nxt['address'])}</code>"
        if nxt
        else "\n\nKamu tidak punya email lagi. Tekan 📧 Email Baru untuk membuat."
    )
    await send(ctx, uid, f"🗑 Email <code>{esc(u['address'])}</code> sudah dihapus.{extra}", main_menu())
