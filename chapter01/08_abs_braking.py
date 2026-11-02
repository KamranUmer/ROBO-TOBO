"""
Problem 1.3(b) - Anti-lock braking system (ABS).

Purpose: stop the wheel from locking during an emergency stop.
    Sensor   : wheel speed sensor (Hall effect / inductive tooth wheel) -> wheel slip
    Actuator : hydraulic modulator valve that raises, holds, or releases brake pressure
    Process  : quarter-car model
                   m dv/dt = -mu(slip) * m g             (vehicle)
                   J dw/dt =  mu(slip) * m g * r - Tb    (wheel)
                   slip    = (v - w r) / v
    Control  : keep slip near 0.2, where the tyre gives the most friction

Tyre friction follows the Burckhardt model for dry asphalt. A locked wheel (slip = 1)
gives less friction than the peak AND gives no steering control.
Vehicle speed is assumed known here; a real ABS has to estimate it.
"""
import numpy as np
import matplotlib.pyplot as plt

from common import finish

g = 9.81
m = 375.0               # quarter of a 1500 kg car [kg]
r = 0.3                 # wheel radius [m]
J = 1.0                 # wheel inertia [kg*m^2]
v0 = 100 / 3.6          # initial speed [m/s]
TB_MAX = 1500.0         # brake torque the driver demands by stomping the pedal [N*m]
c1, c2, c3 = 1.2801, 23.99, 0.52   # Burckhardt dry asphalt


def mu(slip):
    return c1 * (1 - np.exp(-c2 * slip)) - c3 * slip


def simulate(abs_on, dt=1e-4):
    v, w, Tb, x, t = v0, v0 / r, 0.0, 0.0, 0.0
    target, band, rate = 0.2, 0.03, 8000.0     # slip target, hysteresis, valve pressure rate [N*m/s]
    log = []
    while v > 0.5:
        slip = (v - w * r) / v
        if abs_on:
            if slip > target + band:       # wheel about to lock -> release pressure
                Tb -= rate * dt
            elif slip < target - band:     # wheel has grip to spare -> build pressure
                Tb += rate * dt
            Tb = np.clip(Tb, 0, TB_MAX)
        else:
            Tb = min(TB_MAX, Tb + 20000 * dt)   # pedal applied over 75 ms, then held
        F = mu(slip) * m * g
        v -= dt * F / m
        w = max(0.0, w + dt * (F * r - Tb) / J)   # brakes cannot spin the wheel backwards
        x += v * dt
        t += dt
        log.append((t, v, w * r, slip, Tb, x))
    return np.array(log)


fig, axes = plt.subplots(2, 2, figsize=(13, 8))
s = np.linspace(0, 1, 200)
axes[0, 0].plot(s, mu(s))
axes[0, 0].axvline(0.2, c="g", ls="--", label="ABS target slip")
axes[0, 0].set(title="Tyre friction vs slip (dry asphalt)", xlabel="slip", ylabel="mu")
axes[0, 0].legend()

for name, abs_on, c in (("No ABS", False, "tab:red"), ("ABS", True, "tab:blue")):
    lg = simulate(abs_on)
    t, v, wr, slip, Tb, x = lg.T
    locked = t[(slip > 0.99) & (v > 5)]          # ignore the last crawl where slip is ill-defined
    lock_txt = f", wheel locked at t={locked[0]:.2f}s" if len(locked) else ", wheel never locked"
    print(f"{name:7s} stopping distance {x[-1]:5.1f} m, time {t[-1]:.2f} s{lock_txt}")
    axes[0, 1].plot(t, v * 3.6, c=c, label=f"{name}: vehicle")
    axes[0, 1].plot(t, wr * 3.6, c=c, ls="--", label=f"{name}: wheel")
    axes[1, 0].plot(t, slip, c=c, label=name)
    axes[1, 1].plot(x, v * 3.6, c=c, label=f"{name}: stops in {x[-1]:.1f} m")

axes[0, 1].set(title="Speeds", xlabel="time [s]", ylabel="km/h")
axes[1, 0].set(title="Wheel slip (1 = locked)", xlabel="time [s]", ylabel="slip", ylim=(0, 1.05))
axes[1, 1].set(title="Speed vs distance", xlabel="distance [m]", ylabel="km/h")
for a in axes.flat:
    a.grid(alpha=0.3)
    a.legend(fontsize=8)
finish(fig, "08_abs_braking")
