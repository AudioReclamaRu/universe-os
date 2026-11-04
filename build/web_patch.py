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
