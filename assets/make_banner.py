"""Draws assets/banner.png, the header image of the repository README (1280 x 400 px)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BG, FG, MUTED, GRID = "#0f172a", "#f1f5f9", "#94a3b8", "#1e293b"
RED, GREEN, BLUE, YEL = "#f87171", "#4ade80", "#38bdf8", "#facc15"

fig = plt.figure(figsize=(12.8, 4.0), dpi=100, facecolor=BG)

# Right half: an under-damped and a well-damped step response, the motif of the whole repo
ax = fig.add_axes([0.5, 0.0, 0.5, 1.0], facecolor=BG)
t = np.linspace(0, 10, 600)
for zeta, color, lw in ((0.15, RED, 3), (0.7, GREEN, 3), (1.0, BLUE, 2)):
    wd = np.sqrt(max(1 - zeta**2, 1e-6))
    y = 1 - np.exp(-zeta * t) * (np.cos(wd * t) + zeta / wd * np.sin(wd * t))
    for glow in (14, 8):                          # soft glow under each curve
        ax.plot(t, y, color=color, lw=lw + glow, alpha=0.04, solid_capstyle="round")
    ax.plot(t, y, color=color, lw=lw, solid_capstyle="round")
ax.axhline(1, color=MUTED, ls=":", lw=1.5)
ax.set(xlim=(-0.5, 10.5), ylim=(-0.25, 1.75))
ax.set_xticks(np.arange(0, 11, 1))
ax.set_yticks(np.arange(-0.25, 1.76, 0.25))
ax.tick_params(length=0, labelbottom=False, labelleft=False)
ax.grid(color=GRID, lw=1)
for s in ax.spines.values():
    s.set_visible(False)

# Fade the plot into the text side
fade = np.linspace(1, 0, 256)[None, :]
ax.imshow(np.dstack([np.full((1, 256, 3), matplotlib.colors.to_rgb(BG)), fade[..., None] ** 2.2]),
          extent=(-0.5, 4, -0.25, 1.75), aspect="auto", zorder=5)

fig.text(0.05, 0.66, "ROBO-TOBO", fontsize=58, weight="bold", color=FG, va="center")
fig.text(0.052, 0.47, "Learning mechatronics in public", fontsize=21, color=BLUE, va="center")
fig.text(0.052, 0.35, "simulate  →  build  →  compare", fontsize=17, color=MUTED, va="center")
x = 0.052
for tag, color in (("Python", YEL), ("Control", GREEN), ("Sensors", BLUE), ("Actuators", RED)):
    txt = fig.text(x, 0.17, tag, fontsize=13, color=color, va="center",
                   bbox=dict(boxstyle="round,pad=0.45", fc=GRID, ec=color, lw=1.2))
    fig.canvas.draw()
    x += txt.get_window_extent().width / fig.bbox.width + 0.025

out = Path(__file__).parent / "banner.png"
fig.savefig(out, facecolor=BG)
print(f"saved {out}")
