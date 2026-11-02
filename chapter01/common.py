"""Shared helpers for the Chapter 1 simulations."""
import os
from pathlib import Path

import matplotlib.pyplot as plt

FIG_DIR = Path(__file__).parent / "figures"


def rk4_step(f, t, x, dt, *args):
    """One 4th-order Runge-Kutta step for dx/dt = f(t, x, *args)."""
    k1 = f(t, x, *args)
    k2 = f(t + dt / 2, x + dt / 2 * k1, *args)
    k3 = f(t + dt / 2, x + dt / 2 * k2, *args)
    k4 = f(t + dt, x + dt * k3, *args)
    return x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


def finish(fig, name):
    """Save the figure to chapter01/figures/<name>.png and show it (set NO_SHOW=1 to skip the window)."""
    FIG_DIR.mkdir(exist_ok=True)
    fig.tight_layout()
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=120)
    print(f"saved {path.relative_to(Path(__file__).parent.parent)}")
    if not os.environ.get("NO_SHOW"):
        plt.show()
    plt.close(fig)
