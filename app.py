# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          ASTRAEA UNIVERSE OS — ТОРВ/ТабАк Full Simulation Engine            ║
║          Теория Октонионного Резонанса Вакуума  |  v11.0                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Единственный свободный параметр:  p = 3¹² / 2¹⁹  (Пифагорова комма)      ║
║  Всё остальное — геометрическое следствие.                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Архитектура:
  ┌─ TorvEngine       — физическое ядро, фазовый дефект, стресс, коллапсы
  ├─ CayleyProjector  — 4D→3D стереографическая проекция графа Кэли
  ├─ MassMatrix       — матрица квантования масс по 7 октавам
  ├─ PhaseMonitor     — мониторинг Ψ, α, ΩΛ, ΩDM в реальном времени
  └─ UniverseOS       — оркестратор, анимация, интерфейс
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import matplotlib.patches as mpatches
from collections import deque
import time, math

# ══════════════════════════════════════════════════════════════════════════════
# 1.  ФУНДАМЕНТАЛЬНЫЕ КОНСТАНТЫ ТОРВ
# ══════════════════════════════════════════════════════════════════════════════

# Пифагорова комма — единственный свободный параметр
P_NUM   = 531_441          # 3¹²
P_DEN   = 524_288          # 2¹⁹
P       = P_NUM / P_DEN    # ≈ 1.013 643
THETA   = math.log(P)      # фазовый дефект  ≈ 0.013 551

# Икосаэдрическая среда H₃
N       = 128              # 2⁷ — мощность пространства состояний
M_MU    = THETA / N        # базовый квант инерции

# Топологические инварианты
GATE_42 = 42               # I(k=2) = 10·4+2 — вторая оболочка икосаэдра
GATE_85 = 85               # 2·42+1 — первая стоячая мода

# Космологические предсказания (из p)
OMEGA_L  = 1 - (1/P)**85   # тёмная энергия  ≈ 0.6840
OMEGA_DM = P**125          # соотношение ΩDM/ΩB ≈ 5.441
ALPHA_INV = N * P**5       # α⁻¹             ≈ 137.036

# Золотое сечение (оператор шага)
PHI     = (1.0 + math.sqrt(5.0)) / 2.0

# π из 128 мод (дискретный ряд Лейбница)
PI_128  = 4.0 * sum((-1)**k / (2*k+1) for k in range(128))

# Масштаб для физических масс
K_SCALE = 6.81e-25         # кг/с.е.и.
M_0     = M_MU * K_SCALE   # базовый квант [кг]

# Химические якоря — материальные маркеры инвариантов
ANCHORS = {
    "H":  {"Z":  1, "E":3, "color":"#2ecc71", "label":"H  proto-hub",     "marker":"o"},
    "Fe": {"Z": 26, "E":4, "color":"#3498db", "label":"Fe macro-stable",  "marker":"o"},
    "Au": {"Z": 79, "E":6, "color":"#ffd700", "label":"Au stable mirror", "marker":"*"},
    "Hg": {"Z": 80, "E":6, "color":"#00ffff", "label":"Hg volatile",      "marker":"X"},
    "Og": {"Z":118, "E":7, "color":"#e74c3c", "label":"Og collapse",      "marker":"D"},
}

OCTAVES = {
    1: {"name":"Planck Vacuum",      "n":1,   "color":"#7f8c8d"},
    2: {"name":"Quark Matrix",       "n":7,   "color":"#9b59b6"},
    3: {"name":"Proton Hub",         "n":8,   "color":"#2ecc71"},
    4: {"name":"SO(8) Iron Core",    "n":28,  "color":"#3498db"},
    5: {"name":"Gate 42 / Organic",  "n":42,  "color":"#e67e22"},
    6: {"name":"White Dwarf",        "n":64,  "color":"#f1c40f"},
    7: {"name":"Neutron Star",       "n":128, "color":"#e74c3c"},
}


# ══════════════════════════════════════════════════════════════════════════════
# 2.  TORV ENGINE — физическое ядро
# ══════════════════════════════════════════════════════════════════════════════

class TorvEngine:
    """
    Вычисляет эволюцию фазового дефекта Ψ по итерациям.
    Топологический стресс накапливается до порога коллапса,
    затем сбрасывается — аналог землетрясения или флуктуации вакуума.
    """
    COLLAPSE_THRESHOLD = P      # Ψ > P → фазовое вырождение

    def __init__(self, n_nodes=N):
        self.n = n_nodes
        self.t = 0
        self.psi      = 0.0     # текущий фазовый дефект
        self.stress   = np.zeros(n_nodes)   # стресс по узлам
        self.energy   = 0.0
        self.collapses = 0      # счётчик топологических сбросов
        self.history_psi    = deque(maxlen=300)
        self.history_energy = deque(maxlen=300)
        self.collapse_times = []

    def step(self, dt: float = 1.0) -> dict:
        self.t += dt

        # Накопление фазового дефекта (логарифмическое нарастание)
        self.psi += THETA * dt * (1.0 + 0.15 * math.sin(self.t * 2 * PI_128 / 85))

        # Узловой стресс — Пифагорово поле напряжения
        idx = np.arange(self.n)
        d42 = np.abs(idx - GATE_42) / self.n
        d85 = np.abs(idx - GATE_85) / self.n
        gate_field = np.exp(-np.minimum(d42, d85) * 8.0)
        phase_wave = np.sin(self.t * THETA + idx * PI_128 / 32) * 0.5 + 0.5
        self.stress = gate_field * phase_wave * self.psi

        # Полная энергия системы
        self.energy = float(np.sum(self.stress ** 2) * M_MU)

        # Топологический коллапс (сброс)
        collapsed = False
        if self.psi > self.COLLAPSE_THRESHOLD:
            self.psi    = self.psi * THETA  # сброс с остатком (не ноль — среда помнит)
            self.stress *= THETA
            self.collapses += 1
            self.collapse_times.append(self.t)
            collapsed = True

        self.history_psi.append(self.psi)
        self.history_energy.append(self.energy)

        return {
            "t":        self.t,
            "psi":      self.psi,
            "stress":   self.stress.copy(),
            "energy":   self.energy,
            "collapsed": collapsed,
            "collapses": self.collapses,
        }

    def reset(self):
        self.__init__(self.n)


# ══════════════════════════════════════════════════════════════════════════════
# 3.  CAYLEY PROJECTOR — 4D → 3D стереографическая проекция
# ══════════════════════════════════════════════════════════════════════════════

