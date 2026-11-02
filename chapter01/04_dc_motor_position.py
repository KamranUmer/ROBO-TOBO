"""
Example 1.1 - Step-by-step mechatronic design: position control of a PM DC gear motor
with a Hall-effect quadrature encoder and a PI controller (Figure 1-27).

The book spreads this example over Ch.3 (sensor), Ch.4 (motor model), Ch.6 (PI design)
and Ch.7/8 (interfacing, implementation). Here is a first-principles version of the
whole loop so you can see the pieces working together before diving into each chapter.

It also shows the book's point about "unmodeled errors" (Section 1.3): the same controller
is run on
    1. an ideal model      - continuous control, perfect angle measurement, unlimited voltage
    2. a realistic model   - 1 kHz digital controller, encoder quantization, 12 V supply limit
                             and Coulomb friction
and the responses differ.

Motor model (Chapter 4):
    L di/dt = V - R i - Ke w          (armature circuit)
    J dw/dt = Kt i - b w - T_friction (rotor + load reflected through the gearbox)
    dtheta/dt = w                     (motor shaft angle; output angle = theta / N)
"""
import numpy as np
import matplotlib.pyplot as plt

from common import finish, rk4_step

# ---------------------------------------------------------------- motor + gearbox parameters
R, Lm = 2.0, 1e-3          # armature resistance [ohm], inductance [H]
Kt = Ke = 0.05             # torque constant [N*m/A] = back-emf constant [V*s/rad]
N = 30                     # gear ratio
J = 1e-5 + 1e-3 / N**2     # rotor inertia + load inertia reflected to the motor [kg*m^2]
b = 1e-5                   # viscous friction [N*m*s/rad]
V_MAX = 12.0               # supply voltage [V]

# Hall-effect quadrature encoder on the motor shaft
CPR = 12                                       # cycles per motor rev
COUNTS_PER_OUT_REV = CPR * 4 * N               # x4 quadrature decoding, after the gearbox
RAD_PER_COUNT = 2 * np.pi / COUNTS_PER_OUT_REV

# PI controller on the output angle (gains chosen for ~30 rad/s crossover, see Chapter 6)
Kp, Ki = 45.0, 270.0       # [V/rad], [V/(rad*s)]


def motor(t, x, V, T_fric):
    i, w, th = x
    return np.array([(V - R * i - Ke * w) / Lm,
                     (Kt * i - b * w - T_fric * np.tanh(w / 0.5)) / J,   # smooth Coulomb friction
                     w])


def run(realistic, target_deg=90.0, t_end=1.0):
    dt_plant = 2e-5                        # plant integrated finely (electrical time constant 0.5 ms)
    Ts = 1e-3 if realistic else dt_plant   # controller sample time
    T_fric = 2e-3 if realistic else 0.0
    ref = np.radians(target_deg)

    x = np.zeros(3)
    integ, V = 0.0, 0.0
    steps_per_sample = int(round(Ts / dt_plant))
    log = {"t": [], "theta": [], "meas": [], "V": [], "i": []}
    for n in range(int(t_end / dt_plant)):
        t = n * dt_plant
        if n % steps_per_sample == 0:      # ---- controller runs here
            theta_out = x[2] / N
            meas = np.floor(theta_out / RAD_PER_COUNT) * RAD_PER_COUNT if realistic else theta_out
            e = ref - meas
            u = Kp * e + Ki * integ
            if realistic:
                V = np.clip(u, -V_MAX, V_MAX)
                if V == u or np.sign(e) != np.sign(u):   # anti-windup: stop integrating while saturated
                    integ += e * Ts
            else:
                V = u
                integ += e * Ts
        x = rk4_step(motor, t, x, dt_plant, V, T_fric)
        if n % 10 == 0:
            log["t"].append(t)
            log["theta"].append(np.degrees(x[2] / N))
            log["meas"].append(np.degrees(meas))
            log["V"].append(V)
            log["i"].append(x[0])
    return {k: np.array(v) for k, v in log.items()}


def metrics(log, target):
    th = log["theta"]
    overshoot = max(0.0, (th.max() - target) / target * 100)
    outside = np.where(np.abs(th - target) > 0.02 * target)[0]
    settle = log["t"][outside[-1]] if len(outside) else 0.0
    return overshoot, settle, th[-1] - target


ideal, real = run(False), run(True)
print(f"encoder resolution at the output shaft: {np.degrees(RAD_PER_COUNT):.3f} deg/count")
for name, lg in (("ideal", ideal), ("realistic", real)):
    os_, ts_, ess = metrics(lg, 90)
    print(f"{name:9s} overshoot {os_:5.1f}%  2% settling {ts_ * 1e3:6.0f} ms  final error {ess:+.3f} deg"
          f"  peak V {np.abs(lg['V']).max():6.1f}  peak I {np.abs(lg['i']).max():5.1f} A")

fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
axes[0].axhline(90, c="k", ls=":", label="target")
axes[0].plot(ideal["t"], ideal["theta"], label="ideal model")
axes[0].plot(real["t"], real["theta"], label="realistic model")
axes[0].set(ylabel="output angle [deg]",
            title="PM DC gear motor position control (PI) - same controller, two plant models")
axes[1].plot(ideal["t"], ideal["V"], label="ideal: voltage the controller asks for")
axes[1].plot(real["t"], real["V"], label="realistic: clipped at the 12 V supply")
axes[1].set(ylabel="motor voltage [V]", ylim=(-20, 80))
axes[2].plot(ideal["t"], ideal["i"], label="ideal")
axes[2].plot(real["t"], real["i"], label="realistic")
axes[2].set(ylabel="armature current [A]", xlabel="time [s]")
for a in axes:
    a.grid(alpha=0.3)
    a.legend(fontsize=8)
axes[0].legend(fontsize=8, loc="lower left", bbox_to_anchor=(0.3, 0.02))   # keep clear of the inset

# Zoom on the final position: the encoder only sees whole counts, so the motor rests within one count.
ins = axes[0].inset_axes([0.55, 0.12, 0.4, 0.45])
sel = real["t"] > 0.5
ins.plot(real["t"][sel], real["theta"][sel], label="true angle")
ins.step(real["t"][sel], real["meas"][sel], where="post", label="encoder reading")
ins.axhline(90, c="k", ls=":")
ins.set_title("realistic, zoomed", fontsize=8)
ins.tick_params(labelsize=7)
ins.legend(fontsize=7)
finish(fig, "04_dc_motor_position")
