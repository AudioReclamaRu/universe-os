# -*- coding: utf-8 -*-
"""Собирает браузерную версию app.py: исходник UNIVERSE_2.0.py + web-патч.

    python build.py          # из папки build/
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "UNIVERSE_2.0.py")
PATCH = os.path.join(HERE, "web_patch.py")
OUT = os.path.join(os.path.dirname(HERE), "app.py")

src = io.open(SRC, encoding="utf-8").read()

marker = "# ТОЧКА ВХОДА"
idx = src.index(marker)
head = src[:idx].rstrip()
head = head[:head.rfind("# ═")].rstrip() + "\n"

patch = io.open(PATCH, encoding="utf-8").read()

banner = (
    "\n\n# ══════════════════════════════════════════════════════════════════════════\n"
    "#  Ниже — автоматически добавлено сборкой для веба (build/build.py).\n"
    "#  Оригинальный файл UNIVERSE_2.0.py не изменялся.\n"
    "# ══════════════════════════════════════════════════════════════════════════\n"
)

io.open(OUT, "w", encoding="utf-8", newline="\n").write(head + banner + patch)
print("written", OUT, os.path.getsize(OUT), "bytes")
