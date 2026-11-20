#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Корневая точка запуска UNIVERSE OS 2.0 (нативный Python)."""

from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "build" / "UNIVERSE_2.0.py"


def main() -> int:
    if not MODEL.is_file():
        print(f"Не найден файл модели: {MODEL}", file=sys.stderr)
        return 2

    try:
        import numpy  # noqa: F401
        import matplotlib  # noqa: F401
    except ImportError as exc:
        print(
            "Не установлены зависимости. Выполните:\n"
            "  python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        print(f"Подробности: {exc}", file=sys.stderr)
        return 2

    print(f"Запуск модели: {MODEL}")
    # Запускаем существующую точку входа оригинального файла без его изменения.
    runpy.run_path(str(MODEL), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
