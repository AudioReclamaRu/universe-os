#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сохраняет статический кадр исходной графической модели UNIVERSE OS 2.0.

Пример:
  python inspect_universe.py --frames 1 --output universe_os_preview.png

Скрипт импортирует исходный build/UNIVERSE_2.0.py, выполняет указанное
число штатных кадров UniverseOS.update(), сохраняет исходную 6-панельную
Matplotlib-фигуру и печатает структурную сводку графа.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "build" / "UNIVERSE_2.0.py"


def load_model(path: Path):
    spec = importlib.util.spec_from_file_location("universe_os_model", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Не удалось подготовить импорт модели: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=1,
                        help="сколько штатных кадров обновить перед снимком")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "universe_os_preview.png",
                        help="путь для PNG-снимка")
    args = parser.parse_args()

    if args.frames < 1:
        parser.error("--frames должен быть не меньше 1")
    if not MODEL.is_file():
        print(f"Не найден файл модели: {MODEL}", file=sys.stderr)
        return 2

    try:
        import matplotlib
        matplotlib.use("Agg")
        import numpy as np
    except ImportError as exc:
        print("Установите зависимости: python -m pip install -r requirements.txt",
              file=sys.stderr)
        print(f"Подробности: {exc}", file=sys.stderr)
        return 2

    model = load_model(MODEL)
    app = model.UniverseOS()
    for frame in range(args.frames):
        app.update(frame)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    app.fig.savefig(args.output, dpi=120, bbox_inches="tight",
                    facecolor=app.fig.get_facecolor())

    projector = app.projector
    xyz, _ = projector.project(app.engine.t, app.engine.psi, app.engine.stress)
    degrees = np.zeros(projector.n, dtype=int)
    for left, right in projector.edges:
        degrees[left] += 1
        degrees[right] += 1

    radii = np.linalg.norm(xyz, axis=1)
    print("UNIVERSE OS 2.0 — графическая диагностика")
    print(f"Модель: {MODEL}")
    print(f"Сохранено: {args.output.resolve()}")
    print(f"Узлы: {projector.n}")
    print(f"Неориентированные рёбра: {len(projector.edges)}")
    print(f"Степень узлов: min={degrees.min()}, max={degrees.max()}")
    print(f"Диапазон радиусов 3D-проекции: {radii.min():.6f} .. {radii.max():.6f}")
    print(f"Кадры: {args.frames}; шаг модели t={app.engine.t:.6f}")
    print(f"Фазовый дефект Ψ={app.engine.psi:.8f}; сбросов={app.engine.collapses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
