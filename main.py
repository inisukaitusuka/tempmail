#!/usr/bin/env python3
"""
Bot Telegram TempMail (mail.tm + temp.tf)

Jenis email:
  mail.tm  -> domain acak, bisa pilih username & password sendiri
  temp.tf  -> alias Gmail / Outlook / Hotmail (hanya menerima pesan, tanpa password)

Perintah:
  /new               -> pilih jenis email yang mau dibuat
  /new nama          -> mail.tm dengan username sendiri
  /new nama pass     -> mail.tm dengan username & password sendiri
  /gmail             -> alias Gmail dari temp.tf
  /outlook           -> alias Outlook dari temp.tf
  /hotmail           -> alias Hotmail dari temp.tf
  /me                -> daftar semua email kamu, tap untuk ganti email aktif
  /inbox             -> pesan masuk di email yang aktif (tap untuk baca)
  /delete            -> hapus email yang aktif
  + Pesan baru di SEMUA emailmu otomatis dikirim ke Telegram (dicek tiap 15 detik)

Email lama tidak dihapus saat kamu membuat email baru, jadi bisa dipilih lagi.

Cara pakai: taruh BOT_TOKEN (dari @BotFather) di file .env (lihat .env.example),
lalu jalankan:
    python main.py
Detail lengkap ada di README.md.
"""

import asyncio

from telegram import BotCommand
from telegram.ext import Application

import client
import state
from config import BOT_TOKEN, log
from handlers import register
from jobs import poller


async def post_init(app: Application):
    await client.start_http()
    await app.bot.set_my_commands(
        [
            BotCommand("new", "Buat email baru (pilih jenis)"),
            BotCommand("gmail", "Buat alias Gmail (temp.tf)"),
            BotCommand("outlook", "Buat alias Outlook (temp.tf)"),
            BotCommand("hotmail", "Buat alias Hotmail (temp.tf)"),
            BotCommand("me", "Daftar email & ganti email aktif"),
            BotCommand("inbox", "Lihat pesan masuk"),
            BotCommand("delete", "Hapus email aktif"),
        ]
    )
    app.bot_data["poller"] = asyncio.create_task(poller(app))


async def post_shutdown(app: Application):
    task = app.bot_data.get("poller")
    if task:
        task.cancel()
    await client.close_http()


def main():
    if BOT_TOKEN == "ISI_TOKEN_BOT_DISINI":
        raise SystemExit(
            "BOT_TOKEN belum diisi. Salin .env.example menjadi .env, lalu isi BOT_TOKEN "
            "dengan token dari @BotFather."
        )
    state.load()
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    register(app)
    log.info("Bot jalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
