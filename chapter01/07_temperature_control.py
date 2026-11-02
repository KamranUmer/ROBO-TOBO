"""
Problem 1.3(a) - Temperature control system.

Purpose: keep a room at a set temperature.
    Sensor   : thermistor / RTD, modeled as a first-order lag (it takes time to warm up)
    Actuator : 2 kW electric heater switched by a relay (on/off)
    Process  : room thermal model   C dT/dt = Q_heater - (T - T_outside) / R_th
    Control  : thermostat with a hysteresis band

We compare a hysteresis band of 0 (relay chatters, wearing it out) with a 1 degC band.
"""
import numpy as np
import matplotlib.pyplot as plt

from common import finish

C_room = 2e5          # thermal capacitance [J/K]
R_th = 0.01           # thermal resistance to outside [K/W]  (100 W lost per degC difference)
Q_heater = 2000.0     # heater power [W]
T_out = 5.0           # outside temperature [degC]
tau_sensor = 60.0     # sensor time constant [s]
T_set = 21.0


def simulate(band, hours=4.0, dt=1.0):
    n = int(hours * 3600 / dt)
    T, Ts, on = 12.0, 12.0, False
    log = np.zeros((n, 4))
    switches = 0
    for k in range(n):
        # thermostat: turn on below (set - band/2), off above (set + band/2)
        was_on = on
        if Ts < T_set - band / 2:
            on = True
        elif Ts > T_set + band / 2:
            on = False
        switches += on != was_on
        Q = Q_heater if on else 0.0
        T += dt * (Q - (T - T_out) / R_th) / C_room
        Ts += dt * (T - Ts) / tau_sensor
        log[k] = (k * dt / 3600, T, Ts, on)
    return log, switches


fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
for band, ax in zip((0.0, 1.0), axes):
    log, switches = simulate(band)
    steady = log[:, 0] > 1.5
    energy_kwh = log[:, 3].sum() * Q_heater / 3.6e6
    print(f"band {band:.1f} degC: {switches:4d} relay switches, "
          f"room temperature after warm-up {log[steady, 1].min():.2f} to {log[steady, 1].max():.2f} degC, "
          f"energy used {energy_kwh:.2f} kWh")
    ax.plot(log[:, 0], log[:, 1], label="room temperature")
    ax.plot(log[:, 0], log[:, 2], "--", label="sensor reading (lags)")
    ax.axhline(T_set, c="k", ls=":", label="set point")
    ax.fill_between(log[:, 0], 10, 10 + 2 * log[:, 3], step="post", alpha=0.3, color="tab:red", label="heater on")
    ax.set(title=f"Hysteresis band = {band} degC -> {switches} relay switches in 4 h",
           ylabel="temperature [degC]", ylim=(10, 24))
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
axes[-1].set_xlabel("time [h]")
finish(fig, "07_temperature_control")
