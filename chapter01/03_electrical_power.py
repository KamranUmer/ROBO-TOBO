"""
Section 1.4.3 - Electrical systems: impedance and power.

Impedances with the operator D (D = d/dt, and D -> j*w for sinusoids):
    Z_R = R      Z_L = L*D      Z_C = 1/(C*D)

Power:
    instantaneous  p(t) = v(t) * i(t)
    time-averaged  P_av = (1/T) * integral_0^T v(t) i(t) dt

We drive three loads (R, RL, RC) with 230 V rms / 50 Hz, compute the current from the
impedance, and compare the numerically averaged power with Vrms * Irms * cos(phi).
Then we sweep frequency for a series RLC to see where the impedance is smallest (resonance).
"""
import numpy as np
import matplotlib.pyplot as plt

from common import finish

R, L, C = 50.0, 0.2, 100e-6            # ohm, H, F
Vrms, f = 230.0, 50.0
w = 2 * np.pi * f
T = 1 / f
t = np.linspace(0, 2 * T, 2000)

loads = {
    "R":  R,
    "RL": R + 1j * w * L,
    "RC": R + 1 / (1j * w * C),
}

fig, axes = plt.subplots(2, 3, figsize=(14, 7))
v = np.sqrt(2) * Vrms * np.sin(w * t)
print(f"{'load':4s} {'|Z| [ohm]':>10s} {'phi [deg]':>10s} {'P numeric [W]':>14s} {'V*I*cos(phi) [W]':>17s}")
for ax, (name, Z) in zip(axes[0], loads.items()):
    phi = np.angle(Z)
    i = np.sqrt(2) * Vrms / abs(Z) * np.sin(w * t - phi)
    p = v * i
    one_period = t <= T
    P_num = np.trapezoid(p[one_period], t[one_period]) / T
    P_formula = Vrms * (Vrms / abs(Z)) * np.cos(phi)
    print(f"{name:4s} {abs(Z):10.1f} {np.degrees(phi):10.1f} {P_num:14.1f} {P_formula:17.1f}")

    ax.plot(t * 1e3, v, label="v(t) [V]")
    ax.plot(t * 1e3, 50 * i, label="50 x i(t) [A]")
    ax.set(title=f"{name} load: phase = {np.degrees(phi):.0f} deg", xlabel="time [ms]")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    axb = axes[1][list(loads).index(name)]
    axb.fill_between(t * 1e3, p, alpha=0.4, label="p(t) = v*i")
    axb.axhline(P_num, color="r", label=f"P_av = {P_num:.0f} W")
    axb.set(xlabel="time [ms]", ylabel="power [W]")
    axb.legend(fontsize=8)
    axb.grid(alpha=0.3)
fig.suptitle("Instantaneous vs average power (negative p = energy flowing back to the source)")
finish(fig, "03a_power")

# Series RLC impedance vs frequency
fs = np.logspace(0, 3, 500)
Z = R + 1j * 2 * np.pi * fs * L + 1 / (1j * 2 * np.pi * fs * C)
f0 = 1 / (2 * np.pi * np.sqrt(L * C))
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
a1.loglog(fs, abs(Z))
a1.axvline(f0, ls="--", c="gray")
a1.set(ylabel="|Z| [ohm]", title=f"Series RLC impedance, resonance at f0 = {f0:.1f} Hz (|Z| = R)")
a2.semilogx(fs, np.degrees(np.angle(Z)))
a2.axvline(f0, ls="--", c="gray")
a2.set(xlabel="frequency [Hz]", ylabel="phase [deg]")
for a in (a1, a2):
    a.grid(alpha=0.3, which="both")
finish(fig, "03b_rlc_impedance")
