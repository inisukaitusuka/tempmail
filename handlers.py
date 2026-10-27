"""Handler perintah (/start, /new, ...) dan tombol inline."""

import re

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, filters

from actions import (
    do_delete,
    do_delete_confirm,
    do_inbox,
    do_me,
    do_new,
    do_new_menu,
    do_new_tf,
    do_read,
    do_use,
)
from config import TF_PRESETS, log
from keyboards import main_menu
from texts import START
from utils import send


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START, reply_markup=main_menu())


async def cmd_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not ctx.args:
        await do_new_menu(ctx, uid)
        return
    username = ctx.args[0].lower()
    if not re.fullmatch(r"[a-z0-9._-]{3,30}", username):
        await update.message.reply_text(
            "Username harus 3-30 karakter: huruf kecil, angka, titik, strip, atau underscore."
        )
        return
    password = None
    if len(ctx.args) >= 2:
        password = ctx.args[1]
        if not 6 <= len(password) <= 64:
            await update.message.reply_text("Password harus 6-64 karakter, tanpa spasi.")
            return
    await do_new(ctx, uid, username, password)


def tf_command(kind):
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await do_new_tf(ctx, update.effective_user.id, kind)

    return handler


async def cmd_inbox(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await do_inbox(ctx, update.effective_user.id)


async def cmd_me(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await do_me(ctx, update.effective_user.id)


async def cmd_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await do_delete_confirm(ctx, update.effective_user.id)


async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data or ""
    try:
        if data == "new":
            await do_new_menu(ctx, uid)
        elif data == "newmt":
            await do_new(ctx, uid)
        elif data.startswith("newtf:"):
            await do_new_tf(ctx, uid, data[6:])
        elif data == "inbox":
            await do_inbox(ctx, uid)
        elif data == "me":
            await do_me(ctx, uid)
        elif data == "del":
            await do_delete_confirm(ctx, uid)
        elif data == "delyes":
            await do_delete(ctx, uid)
        elif data.startswith("use:"):
            await do_use(ctx, uid, data[4:])
        elif data.startswith("read:"):
            await do_read(ctx, uid, data[5:])
    except Exception:
        log.exception("Error saat memproses tombol %s", data)
        await send(ctx, uid, "⚠️ Terjadi error di bot, coba lagi. Kalau terus begini, cek log di server.")


def register(app):
    """Daftarkan semua handler ke aplikasi bot."""
    private = filters.ChatType.PRIVATE
    app.add_handler(CommandHandler("start", cmd_start, filters=private))
    app.add_handler(CommandHandler("new", cmd_new, filters=private))
    for kind in TF_PRESETS:
        app.add_handler(CommandHandler(kind, tf_command(kind), filters=private))
    app.add_handler(CommandHandler("inbox", cmd_inbox, filters=private))
    app.add_handler(CommandHandler("me", cmd_me, filters=private))
    app.add_handler(CommandHandler("delete", cmd_delete, filters=private))
    app.add_handler(CallbackQueryHandler(on_button))
