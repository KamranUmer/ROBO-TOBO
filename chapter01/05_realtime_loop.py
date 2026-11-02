"""
Sections 1.3.2 and 1.4.5 - Simulated time vs real (wall-clock) time.

A simulation can run faster than real time because nobody is waiting on it. Once real
hardware joins the loop (hardware-in-the-loop), the model has to be locked to the wall
clock: each control tick must happen every Ts seconds, no earlier and no later.

This script
    1. runs a plant model as fast as possible and reports how much faster than real time it is,
    2. runs a 100 Hz loop locked to the wall clock and measures the timing jitter,
       which is what you get on a normal desktop OS (no real-time guarantees).

The plant is a first-order speed model, the kind of "first principle module" from Fig. 1-4.
In Phase 2 this same loop will talk to a microcontroller over USB instead of to a model.
"""
import time

import numpy as np
import matplotlib.pyplot as plt

from common import finish

TAU, K = 0.3, 2.0        # plant time constant [s], gain


def plant_step(y, u, dt):
    return y + dt * (K * u - y) / TAU


def controller(ref, y, state, dt, kp=1.5, ki=4.0):
    e = ref - y
    state["i"] += e * dt
    return kp * e + ki * state["i"]


def ref_at(t):
    return 1.0 if t < 2.5 else 0.5


# ---------------------------------------------------------------- 1. as fast as possible
dt, sim_seconds = 0.01, 600.0
y, st = 0.0, {"i": 0.0}
t0 = time.perf_counter()
for n in range(int(sim_seconds / dt)):
    u = controller(ref_at(n * dt % 5), y, st, dt)
    y = plant_step(y, u, dt)
wall = time.perf_counter() - t0
print(f"Simulated {sim_seconds:.0f} s in {wall * 1e3:.0f} ms wall time -> {sim_seconds / wall:,.0f}x faster than real time")

# ---------------------------------------------------------------- 2. locked to the wall clock
Ts, duration = 0.01, 5.0
y, st = 0.0, {"i": 0.0}
ticks, ys, refs = [], [], []
start = time.perf_counter()
next_tick = start
for n in range(int(duration / Ts)):
    # wait for the next tick: sleep most of the way, then spin for the last ~1 ms for accuracy
    while (remaining := next_tick - time.perf_counter()) > 0:
        if remaining > 0.002:
            time.sleep(remaining - 0.001)
    now = time.perf_counter()
    ticks.append(now - start)

    t = n * Ts
    u = controller(ref_at(t), y, st, Ts)   # in HIL: read sensor, compute, write actuator
    y = plant_step(y, u, Ts)
    ys.append(y)
    refs.append(ref_at(t))
    next_tick += Ts

ticks = np.array(ticks)
jitter_ms = (ticks - np.arange(len(ticks)) * Ts) * 1e3
period_ms = np.diff(ticks) * 1e3
print(f"Real-time loop at {1 / Ts:.0f} Hz: period mean {period_ms.mean():.3f} ms, "
      f"std {period_ms.std():.3f} ms, worst lateness {jitter_ms.max():.3f} ms")

fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(10, 8))
a1.plot(ticks, refs, "k:", label="reference")
a1.plot(ticks, ys, label="plant output")
a1.set(title=f"Loop locked to the wall clock at {1 / Ts:.0f} Hz", xlabel="wall-clock time [s]", ylabel="y")
a1.legend()
a2.plot(ticks, jitter_ms, ".", ms=3)
a2.set(xlabel="wall-clock time [s]", ylabel="tick lateness [ms]", title="Timing error of each tick")
a3.hist(period_ms, bins=50)
a3.axvline(Ts * 1e3, c="r", ls="--", label="ideal period")
a3.set(xlabel="measured period [ms]", ylabel="count", title="Distribution of loop periods")
a3.legend()
for a in (a1, a2, a3):
    a.grid(alpha=0.3)
finish(fig, "05_realtime_loop")