class CayleyProjector:
    """
    Граф Кэли на 128 узлах с XOR-топологией (14 рёбер на узел).
    W-координата кодирует фазовый дефект Ψ.
    """
    def __init__(self, n=N):
        self.n    = n
        self.bits = [1, 2, 4, 8, 16, 32, 64]   # 7 бит → 7 октав

        # Предвычисляем рёбра
        self.edges = []
        for i in range(n):
            for b in self.bits:
                j = i ^ b
                if j < n and j > i:
                    self.edges.append((i, j))

    def project(self, t: float, psi: float, stress: np.ndarray) -> tuple:
        """
        Возвращает (xyz [n,3], edge_stresses [m]).
        W = sin(zw) * Ψ * θ → фазовый сдвиг модулирует глубину.
        """
        ang_xy = (np.arange(self.n) * PI_128 / 32) + t * 0.018
        ang_zw = (np.arange(self.n) * PI_128 / 64) + t * 0.009

        x = np.cos(ang_xy) * (1 + 0.28 * np.sin(ang_zw))
        y = np.sin(ang_xy) * (1 + 0.28 * np.sin(ang_zw))
        z = np.cos(ang_zw) * PHI
        w = np.sin(ang_zw) * psi * THETA * 6   # Ψ входит в W

        # Стереографическая проекция 4D → 3D
        d = 1.0 / np.maximum(2.2 - w, 0.2)
        xyz = np.column_stack([x*d, y*d, z*d])

        # Стресс по рёбрам — среднее стрессов двух узлов
        edge_stress = np.array([
            (stress[i] + stress[j]) / 2.0
            for i, j in self.edges
        ])

        return xyz, edge_stress


# ══════════════════════════════════════════════════════════════════════════════
# 4.  MASS MATRIX
# ══════════════════════════════════════════════════════════════════════════════

def tabak_mass_kg(n: int, E: int) -> float:
    """M = m₀ · n · 2^(E-1)  [10⁻²⁷ кг]"""
    return M_0 * n * (2**(E-1)) * 1e27


OCTAVE_MASSES = {
    E: tabak_mass_kg(OCTAVES[E]["n"], E) for E in OCTAVES
}

# Экспериментальные значения для сравнения
REFERENCE = {
    "proton_kg":   1.6726e-27,
    "electron_kg": 9.1094e-31,
    "alpha_inv":   137.035999084,
    "omega_L":     0.6847,
    "omega_dm_ob": 5.36,
}


# ══════════════════════════════════════════════════════════════════════════════
# 5.  UNIVERSE OS — главный класс
# ══════════════════════════════════════════════════════════════════════════════

