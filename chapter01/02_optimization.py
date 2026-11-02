"""
Section 1.4.1 - Optimization.

Part A: the book's luggage problem, solved by a numerical optimizer instead of by intuition.
    Design variables  P = [L, W, H]
    Objective         maximize V = L*W*H   (=> minimize J = -V)
    Resource          L + W + H <= 80 cm
    Side constraints  0 <= L <= 40, 0 <= W <= 30, 0 <= H <= 20

Part B: the iteration P(k+1) = P(k) + t * S(k) drawn on a 2-D objective that has several
local minima, showing why the book recommends many runs from different starting points.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

from common import finish

# ---------------------------------------------------------------- Part A: luggage
J = lambda P: -np.prod(P)                                                   # objective
resource = {"type": "ineq", "fun": lambda P: 80 - P.sum()}                  # H(P) >= 0 form
cases = {
    "resource only": [(0, None)] * 3,
    "resource + side": [(0, 40), (0, 30), (0, 20)],
}
print("Luggage problem")
for name, bounds in cases.items():
    res = minimize(J, x0=[10, 10, 10], bounds=bounds, constraints=[resource], method="SLSQP")
    L, W, H = res.x
    print(f"  {name:16s} L={L:5.2f} W={W:5.2f} H={H:5.2f}  V={-res.fun:8.0f} cm^3  ({res.nit} iterations)")

# ---------------------------------------------------------------- Part B: local vs global minima
def J2(P):
    x, y = P
    return 0.05 * (x**2 + y**2) - np.cos(1.5 * x) * np.cos(1.5 * y)


def grad_J2(P):
    x, y = P
    return np.array([0.1 * x + 1.5 * np.sin(1.5 * x) * np.cos(1.5 * y),
                     0.1 * y + 1.5 * np.cos(1.5 * x) * np.sin(1.5 * y)])


def steepest_descent(P0, iters=200):
    """P(k+1) = P(k) + t*S(k) with S = -grad J and a backtracking step size t."""
    P, path = np.array(P0, float), [np.array(P0, float)]
    for _ in range(iters):
        S = -grad_J2(P)
        if np.linalg.norm(S) < 1e-6:          # no further improvement -> P* found
            break
        t = 1.0
        while J2(P + t * S) > J2(P) - 0.5 * t * S @ S:
            t *= 0.5
        P = P + t * S
        path.append(P)
    return np.array(path)


rng = np.random.default_rng(1)
starts = rng.uniform(-6, 6, size=(12, 2))
paths = [steepest_descent(p) for p in starts]
best = min(paths, key=lambda p: J2(p[-1]))
print(f"\nMulti-start: {len(starts)} runs, best P* = {best[-1].round(3)}, J* = {J2(best[-1]):.3f}")
print("  final J of each run:", np.round([J2(p[-1]) for p in paths], 2))

g = np.linspace(-6.5, 6.5, 300)
X, Y = np.meshgrid(g, g)
fig, ax = plt.subplots(figsize=(7, 6))
cs = ax.contourf(X, Y, J2((X, Y)), levels=30, cmap="viridis")
fig.colorbar(cs, label="J(P)")
for p in paths:
    ax.plot(p[:, 0], p[:, 1], "w.-", ms=3, lw=1)
    ax.plot(*p[0], "wo", ms=5)
    ax.plot(*p[-1], "rx", ms=9, mew=2)
ax.plot(*best[-1], "y*", ms=20, label="best of all runs (global min)")
ax.set(title="Steepest descent from 12 random starts\n(white o = start, red x = local minimum found)",
       xlabel="p1", ylabel="p2")
ax.legend(loc="upper right")
finish(fig, "02_optimization")
