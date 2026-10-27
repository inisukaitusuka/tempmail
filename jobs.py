"""Tugas latar belakang: cek pesan baru di semua email lalu kirim ke Telegram."""

import asyncio

from telegram.error import Forbidden

from client import AccountGone, RateLimited, delete_remote, get_message, list_messages
from config import CHECK_INTERVAL, log
from render import message_parts
from state import drop_account, save, users
from utils import esc, is_tf, send, send_parts


async def poller(app):
    await asyncio.sleep(5)
    while True:
        for key, rec in list(users.items()):
            for acc in list(rec["accounts"]):
                try:
                    msgs = await list_messages(acc)
                    if users.get(key) is not rec or acc not in rec["accounts"]:
                        continue  # email dihapus saat kita menunggu
                    seen = acc.setdefault("seen", [])
                    new = [m for m in reversed(msgs) if m["id"] not in seen]
                    blocked = False
                    for m in new:
                        seen.append(m["id"])
                        try:
                            # temp.tf sudah mengirim isi pesan lengkap saat cek inbox
                            full = m if is_tf(acc) else (await get_message(acc, m["id"]) or m)
                            await send_parts(
                                app,
                                int(key),
                                message_parts(
                                    full,
                                    prefix=f"📬 <b>Pesan baru</b> di <code>{esc(acc['address'])}</code>\n\n",
                                ),
                            )
                        except Forbidden:
                            blocked = True
                            break
                        except Exception:
                            log.warning("Gagal kirim notifikasi", exc_info=True)
                    if new:
                        acc["seen"] = seen[-200:]
                        save()
                    if blocked:
                        log.info("User %s memblokir bot, datanya dihapus", key)
                        users.pop(key, None)
                        save()
                        for a in rec["accounts"]:
                            await delete_remote(a)
                        break
                except AccountGone:
                    drop_account(rec, acc)
                    try:
                        await send(
                            app,
                            int(key),
                            f"⚠️ Email <code>{esc(acc['address'])}</code> sudah tidak aktif dan "
                            "dibuang dari daftar.",
                        )
                    except Exception:
                        pass
                except RateLimited as e:
                    log.warning("Kena batas permintaan, menunggu %s detik", e.wait)
                    await asyncio.sleep(min(e.wait, 120))
                except Exception:
                    log.warning("Cek inbox gagal untuk user %s", key, exc_info=True)
                await asyncio.sleep(1)  # jeda kecil supaya tidak kena rate limit
        await asyncio.sleep(CHECK_INTERVAL)
