"""Fungsi kecil yang dipakai banyak modul + helper kirim pesan Telegram."""

import html
import random
import string

from telegram.constants import ParseMode

from config import NO_PREVIEW


def esc(s):
    return html.escape(str(s), quote=False)


def rand(n):
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(n))


def is_tf(acc):
    return acc.get("provider") == "tf"


def creds(acc):
    s = f"Email: <code>{esc(acc['address'])}</code>"
    if acc.get("password"):
        s += f"\nPassword: <code>{esc(acc['password'])}</code>"
    return s


async def send(ctx, uid, text, kb=None):
    await ctx.bot.send_message(
        uid,
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
        link_preview_options=NO_PREVIEW,
    )


async def send_parts(ctx, uid, parts, kb=None):
    for i, p in enumerate(parts):
        await send(ctx, uid, p, kb if i == len(parts) - 1 else None)