class UniverseOS:
    """
    Оркестратор. Управляет всеми подсистемами.
    Макет: 4 панели + 2 слайдера + кнопка Reset.
    """

    # цвета интерфейса
    BG      = "#020208"
    BG2     = "#03030f"
    GRID    = "#0a1020"
    TEXT    = "#c8d8f0"
    ACCENT  = "#00ffcc"
    WARN    = "#ff6b35"
    CRIT    = "#ff0055"
    GOLD    = "#ffd700"
    CYAN    = "#00e5ff"

    def __init__(self):
        self.engine    = TorvEngine()
        self.projector = CayleyProjector()
        self.paused    = False
        self.frame     = 0
        self.speed     = 1.0    # слайдер скорости
        self.threshold = P      # слайдер порога коллапса

        # История для фазового монитора
        self.psi_trace    = deque(maxlen=250)
        self.energy_trace = deque(maxlen=250)
        self.collapse_markers = []

        self._build_layout()

    # ── Построение интерфейса ─────────────────────────────────────────────────

    def _build_layout(self):
        plt.rcParams.update({
            "font.family":  "monospace",
            "axes.facecolor": self.BG2,
            "axes.edgecolor": self.GRID,
            "axes.labelcolor": self.TEXT,
            "xtick.color": self.TEXT,
            "ytick.color": self.TEXT,
            "grid.color": self.GRID,
            "grid.alpha": 0.5,
            "figure.facecolor": self.BG,
        })

        self.fig = plt.figure(figsize=(22, 12), facecolor=self.BG)
        self.fig.canvas.manager.set_window_title("UNIVERSE OS — ТОРВ/ТабАк v11.0")

        gs = gridspec.GridSpec(3, 4, figure=self.fig,
                               left=0.04, right=0.98,
                               top=0.93, bottom=0.12,
                               wspace=0.35, hspace=0.45)

        # ── P1: Граф Кэли 3D ─────────────────────────────────────────────────
        self.ax_cayley = self.fig.add_subplot(gs[0:2, 0:2], projection="3d",
                                               facecolor=self.BG)
        self.ax_cayley.set_facecolor(self.BG)

        # ── P2: Матрица масс 7 октав ─────────────────────────────────────────
        self.ax_mass = self.fig.add_subplot(gs[0, 2:4])
        self.ax_mass.set_yscale("log")

        # ── P3: Фазовый монитор Ψ(t) ─────────────────────────────────────────
        self.ax_psi = self.fig.add_subplot(gs[1, 2])

        # ── P4: Узловой стресс σ(Z) ──────────────────────────────────────────
        self.ax_stress = self.fig.add_subplot(gs[1, 3])

        # ── P5: Энергия E(t) ─────────────────────────────────────────────────
        self.ax_energy = self.fig.add_subplot(gs[2, 2:4])

        # ── P6: Панель констант ───────────────────────────────────────────────
        self.ax_info = self.fig.add_subplot(gs[2, 0:2])
        self.ax_info.set_axis_off()

        # ── Заголовок ─────────────────────────────────────────────────────────
        self.fig.text(0.5, 0.975,
            "UNIVERSE OS  ·  ТОРВ / ТабАк  ·  p = 531441/524288  ·  θ = ln(p)",
            ha="center", va="top", fontsize=13, color=self.ACCENT, fontweight="bold")

        # ── Слайдеры ──────────────────────────────────────────────────────────
        ax_spd = self.fig.add_axes([0.07, 0.04, 0.18, 0.025], facecolor=self.BG2)
        self.sl_speed = Slider(ax_spd, "Speed", 0.1, 5.0, valinit=1.0,
                               color=self.ACCENT, handle_style={"facecolor":self.GOLD})
        self.sl_speed.label.set_color(self.TEXT)
        self.sl_speed.valtext.set_color(self.ACCENT)

        ax_thr = self.fig.add_axes([0.30, 0.04, 0.18, 0.025], facecolor=self.BG2)
        self.sl_thr = Slider(ax_thr, "Ψ threshold", 0.5, 2.5, valinit=P,
                             color=self.WARN, handle_style={"facecolor":self.CRIT})
        self.sl_thr.label.set_color(self.TEXT)
        self.sl_thr.valtext.set_color(self.WARN)

        # ── Кнопки ────────────────────────────────────────────────────────────
        ax_reset = self.fig.add_axes([0.52, 0.035, 0.07, 0.04], facecolor="#1a0a0a")
        self.btn_reset = Button(ax_reset, "RESET", color="#1a0a0a", hovercolor="#330000")
        self.btn_reset.label.set_color(self.CRIT)
        self.btn_reset.on_clicked(self._on_reset)

        ax_pause = self.fig.add_axes([0.61, 0.035, 0.07, 0.04], facecolor="#0a1a0a")
        self.btn_pause = Button(ax_pause, "PAUSE", color="#0a1a0a", hovercolor="#003300")
        self.btn_pause.label.set_color(self.ACCENT)
        self.btn_pause.on_clicked(self._on_pause)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_reset(self, _):
        self.engine.reset()
        self.psi_trace.clear()
        self.energy_trace.clear()
        self.collapse_markers.clear()
        self.frame = 0

    def _on_pause(self, _):
        self.paused = not self.paused
        self.btn_pause.label.set_text("RESUME" if self.paused else "PAUSE")

    # ── Главный кадр ──────────────────────────────────────────────────────────

    def update(self, frame_num: int):
        if self.paused:
            return

        self.frame += 1
        speed     = self.sl_speed.val
        self.engine.COLLAPSE_THRESHOLD = self.sl_thr.val

        # Несколько шагов за кадр (speed)
        state = None
        for _ in range(max(1, int(speed))):
            state = self.engine.step(dt=speed / max(1, int(speed)))

        psi      = state["psi"]
        stress   = state["stress"]
        energy   = state["energy"]
        collapsed= state["collapsed"]

        self.psi_trace.append(psi)
        self.energy_trace.append(energy)
        if collapsed:
            self.collapse_markers.append(len(self.psi_trace) - 1)

        t_anim = self.engine.t

        # ── Граф Кэли ─────────────────────────────────────────────────────────
        xyz, edge_stress = self.projector.project(t_anim, psi, stress)
        self._draw_cayley(xyz, edge_stress, stress, psi, collapsed)

        # ── Матрица масс ──────────────────────────────────────────────────────
        self._draw_mass(psi)

        # ── Фазовый монитор ───────────────────────────────────────────────────
        self._draw_psi(psi)

        # ── Узловой стресс ────────────────────────────────────────────────────
        self._draw_stress(stress, psi)

        # ── Энергия ───────────────────────────────────────────────────────────
        self._draw_energy()

        # ── Панель констант ───────────────────────────────────────────────────
        self._draw_info(psi, energy, state["collapses"])

    # ── Граф Кэли ─────────────────────────────────────────────────────────────

    def _draw_cayley(self, xyz, edge_stress, stress, psi, collapsed):
        ax = self.ax_cayley
        ax.cla()
        ax.set_axis_off()
        ax.set_facecolor(self.BG)

        n_edges   = len(self.projector.edges)
        max_stress = max(edge_stress.max(), 1e-9)

        # Окраска рёбер: золото (нисходящий) / ртуть (восходящий) + интенсивность
        segs, cols, lws = [], [], []
        for k, (i, j) in enumerate(self.projector.edges):
            segs.append([xyz[i], xyz[j]])
            rel  = edge_stress[k] / max_stress
            if i < 64:
                # Au-вектор: от тёмно-золотого до ярко-жёлтого
                r = 0.6 + 0.4 * rel
                g = 0.5 + 0.35 * rel
                b = 0.0
            else:
                # Hg-вектор: от тёмно-синего до яркого циана
                r = 0.0
                g = 0.5 + 0.5 * rel
                b = 0.6 + 0.4 * rel
            alpha = 0.05 + 0.35 * rel
            cols.append((r, g, b, alpha))
            lws.append(0.5 + 1.5 * rel)

        lc = Line3DCollection(segs, colors=cols, linewidths=lws, zorder=1)
        ax.add_collection3d(lc)

        # Узлы — размер пропорционален стрессу
        node_s = 8 + 180 * (stress / max(stress.max(), 1e-9))
        node_c = []
        thr    = self.engine.COLLAPSE_THRESHOLD
        for s in stress:
            rel = s / thr
            if rel > 0.9:
                node_c.append(self.CRIT)
            elif rel > 0.6:
                node_c.append(self.WARN)
            elif rel > 0.3:
                node_c.append("#88bbff")
            else:
                node_c.append("#1a3a6a")

        if collapsed:
            # Вспышка при коллапсе
            ax.scatter(xyz[:,0], xyz[:,1], xyz[:,2],
                       s=node_s*3, c=self.CRIT, alpha=0.5, zorder=3)
        ax.scatter(xyz[:,0], xyz[:,1], xyz[:,2],
                   s=node_s, c=node_c, alpha=0.85, edgecolors="none", zorder=4)

        # Химические якоря поверх
        for sym, a in ANCHORS.items():
            z  = a["Z"]
            if z < N:
                ax.scatter(xyz[z,0], xyz[z,1], xyz[z,2],
                           s=200, c=a["color"], marker=a["marker"],
                           edgecolors="white", linewidths=0.8, zorder=5,
                           label=f'{sym}')

        # Оси подписей
        regime = self._psi_regime(psi)
        ax.set_title(
            f"4D Cayley–Tabakov Lattice  |  Ψ={psi:.5f}  |  {regime}",
            color=self.CRIT if psi > self.engine.COLLAPSE_THRESHOLD * 0.9 else self.TEXT,
            fontsize=10, pad=8)
        ax.view_init(elev=22 + 8*math.sin(self.engine.t*0.006),
                     azim=self.engine.t * 0.35)

        legend = ax.legend(loc="lower left", fontsize=7,
                           facecolor=self.BG, edgecolor=self.GRID,
                           labelcolor=self.TEXT, framealpha=0.8,
                           markerscale=0.8)

    # ── Матрица масс ──────────────────────────────────────────────────────────

    def _draw_mass(self, psi):
        ax = self.ax_mass
        ax.cla()
        ax.set_facecolor(self.BG2)
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3, color=self.GRID)

        E_list = list(OCTAVES.keys())
        masses = [OCTAVE_MASSES[E] for E in E_list]
        colors = [OCTAVES[E]["color"] for E in E_list]

        ax.plot(E_list, masses, color="#1b2a47", lw=1.2, ls="--", alpha=0.7, zorder=1)

        for E, m, c in zip(E_list, masses, colors):
            # Пульсация Gate 42
            s = 120
            if E == 5:
                pulse = abs(math.sin(self.engine.t * 0.08)) * psi / P
                s = int(120 + 180 * pulse)
                ax.scatter(E, m, s=s, color=self.WARN, edgecolors="white",
                           lw=0.8, zorder=3, alpha=0.9)
            else:
                ax.scatter(E, m, s=s, color=c, edgecolors="white",
                           lw=0.5, zorder=2)
            ax.text(E + 0.12, m * 1.15,
                    f"{OCTAVES[E]['name']}\n{m:.3e} ×10⁻²⁷kg",
                    color=self.TEXT, fontsize=7.5, va="bottom")

        # Gate 42 threshold line (пульсирует)
        g42 = OCTAVE_MASSES[5]
        ax.axhline(g42, color=self.WARN, ls=":", alpha=0.4 * abs(math.sin(self.engine.t*0.05)),
                   lw=1)

        # Экспериментальный протон
        ax.axhline(REFERENCE["proton_kg"]*1e27, color=self.CYAN, ls="--",
                   alpha=0.4, lw=0.8, label="M_p exp")
        ax.set_xlim(0.5, 7.8)
        ax.set_xlabel("Октава E", fontsize=9)
        ax.set_ylabel("×10⁻²⁷ кг", fontsize=9)
        ax.set_title("Матрица квантования масс (7 октав ТабАк)", color=self.TEXT, fontsize=9)
        ax.tick_params(labelsize=7)

    # ── Фазовый монитор Ψ ─────────────────────────────────────────────────────

    def _draw_psi(self, psi):
        ax = self.ax_psi
        ax.cla()
        ax.set_facecolor(self.BG2)
        ax.grid(True, alpha=0.3, color=self.GRID)

        pts = list(self.psi_trace)
        if pts:
            xs = np.arange(len(pts))
            # Раскраска по уровню — ниже порога синий, выше WARN, критический красный
            thr = self.engine.COLLAPSE_THRESHOLD
            colors = []
            for v in pts:
                rel = v / thr
                if rel > 0.9:    colors.append(self.CRIT)
                elif rel > 0.65: colors.append(self.WARN)
                else:            colors.append(self.CYAN)

            # Рисуем отрезки с переменным цветом
            for k in range(len(pts)-1):
                ax.plot(xs[k:k+2], pts[k:k+2], color=colors[k], lw=1.0, alpha=0.85)

            # Маркеры коллапсов
            for cm in self.collapse_markers:
                if 0 <= cm < len(pts):
                    ax.axvline(cm, color=self.CRIT, alpha=0.6, lw=0.8, ls="--")

        # Порог
        ax.axhline(self.engine.COLLAPSE_THRESHOLD, color=self.WARN,
                   ls=":", lw=1.0, alpha=0.7)
        ax.axhline(P, color=self.GOLD, ls="--", lw=0.7, alpha=0.5, label="p")

        ax.set_title(f"Ψ(t)  collapses={self.engine.collapses}", color=self.TEXT, fontsize=9)
        ax.set_xlabel("кадры", fontsize=8); ax.set_ylabel("Ψ", fontsize=8)
        ax.tick_params(labelsize=7)

    # ── Узловой стресс ────────────────────────────────────────────────────────

    def _draw_stress(self, stress, psi):
        ax = self.ax_stress
        ax.cla()
        ax.set_facecolor(self.BG2)
        ax.grid(True, alpha=0.3, color=self.GRID)

        xs = np.arange(N)
        # Градиент от синего к красному по величине стресса
        norm = stress / max(stress.max(), 1e-9)
        colors = plt.cm.plasma(norm)

        ax.bar(xs, stress, color=colors, width=1.0, alpha=0.85, edgecolor="none")

        # Маркеры якорей
        for sym, a in ANCHORS.items():
            z = a["Z"]
            if z < N:
                ax.axvline(z, color=a["color"], ls="--", alpha=0.6, lw=0.8)
                ax.text(z, stress[z]*1.05, sym, color=a["color"],
                        fontsize=7, ha="center")

        # Gate 42 и Gate 85
        ax.axvline(GATE_42, color=self.WARN, ls=":", lw=1.2, alpha=0.8)
        ax.axvline(GATE_85, color=self.WARN, ls=":", lw=1.2, alpha=0.8)

        ax.set_title("Узловой стресс σ(Z)", color=self.TEXT, fontsize=9)
        ax.set_xlabel("Z (узел)", fontsize=8); ax.set_ylabel("σ", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_xlim(0, N)

    # ── Энергия ───────────────────────────────────────────────────────────────

    def _draw_energy(self):
        ax = self.ax_energy
        ax.cla()
        ax.set_facecolor(self.BG2)
        ax.grid(True, alpha=0.3, color=self.GRID)

        pts = list(self.energy_trace)
        if pts:
            xs = np.arange(len(pts))
            ax.fill_between(xs, pts, alpha=0.25, color=self.GOLD)
            ax.plot(xs, pts, color=self.GOLD, lw=1.2)

            # Коллапсы
            for cm in self.collapse_markers:
                if 0 <= cm < len(pts):
                    ax.axvline(cm, color=self.CRIT, alpha=0.5, lw=0.8)

        ax.set_title("Энергия вакуума E(t)", color=self.TEXT, fontsize=9)
        ax.set_xlabel("кадры", fontsize=8); ax.set_ylabel("E [с.е.и.]", fontsize=8)
        ax.tick_params(labelsize=7)

    # ── Панель констант ───────────────────────────────────────────────────────

    def _draw_info(self, psi, energy, collapses):
        ax = self.ax_info
        ax.cla()
        ax.set_axis_off()
        ax.set_facecolor(self.BG)

        # Предсказания vs эксперимент
        lines = [
            ("═══ ТОРВ: константы из p ═══════════════════════", self.ACCENT, 12, True),
            (f"p  = {P:.8f}  (3¹²/2¹⁹)",                       self.GOLD,   9,  False),
            (f"θ  = {THETA:.8f}  (ln p)",                        self.GOLD,   9,  False),
            ("", self.TEXT, 8, False),
            ("═══ Предсказание  vs  Эксперимент ══════════════", self.CYAN, 9, True),
            (f"α⁻¹  = {ALPHA_INV:.5f}  |  ref {REFERENCE['alpha_inv']:.5f}  "
             f"Δ {abs(ALPHA_INV-REFERENCE['alpha_inv']):.4f}",   self.TEXT,   8,  False),
            (f"ΩΛ   = {OMEGA_L:.5f}  |  ref {REFERENCE['omega_L']:.4f}  "
             f"Δ {abs(OMEGA_L-REFERENCE['omega_L']):.4f}",       self.TEXT,   8,  False),
            (f"ΩDM/ΩB = {OMEGA_DM:.3f}  |  ref {REFERENCE['omega_dm_ob']:.3f}  "
             f"Δ {abs(OMEGA_DM-REFERENCE['omega_dm_ob']):.3f}",  self.TEXT,   8,  False),
            ("", self.TEXT, 8, False),
            ("═══ Текущее состояние ТОРВ ═════════════════════", self.WARN, 9, True),
            (f"Ψ(t)  = {psi:.6f}   (порог {self.engine.COLLAPSE_THRESHOLD:.5f})",
                                                                  self.WARN,   9,  False),
            (f"E(t)  = {energy:.4e} с.е.и.",                     self.TEXT,   8,  False),
            (f"Коллапсов: {collapses}   t={self.engine.t:.1f}",  self.CRIT if collapses>0 else self.TEXT, 9, False),
            (f"Режим: {self._psi_regime(psi)}",                  self._regime_color(psi), 9, True),
            ("", self.TEXT, 8, False),
            ("═══ Якоря ═══════════════════════════════════════", "#5577aa", 9, True),
            (f"Gate-42  I(k=2)=10·4+2   Z=42",                  self.WARN,   8,  False),
            (f"Gate-85  2·42+1          Z=85",                   self.WARN,   8,  False),
            (f"Au Z=79  prime, stable mirror",                    self.GOLD,   8,  False),
            (f"Hg Z=80  volatile mirror",                         self.CYAN,   8,  False),
        ]

        y = 0.98
        for text, color, size, bold in lines:
            if text == "":
                y -= 0.028
                continue
            w = "bold" if bold else "normal"
            ax.text(0.02, y, text, transform=ax.transAxes,
                    color=color, fontsize=size, fontweight=w,
                    va="top", fontfamily="monospace")
            y -= 0.048 if size >= 9 else 0.040

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _psi_regime(self, psi) -> str:
        thr = self.engine.COLLAPSE_THRESHOLD
        rel = psi / thr
        if rel > 1.0:  return "⚡ COLLAPSE"
        if rel > 0.9:  return "🔴 CRITICAL"
        if rel > 0.6:  return "🟠 STRESSED"
        if rel > 0.3:  return "🟡 ACTIVE"
        return "🟢 STABLE"

    def _regime_color(self, psi) -> str:
        thr = self.engine.COLLAPSE_THRESHOLD
        rel = psi / thr
        if rel > 1.0:  return self.CRIT
        if rel > 0.9:  return self.CRIT
        if rel > 0.6:  return self.WARN
        if rel > 0.3:  return self.GOLD
        return self.ACCENT

    # ── Запуск ────────────────────────────────────────────────────────────────

    def run(self):
        self.ani = FuncAnimation(
            self.fig,
            self.update,
            interval=38,   # ~26 fps
            blit=False,
            cache_frame_data=False,
        )
        plt.show()


# ══════════════════════════════════════════════════════════════════════════
#  Ниже — автоматически добавлено сборкой для веба (build/build.py).
#  Оригинальный файл UNIVERSE_2.0.py не изменялся.
# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  WEB BUILD — браузерная сборка (Pyodide)
#  Тот же движок и те же панели, но артисты создаются ОДИН раз и дальше
#  обновляются на месте (set_data / set_offsets / set_text). Это убирает
#  пересоздание ~400 объектов на кадр и даёт приемлемый FPS в браузере.
# ══════════════════════════════════════════════════════════════════════════════

from matplotlib.colors import to_rgba
from matplotlib.collections import LineCollection
from matplotlib import colormaps

WEB_DPI     = 72
WEB_FIGSIZE = (20.0, 11.25)

# Эмодзи в шрифтах DejaVu отсутствуют → в браузере были бы «квадратики».
# Заменяем на ASCII-маркеры (цвет и так кодирует режим).
REGIMES = [
    (1.00, "!! COLLAPSE"),
    (0.90, "!  CRITICAL"),
    (0.60, "•  STRESSED"),
    (0.30, "·  ACTIVE"),
    (0.00, "·  STABLE"),
]


def _regime_text(psi, thr):
    rel = psi / thr
    for lim, txt in REGIMES:
        if rel > lim:
            return txt
    return REGIMES[-1][1]


class UniverseWeb(UniverseOS):
    """Версия UniverseOS для браузера (in-place rendering)."""

    # ── Каркас ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        plt.rcParams.update({
            "font.family":  "monospace",
            "axes.facecolor": self.BG2,
            "axes.edgecolor": self.GRID,
            "axes.labelcolor": self.TEXT,
            "xtick.color": self.TEXT,
            "ytick.color": self.TEXT,
            "grid.color": self.GRID,
            "grid.alpha": 0.5,
            "figure.facecolor": self.BG,
        })

        self.fig = plt.figure(figsize=WEB_FIGSIZE, dpi=WEB_DPI, facecolor=self.BG)

        gs = gridspec.GridSpec(3, 4, figure=self.fig,
                               left=0.04, right=0.98,
                               top=0.93, bottom=0.12,
                               wspace=0.35, hspace=0.45)

        self.ax_cayley = self.fig.add_subplot(gs[0:2, 0:2], projection="3d",
                                              facecolor=self.BG)
        self.ax_cayley.set_facecolor(self.BG)
        self.ax_mass   = self.fig.add_subplot(gs[0, 2:4])
        self.ax_mass.set_yscale("log")
        self.ax_psi    = self.fig.add_subplot(gs[1, 2])
        self.ax_stress = self.fig.add_subplot(gs[1, 3])
        self.ax_energy = self.fig.add_subplot(gs[2, 2:4])
        self.ax_info   = self.fig.add_subplot(gs[2, 0:2])
        self.ax_info.set_axis_off()

        self.fig.text(0.5, 0.975,
            "UNIVERSE OS  ·  ТОРВ / ТабАк  ·  p = 531441/524288  ·  θ = ln(p)",
            ha="center", va="top", fontsize=13, color=self.ACCENT, fontweight="bold")

        ax_spd = self.fig.add_axes([0.07, 0.04, 0.18, 0.025], facecolor=self.BG2)
        self.sl_speed = Slider(ax_spd, "Speed", 0.1, 5.0, valinit=1.0,
                               color=self.ACCENT, handle_style={"facecolor": self.GOLD})
        self.sl_speed.label.set_color(self.TEXT)
        self.sl_speed.valtext.set_color(self.ACCENT)

        ax_thr = self.fig.add_axes([0.30, 0.04, 0.18, 0.025], facecolor=self.BG2)
        self.sl_thr = Slider(ax_thr, "Ψ threshold", 0.5, 2.5, valinit=P,
                             color=self.WARN, handle_style={"facecolor": self.CRIT})
        self.sl_thr.label.set_color(self.TEXT)
        self.sl_thr.valtext.set_color(self.WARN)

        ax_reset = self.fig.add_axes([0.52, 0.035, 0.07, 0.04], facecolor="#1a0a0a")
        self.btn_reset = Button(ax_reset, "RESET", color="#1a0a0a", hovercolor="#330000")
        self.btn_reset.label.set_color(self.CRIT)
        self.btn_reset.on_clicked(self._on_reset)

        ax_pause = self.fig.add_axes([0.61, 0.035, 0.07, 0.04], facecolor="#0a1a0a")
        self.btn_pause = Button(ax_pause, "PAUSE", color="#0a1a0a", hovercolor="#003300")
        self.btn_pause.label.set_color(self.ACCENT)
        self.btn_pause.on_clicked(self._on_pause)

        # предвычисленные индексы рёбер
        self._edge_i = np.array([i for i, j in self.projector.edges], dtype=np.intp)
        self._edge_j = np.array([j for i, j in self.projector.edges], dtype=np.intp)

        self._psi_marks    = []
        self._energy_marks = []

        self._build_cayley()
        self._build_mass()
        self._build_psi()
        self._build_stress()
        self._build_energy()
        self._build_info()

    def _on_reset(self, _):
        UniverseOS._on_reset(self, _)
        for art in self._psi_marks + self._energy_marks:
            try:
                art.remove()
            except Exception:
                pass
        self._psi_marks = []
        self._energy_marks = []

    # ── P1: граф Кэли 3D ──────────────────────────────────────────────────────

    def _build_cayley(self):
        ax = self.ax_cayley
        ax.set_axis_off()
        ax.set_facecolor(self.BG)

        self._cay_lc = Line3DCollection([[(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]], zorder=1)
        ax.add_collection3d(self._cay_lc, autolim=False)

        z = np.zeros((N, 3))
        self._cay_flash = ax.scatter(z[:, 0], z[:, 1], z[:, 2], s=np.zeros(N),
                                     c=self.CRIT, alpha=0.5, zorder=3)
        self._cay_flash.set_visible(False)
        self._cay_nodes = ax.scatter(z[:, 0], z[:, 1], z[:, 2], s=np.full(N, 10.0),
                                     c="#1a3a6a", alpha=0.85, edgecolors="none", zorder=4)

        self._cay_anchor = {}
        for sym, a in ANCHORS.items():
            if a["Z"] < N:
                sc = ax.scatter([0.0], [0.0], [0.0], s=200, c=a["color"],
                                marker=a["marker"], edgecolors="white",
                                linewidths=0.8, zorder=5, label=sym)
                self._cay_anchor[sym] = sc

        self._cay_title = ax.set_title("", color=self.TEXT, fontsize=10, pad=8)
        self._cay_legend = ax.legend(loc="lower left", fontsize=7,
                                     facecolor=self.BG, edgecolor=self.GRID,
                                     labelcolor=self.TEXT, framealpha=0.8,
                                     markerscale=0.8)

    def _u_cayley(self, xyz, edge_stress, stress, psi, collapsed):
        ax = self.ax_cayley
        i_idx, j_idx = self._edge_i, self._edge_j

        # рёбра (448 штук) — одной коллекцией
        self._cay_lc.set_segments(np.stack([xyz[i_idx], xyz[j_idx]], axis=1))

        max_e = max(float(edge_stress.max()) if edge_stress.size else 0.0, 1e-9)
        rel = edge_stress / max_e
        gold = i_idx < 64
        cols = np.empty((rel.size, 4))
        cols[:, 0] = np.where(gold, 0.6 + 0.4 * rel, 0.0)
        cols[:, 1] = np.where(gold, 0.5 + 0.35 * rel, 0.5 + 0.5 * rel)
        cols[:, 2] = np.where(gold, 0.0, 0.6 + 0.4 * rel)
        cols[:, 3] = 0.05 + 0.35 * rel
        self._cay_lc.set_color(cols)
        self._cay_lc.set_linewidths(0.5 + 1.5 * rel)

        # узлы
        max_s = max(float(stress.max()), 1e-9)
        node_s = 8 + 180 * (stress / max_s)
        thr = self.engine.COLLAPSE_THRESHOLD
        rel_n = stress / thr
        crit, warn = to_rgba(self.CRIT), to_rgba(self.WARN)
        cool, cold = to_rgba("#88bbff"), to_rgba("#1a3a6a")
        node_c = np.empty((N, 4))
        for k in range(N):
            r = rel_n[k]
            c = crit if r > 0.9 else (warn if r > 0.6 else (cool if r > 0.3 else cold))
            node_c[k] = (c[0], c[1], c[2], 0.85)

        self._cay_nodes._offsets3d = (xyz[:, 0], xyz[:, 1], xyz[:, 2])
        self._cay_nodes.set_sizes(node_s)
        self._cay_nodes.set_facecolors(node_c)

        # вспышка коллапса
        if collapsed:
            self._cay_flash._offsets3d = (xyz[:, 0], xyz[:, 1], xyz[:, 2])
            self._cay_flash.set_sizes(node_s * 3)
        self._cay_flash.set_visible(bool(collapsed))

        # химические якоря
        for sym, sc in self._cay_anchor.items():
            z = ANCHORS[sym]["Z"]
            sc._offsets3d = ([xyz[z, 0]], [xyz[z, 1]], [xyz[z, 2]])

        # масштаб и камера
        ax.auto_scale_xyz(xyz[:, 0], xyz[:, 1], xyz[:, 2])
        ax.view_init(elev=22 + 8 * math.sin(self.engine.t * 0.006),
                     azim=self.engine.t * 0.35)

        regime = _regime_text(psi, thr)
        self._cay_title.set_text(
            f"4D Cayley–Tabakov Lattice  |  Ψ={psi:.5f}  |  {regime}")
        self._cay_title.set_color(self.CRIT if psi > thr * 0.9 else self.TEXT)

    # ── P2: матрица масс ──────────────────────────────────────────────────────

    def _build_mass(self):
        ax = self.ax_mass
        # прогоняем оригинальную отрисовку один раз, чтобы получить те же лимиты
        UniverseOS._draw_mass(self, 0.0)
        ylim = ax.get_ylim()
        ax.cla()
        ax.set_facecolor(self.BG2)
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3, color=self.GRID)

        E_list = list(OCTAVES.keys())
        masses = [OCTAVE_MASSES[E] for E in E_list]

        self._mass_line, = ax.plot(E_list, masses, color="#1b2a47", lw=1.2,
                                   ls="--", alpha=0.7, zorder=1)

        normal = [E for E in E_list if E != 5]
        self._mass_sc = ax.scatter(normal, [OCTAVE_MASSES[E] for E in normal],
                                   s=120, c=[OCTAVES[E]["color"] for E in normal],
                                   edgecolors="white", linewidths=0.5, zorder=2)
        self._mass_g42 = ax.scatter([5], [OCTAVE_MASSES[5]], s=120, color=self.WARN,
                                    edgecolors="white", linewidths=0.8, zorder=3,
                                    alpha=0.9)

        for E in E_list:
            m = OCTAVE_MASSES[E]
            ax.text(E + 0.12, m * 1.15,
                    f"{OCTAVES[E]['name']}\n{m:.3e} ×10⁻²⁷kg",
                    color=self.TEXT, fontsize=7.5, va="bottom")

        self._mass_g42_line = ax.axhline(OCTAVE_MASSES[5], color=self.WARN, ls=":",
                                         alpha=0.4, lw=1)
        ax.axhline(REFERENCE["proton_kg"] * 1e27, color=self.CYAN, ls="--",
                   alpha=0.4, lw=0.8, label="M_p exp")

        ax.set_xlim(0.5, 7.8)
        ax.set_ylim(ylim)
        ax.set_xlabel("Октава E", fontsize=9)
        ax.set_ylabel("×10⁻²⁷ кг", fontsize=9)
        ax.set_title("Матрица квантования масс (7 октав ТабАк)",
                     color=self.TEXT, fontsize=9)
        ax.tick_params(labelsize=7)

    def _u_mass(self, psi):
        pulse = abs(math.sin(self.engine.t * 0.08)) * psi / P
        self._mass_g42.set_sizes(np.array([120 + 180 * pulse]))
        self._mass_g42_line.set_alpha(0.4 * abs(math.sin(self.engine.t * 0.05)))

    # ── P3: фазовый монитор Ψ ─────────────────────────────────────────────────

    def _build_psi(self):
        ax = self.ax_psi
        ax.set_facecolor(self.BG2)
        ax.grid(True, alpha=0.3, color=self.GRID)

        self._psi_lc = LineCollection([], linewidths=1.0, alpha=0.85, zorder=2)
        ax.add_collection(self._psi_lc)

        ax.axhline(self.engine.COLLAPSE_THRESHOLD, color=self.WARN, ls=":",
                   lw=1.0, alpha=0.7)
        ax.axhline(P, color=self.GOLD, ls="--", lw=0.7, alpha=0.5, label="p")

        self._psi_title = ax.set_title("Ψ(t)", color=self.TEXT, fontsize=9)
        ax.set_xlabel("кадры", fontsize=8)
        ax.set_ylabel("Ψ", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.relim()
        ax.autoscale_view()

    def _u_psi(self, psi):
        ax = self.ax_psi
        pts = self.psi_trace
        n = len(pts)
        thr = self.engine.COLLAPSE_THRESHOLD
        ys = np.fromiter(pts, dtype=float, count=n) if n else np.zeros(0)

        if n >= 2:
            xs = np.arange(n, dtype=float)
            segs = np.stack([np.column_stack([xs[:-1], ys[:-1]]),
                             np.column_stack([xs[1:], ys[1:]])], axis=1)
            self._psi_lc.set_segments(segs)

            rel = ys[:-1] / thr
            cols = np.empty((rel.size, 4))
            c_crit, c_warn, c_cyan = to_rgba(self.CRIT), to_rgba(self.WARN), to_rgba(self.CYAN)
            for k in range(rel.size):
                r = rel[k]
                cols[k] = c_crit if r > 0.9 else (c_warn if r > 0.65 else c_cyan)
            self._psi_lc.set_color(cols)
        else:
            self._psi_lc.set_segments([])

        # метки коллапсов (создаём по одной, а не каждый кадр)
        marks = [m for m in self.collapse_markers if 0 <= m < n]
        while len(self._psi_marks) < len(marks):
            m = marks[len(self._psi_marks)]
            self._psi_marks.append(
                ax.axvline(m, color=self.CRIT, alpha=0.6, lw=0.8, ls="--"))

        self._psi_title.set_text(f"Ψ(t)  collapses={self.engine.collapses}")

        # лимиты как у matplotlib-автоскейла (margin 5%)
        xr = max(n - 1, 1)
        ax.set_xlim(-0.05 * xr, 1.05 * xr)
        if n:
            lo = min(float(ys.min()), thr, P)
            hi = max(float(ys.max()), thr, P)
        else:
            lo, hi = 0.0, max(thr, P)
        pad = 0.05 * (hi - lo) if hi > lo else 0.05
        ax.set_ylim(lo - pad, hi + pad)

    # ── P4: узловой стресс ────────────────────────────────────────────────────

    def _build_stress(self):
        ax = self.ax_stress
        ax.set_facecolor(self.BG2)
        ax.grid(True, alpha=0.3, color=self.GRID)

        xs = np.arange(N)
        self._stress_bars = ax.bar(xs, np.zeros(N), color="#1a3a6a", width=1.0,
                                   alpha=0.85, edgecolor="none")

        for sym, a in ANCHORS.items():
            z = a["Z"]
            if z < N:
                ax.axvline(z, color=a["color"], ls="--", alpha=0.6, lw=0.8)
                ax.text(z, 0.0, sym, color=a["color"], fontsize=7, ha="center")

        ax.axvline(GATE_42, color=self.WARN, ls=":", lw=1.2, alpha=0.8)
        ax.axvline(GATE_85, color=self.WARN, ls=":", lw=1.2, alpha=0.8)

        ax.set_title("Узловой стресс σ(Z)", color=self.TEXT, fontsize=9)
        ax.set_xlabel("Z (узел)", fontsize=8)
        ax.set_ylabel("σ", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_xlim(0, N)
        ax.set_ylim(0, 1.0)

    def _u_stress(self, stress, psi):
        max_s = max(float(stress.max()), 1e-9)
        cols = colormaps["plasma"](stress / max_s)
        for rect, h, c in zip(self._stress_bars, stress, cols):
            rect.set_height(float(h))
            rect.set_facecolor(c)
        self.ax_stress.set_ylim(0, max_s * 1.05)

    # ── P5: энергия ───────────────────────────────────────────────────────────

    def _build_energy(self):
        ax = self.ax_energy
        ax.set_facecolor(self.BG2)
        ax.grid(True, alpha=0.3, color=self.GRID)

        self._energy_poly = ax.fill_between([0.0, 1.0], [0.0, 0.0],
                                            alpha=0.25, color=self.GOLD)
        self._energy_line, = ax.plot([], [], color=self.GOLD, lw=1.2)

        ax.set_title("Энергия вакуума E(t)", color=self.TEXT, fontsize=9)
        ax.set_xlabel("кадры", fontsize=8)
        ax.set_ylabel("E [с.е.и.]", fontsize=8)
        ax.tick_params(labelsize=7)

    def _u_energy(self):
        ax = self.ax_energy
        pts = self.energy_trace
        n = len(pts)
        if n >= 2:
            xs = np.arange(n, dtype=float)
            ys = np.fromiter(pts, dtype=float, count=n)
            self._energy_line.set_data(xs, ys)
            verts = np.vstack([np.column_stack([xs, ys]),
                               [[xs[-1], 0.0], [xs[0], 0.0]]])
            self._energy_poly.set_verts([verts])
        else:
            self._energy_line.set_data([], [])
            self._energy_poly.set_verts([np.zeros((0, 2))])

        marks = [m for m in self.collapse_markers if 0 <= m < n]
        while len(self._energy_marks) < len(marks):
            m = marks[len(self._energy_marks)]
            self._energy_marks.append(
                ax.axvline(m, color=self.CRIT, alpha=0.5, lw=0.8))

        ax.relim()
        ax.autoscale_view()

    # ── P6: панель констант ───────────────────────────────────────────────────

    def _build_info(self):
        ax = self.ax_info
        ax.set_axis_off()
        ax.set_facecolor(self.BG)

        # (текст, цвет, кегль, жирный, ключ)  ключ != None → строка обновляется
        lines = [
            ("═══ ТОРВ: константы из p ═══════════════════════", self.ACCENT, 12, True,  None),
            (f"p  = {P:.8f}  (3¹²/2¹⁹)",                       self.GOLD,   9,  False, None),
            (f"θ  = {THETA:.8f}  (ln p)",                      self.GOLD,   9,  False, None),
            ("", self.TEXT, 8, False, None),
            ("═══ Предсказание  vs  Эксперимент ══════════════", self.CYAN, 9, True,  None),
            (f"α⁻¹  = {ALPHA_INV:.5f}  |  ref {REFERENCE['alpha_inv']:.5f}  "
             f"Δ {abs(ALPHA_INV-REFERENCE['alpha_inv']):.4f}",   self.TEXT,   8,  False, None),
            (f"ΩΛ   = {OMEGA_L:.5f}  |  ref {REFERENCE['omega_L']:.4f}  "
             f"Δ {abs(OMEGA_L-REFERENCE['omega_L']):.4f}",       self.TEXT,   8,  False, None),
            (f"ΩDM/ΩB = {OMEGA_DM:.3f}  |  ref {REFERENCE['omega_dm_ob']:.3f}  "
             f"Δ {abs(OMEGA_DM-REFERENCE['omega_dm_ob']):.3f}",  self.TEXT,   8,  False, None),
            ("", self.TEXT, 8, False, None),
            ("═══ Текущее состояние ТОРВ ═════════════════════", self.WARN, 9, True,  None),
            ("", self.WARN, 9, False, "psi"),
            ("", self.TEXT, 8, False, "energy"),
            ("", self.CRIT, 9, False, "coll"),
            ("", self.WARN, 9, True,  "regime"),
            ("", self.TEXT, 8, False, None),
            ("═══ Якоря ═══════════════════════════════════════", "#5577aa", 9, True,  None),
            ("Gate-42  I(k=2)=10·4+2   Z=42",                   self.WARN,   8,  False, None),
            ("Gate-85  2·42+1          Z=85",                   self.WARN,   8,  False, None),
            ("Au Z=79  prime, stable mirror",                    self.GOLD,   8,  False, None),
            ("Hg Z=80  volatile mirror",                         self.CYAN,   8,  False, None),
        ]

        self._info = {}
        y = 0.98
        for text, color, size, bold, key in lines:
            if text == "" and key is None:
                y -= 0.028
                continue
            t = ax.text(0.02, y, text, transform=ax.transAxes, color=color,
                        fontsize=size, fontweight=("bold" if bold else "normal"),
                        va="top", fontfamily="monospace")
            if key:
                self._info[key] = t
            y -= 0.048 if size >= 9 else 0.040

    def _u_info(self, psi, energy, collapses):
        thr = self.engine.COLLAPSE_THRESHOLD
        self._info["psi"].set_text(f"Ψ(t)  = {psi:.6f}   (порог {thr:.5f})")
        self._info["energy"].set_text(f"E(t)  = {energy:.4e} с.е.и.")
        self._info["coll"].set_text(f"Коллапсов: {collapses}   t={self.engine.t:.1f}")
        self._info["coll"].set_color(self.CRIT if collapses > 0 else self.TEXT)
        self._info["regime"].set_text(f"Режим: {_regime_text(psi, thr)}")
        self._info["regime"].set_color(self._regime_color(psi))

    # ── Главный кадр ──────────────────────────────────────────────────────────

    def update(self, frame_num):
        if self.paused:
            return

        self.frame += 1
        speed = self.sl_speed.val
        self.engine.COLLAPSE_THRESHOLD = self.sl_thr.val

        state = None
        for _ in range(max(1, int(speed))):
            state = self.engine.step(dt=speed / max(1, int(speed)))

        psi       = state["psi"]
        stress    = state["stress"]
        energy    = state["energy"]
        collapsed = state["collapsed"]

        self.psi_trace.append(psi)
        self.energy_trace.append(energy)
        if collapsed:
            self.collapse_markers.append(len(self.psi_trace) - 1)

        xyz, edge_stress = self.projector.project(self.engine.t, psi, stress)

        self._u_cayley(xyz, edge_stress, stress, psi, collapsed)
        self._u_mass(psi)
        self._u_psi(psi)
        self._u_stress(stress, psi)
        self._u_energy()
        self._u_info(psi, energy, state["collapses"])


# ── точка входа для веба ─────────────────────────────────────────────────────

def start_web():
    app = UniverseWeb()
    app.update(0)          # первый кадр, чтобы панели не были пустыми
    app.run()              # FuncAnimation + plt.show() (в pyodide не блокирует)
    return app
