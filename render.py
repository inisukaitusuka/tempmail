"""Ubah isi email (HTML/teks) jadi pesan Telegram (HTML) yang rapi."""

import html
import re

from utils import esc

# Penanda sementara untuk link saat mengubah HTML email jadi teks
OPEN, MID, CLOSE = "", "", ""
MARK_RE = re.compile(OPEN + r"(\d+)" + MID + r"(.*?)" + CLOSE, re.S)
URL_RE = re.compile(r"https?://[^\s<>\"]+")
CHUNK = 3300  # maks. karakter terlihat per pesan Telegram (batasnya 4096)
MAX_PARTS = 3  # kalau email lebih panjang dari ini, sisanya dipotong


def link_label(url):
    """Teks pendek untuk link panjang, misal 'claude.ai/…'."""
    if len(url) <= 40:
        return url
    host = re.match(r"https?://([^/?#]+)", url)
    return (host.group(1) if host else "link") + "/…"


def a_tag(url, label):
    u = url.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return f'<a href="{u}">{esc(label)}</a>'


def linkify(text):
    """Escape teks + ubah URL telanjang jadi link bertulisan pendek (tetap bisa di-tap)."""
    out, pos = [], 0
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?)]}'\"")
        out.append(esc(text[pos : m.start()]))
        out.append(a_tag(url, link_label(url)))
        pos = m.start() + len(url)
    out.append(esc(text[pos:]))
    return "".join(out)


def html_to_marked(h, links):
    """HTML email -> teks biasa; link dibungkus penanda supaya bisa dibuat link pendek."""
    h = re.sub(r"(?is)<(script|style|head)\b[^>]*>.*?</\1>", "", h)

    def anchor(mt):
        url = html.unescape(mt.group(1)).strip()
        inner = re.sub(r"<[^>]+>", "", mt.group(2))
        if not re.match(r"https?://", url, re.I):
            return inner
        links.append(url)
        return f"{OPEN}{len(links) - 1}{MID}{inner}{CLOSE}"

    h = re.sub(r"""(?is)<a\s[^>]*?href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""", anchor, h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>|</li>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    return html.unescape(h)


def clean_text(t):
    t = t.replace("\r", "")
    t = re.sub(r"[ \t ]+", " ", t)
    t = re.sub(r" ?\n ?", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def split_marked(text, limit):
    """Pecah teks panjang jadi beberapa bagian, di batas baris dan tidak memotong link."""
    chunks = []
    while len(text) > limit:
        cut = -1
        for m in re.finditer(r"\n", text[:limit]):
            seg = text[: m.start()]
            if seg.count(OPEN) == seg.count(CLOSE):
                cut = m.start()
        if cut < limit // 3:  # tidak ada batas baris yang layak
            cut = limit
            seg = text[:cut]
            if seg.count(OPEN) != seg.count(CLOSE):
                back = text.rfind(OPEN, 0, cut)
                if back > 0:
                    cut = back
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    chunks.append(text)
    return [c for c in chunks if c]


def render_marked(text, links):
    out, pos = [], 0
    for m in MARK_RE.finditer(text):
        out.append(linkify(text[pos : m.start()]))
        url = links[int(m.group(1))]
        label = " ".join(m.group(2).split())
        if label:  # link tanpa tulisan (gambar/logo/pelacak) dibuang saja
            if re.match(r"https?://", label):
                label = link_label(url)
            out.append(a_tag(url, label))
        pos = m.end()
    out.append(linkify(text[pos:]))
    return re.sub("[-]", "", "".join(out))


def body_chunks(m):
    """Isi pesan -> daftar bagian HTML siap kirim (link panjang disingkat, tetap bisa di-tap)."""
    links = []
    text = (m.get("text") or "").strip()
    if not text:
        h = m.get("html") or ""
        if isinstance(h, list):
            h = "\n".join(h)
        text = html_to_marked(h, links)
    text = clean_text(text)
    if not text:
        return ["(isi pesan kosong)"]
    parts = split_marked(text, CHUNK)
    cut = len(parts) > MAX_PARTS
    rendered = [render_marked(p, links) for p in parts[:MAX_PARTS]]
    if cut:
        rendered[-1] += "\n\n…(email terlalu panjang, sisanya dipotong)"
    return rendered


def message_parts(m, prefix=""):
    sender = m.get("from") or {}
    frm = sender.get("address", "?")
    if sender.get("name"):
        frm = f"{sender['name']} <{frm}>"
    subject = (m.get("subject") or "(tanpa subjek)")[:200]
    chunks = body_chunks(m)
    if m.get("hasAttachments"):
        chunks[-1] += "\n\n📎 Pesan ini punya lampiran (belum didukung bot)."
    parts = [f"{prefix}📨 <b>{esc(subject)}</b>\nDari: {esc(frm)}\n\n{chunks[0]}"]
    for i, c in enumerate(chunks[1:], start=2):
        parts.append(f"<i>…lanjutan ({i}/{len(chunks)})</i>\n\n{c}")
    return parts
