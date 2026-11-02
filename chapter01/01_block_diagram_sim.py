"""
Section 1.4.1 - Modeling & Simulation with the three basic blocks (Figure 1-6).

Every block-diagram tool (Simulink, LabVIEW, ...) is built on:
    Summing junction   Y = X - W
    Gain               Y = K * X
    Integrator         Y = (1/D) X = integral(X) + Yo

Here we write a tiny block-diagram simulator ourselves, build a mass-spring-damper
    m x'' + c x' + k x = F(t)
out of only those three blocks, and run it through the three simulation phases the book
describes: initialization (sort the blocks), iteration (numerical integration), display.

The iteration part uses truncated Taylor series (Euler = 1st order, RK2, RK4) so you can
see how the truncation order changes the error.
"""
import numpy as np
import matplotlib.pyplot as plt

from common import finish


# ---------------------------------------------------------------- the three blocks
class Sum:
    def __init__(self, *inputs, signs):
        self.inputs, self.signs = inputs, signs

    def output(self, v):
        return sum(s * v[i] for i, s in zip(self.inputs, self.signs))


class Gain:
    def __init__(self, inp, K):
        self.inputs, self.K = (inp,), K

    def output(self, v):
        return self.K * v[self.inputs[0]]


class Integrator:
    """Holds a state. Its output is the state, so it does not need its input to produce an output."""

    def __init__(self, inp, y0=0.0):
        self.inputs, self.y0 = (inp,), y0


class Source:
    def __init__(self, fn):
        self.inputs, self.fn = (), fn


# ---------------------------------------------------------------- the simulator
class Diagram:
    def __init__(self, blocks):
        self.blocks = blocks
        self.integrators = [n for n, b in blocks.items() if isinstance(b, Integrator)]
        self.order = self._sort()

    def _sort(self):
        """Initialization phase: order the algebraic blocks so each runs after its inputs are known.
        Integrator and source outputs are known at the start of every step, so they are the roots."""
        known = set(self.integrators) | {n for n, b in self.blocks.items() if isinstance(b, Source)}
        pending = [n for n in self.blocks if n not in known]
        order = []
        while pending:
            ready = [n for n in pending if all(i in known for i in self.blocks[n].inputs)]
            if not ready:
                raise ValueError(f"algebraic loop among {pending}")
            for n in ready:
                order.append(n)
                known.add(n)
                pending.remove(n)
        return order

    def derivatives(self, t, x):
        """Evaluate every signal for integrator states x, return what each integrator is integrating."""
        v = dict(zip(self.integrators, x))
        for n, b in self.blocks.items():
            if isinstance(b, Source):
                v[n] = b.fn(t)
        for n in self.order:
            v[n] = self.blocks[n].output(v)
        return np.array([v[self.blocks[n].inputs[0]] for n in self.integrators]), v

    def simulate(self, t_end, dt, method="rk4"):
        """Iteration phase: march the integrator states forward in time."""
        f = lambda t, x: self.derivatives(t, x)[0]
        x = np.array([self.blocks[n].y0 for n in self.integrators], float)
        ts = np.arange(0, t_end + dt / 2, dt)
        xs = [x]
        for t in ts[:-1]:
            if method == "euler":      # Taylor series truncated after the 1st derivative
                x = x + dt * f(t, x)
            elif method == "rk2":      # matches the Taylor series up to the 2nd derivative
                k1 = f(t, x)
                x = x + dt / 2 * (k1 + f(t + dt, x + dt * k1))
            else:                      # rk4: up to the 4th derivative
                k1 = f(t, x)
                k2 = f(t + dt / 2, x + dt / 2 * k1)
                k3 = f(t + dt / 2, x + dt / 2 * k2)
                k4 = f(t + dt, x + dt * k3)
                x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            xs.append(x)
        return ts, dict(zip(self.integrators, np.array(xs).T))


# ---------------------------------------------------------------- mass-spring-damper
m, c, k = 1.0, 0.8, 16.0     # kg, N*s/m, N/m  -> wn = 4 rad/s, zeta = 0.1
F0 = 16.0                     # N step force -> static deflection F0/k = 1 m

#   F ---->(+)---[1/m]---> a ---[1/D]---> v ---[1/D]---> x
#           ^-  ^-                         |              |
#           |   +--------[c]---------------+              |
#           +------------[k]------------------------------+
msd = Diagram({
    "F":     Source(lambda t: F0 if t >= 0 else 0.0),
    "sum":   Sum("F", "c_v", "k_x", signs=(+1, -1, -1)),
    "a":     Gain("sum", 1 / m),
    "v":     Integrator("a", y0=0.0),
    "x":     Integrator("v", y0=0.0),
    "c_v":   Gain("v", c),
    "k_x":   Gain("x", k),
})
print("block evaluation order found during initialization:", msd.order)


def exact(t):
    wn = np.sqrt(k / m)
    z = c / (2 * np.sqrt(k * m))
    wd = wn * np.sqrt(1 - z**2)
    return F0 / k * (1 - np.exp(-z * wn * t) * (np.cos(wd * t) + z / np.sqrt(1 - z**2) * np.sin(wd * t)))


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

dt = 0.05
t_fine = np.linspace(0, 8, 2000)
ax1.plot(t_fine, exact(t_fine), "k", lw=3, alpha=0.3, label="exact solution")
for method in ("euler", "rk2", "rk4"):
    ts, out = msd.simulate(8, dt, method)
    ax1.plot(ts, out["x"], label=f"{method}, dt={dt}s")
ax1.set(title="Mass-spring-damper step response from 3 basic blocks",
        xlabel="time [s]", ylabel="x [m]")
ax1.legend()
ax1.grid(alpha=0.3)

# Global error vs step size: the slope of each line is the order of the method.
dts = np.logspace(-3.3, -1, 10)
for method, mk in (("euler", "o"), ("rk2", "s"), ("rk4", "^")):
    errs = []
    for h in dts:
        ts, out = msd.simulate(4, h, method)
        errs.append(np.max(np.abs(out["x"] - exact(ts))))
    slope = np.polyfit(np.log(dts), np.log(errs), 1)[0]
    ax2.loglog(dts, errs, mk + "-", label=f"{method} (slope = {slope:.1f})")
ax2.set(title="Truncation order -> accuracy", xlabel="step size dt [s]", ylabel="max |error| [m]")
ax2.legend()
ax2.grid(alpha=0.3, which="both")

finish(fig, "01_block_diagram_sim")
