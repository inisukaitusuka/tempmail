"""Tombol inline yang tampilannya tetap (yang berubah-ubah dibuat langsung di actions.py)."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📧 Email Baru", callback_data="new"),
                InlineKeyboardButton("📥 Inbox", callback_data="inbox"),
            ],
            [
                InlineKeyboardButton("📋 Email Saya", callback_data="me"),
                InlineKeyboardButton("🗑 Hapus Email", callback_data="del"),
            ],
        ]
    )


def new_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📧 mail.tm (domain acak)", callback_data="newmt")],
            [
                InlineKeyboardButton("📨 Gmail", callback_data="newtf:gmail"),
                InlineKeyboardButton("📨 Outlook", callback_data="newtf:outlook"),
            ],
            [InlineKeyboardButton("📨 Hotmail", callback_data="newtf:hotmail")],
        ]
    )
