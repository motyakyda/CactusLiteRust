"""Image loading for icons and mod avatars, with Pillow used when available."""

import base64
import io
import tkinter as tk

from cactus_lite.core.net import get_bytes
from cactus_lite.core.paths import MOD_ICONS_PATH
from cactus_lite.core.storage import read_json

ICON_SIZE = 44


def _load_icons():
    data = read_json(MOD_ICONS_PATH, default={})
    return data if isinstance(data, dict) else {}


class ImageCache:
    """Keeps PhotoImage references alive — Tk drops unreferenced images."""

    def __init__(self):
        self._refs = []
        self._icons = _load_icons()
        self._by_url = {}

    def keep(self, photo):
        self._refs.append(photo)
        return photo

    def clear(self):
        self._refs.clear()

    def _from_bytes(self, raw, size=ICON_SIZE):
        try:
            from PIL import Image, ImageTk
            img = Image.open(io.BytesIO(raw)).convert("RGBA").resize((size, size), Image.LANCZOS)
            return self.keep(ImageTk.PhotoImage(img))
        except Exception:
            pass
        try:
            return self.keep(tk.PhotoImage(data=base64.b64encode(raw)))
        except Exception:
            return None

    def mod_icon(self, icon_key, size=ICON_SIZE):
        b64 = self._icons.get(icon_key or "")
        if not b64:
            return None
        try:
            raw = base64.b64decode(b64)
        except Exception:
            return None
        return self._from_bytes(raw, size)

    def remote_icon(self, url, size=ICON_SIZE):
        if not url:
            return None
        if url in self._by_url:
            return self._by_url[url]
        try:
            raw = get_bytes(url, timeout=6)
        except Exception:
            return None
        photo = self._from_bytes(raw, size)
        self._by_url[url] = photo
        return photo


def app_icon(path):
    try:
        return tk.PhotoImage(file=path)
    except Exception:
        return None
