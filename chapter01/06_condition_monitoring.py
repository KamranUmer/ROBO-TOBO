"""
Sections 1.5.1-1.5.2 - Condition monitoring with vibration.

The book says the vibration frequency spectrum of a ball bearing tells a good bearing from
a defective one: "the level of vibrations and presence of additional peaks are an
indication of defects". We simulate an accelerometer on a bearing housing:

    healthy : shaft unbalance at 1x running speed + 2x (misalignment) + noise
    faulty  : the same + an outer-race crack. Every time a ball rolls over the crack it
              produces a short impact that rings the housing at its resonance (~3 kHz).
              The impacts repeat at the Ball Pass Frequency of the Outer race (BPFO).

Then we compute the usual condition indicators: RMS, kurtosis, FFT spectrum, and the
envelope spectrum (the standard trick for finding bearing faults).
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert, butter, sosfiltfilt
from scipy.stats import kurtosis

from common import finish

fs = 20_000                     # accelerometer sample rate [Hz]
t = np.arange(0, 1.0, 1 / fs)
rpm = 1800
fr = rpm / 60                   # shaft frequency [Hz]

# Bearing geometry (typical 6205 deep-groove ball bearing)
n_balls, d_ball, D_pitch, phi = 9, 7.94, 39.04, 0.0
BPFO = n_balls / 2 * fr * (1 - d_ball / D_pitch * np.cos(phi))
print(f"shaft {fr:.1f} Hz, BPFO = {BPFO:.1f} Hz")

rng = np.random.default_rng(0)
base = 0.5 * np.sin(2 * np.pi * fr * t) + 0.2 * np.sin(2 * np.pi * 2 * fr * t + 0.4)
healthy = base + 0.3 * rng.standard_normal(t.size)

f_res, zeta = 3000.0, 0.05
impulse = np.zeros_like(t)
impact_times = np.arange(0, 1.0, 1 / BPFO)
impact_times += rng.normal(0, 2e-5, impact_times.size)      # balls slip a little, so impacts are not perfectly periodic
impulse[np.clip(impact_times * fs, 0, t.size - 1).astype(int)] = 1.0
tr = np.arange(0, 0.01, 1 / fs)
ring = np.exp(-zeta * 2 * np.pi * f_res * tr) * np.sin(2 * np.pi * f_res * tr)
faulty = healthy + 3.0 * np.convolve(impulse, ring)[: t.size]


def spectrum(x):
    X = np.abs(np.fft.rfft(x * np.hanning(x.size))) * 2 / x.size * 2
    return np.fft.rfftfreq(x.size, 1 / fs), X


def envelope_spectrum(x):
    sos = butter(4, [2000, 4000], btype="bandpass", fs=fs, output="sos")   # isolate the resonance band
    env = np.abs(hilbert(sosfiltfilt(sos, x)))
    return spectrum(env - env.mean())


print(f"{'':8s} {'RMS':>6s} {'kurtosis':>9s}")
for name, x in (("healthy", healthy), ("faulty", faulty)):
    print(f"{name:8s} {np.sqrt(np.mean(x**2)):6.3f} {kurtosis(x, fisher=False):9.2f}   (kurtosis ~3 = Gaussian, >4 = impacts)")

fig, axes = plt.subplots(3, 2, figsize=(14, 9))
for col, (name, x) in enumerate((("Healthy bearing", healthy), ("Outer-race defect", faulty))):
    seg = t < 0.1
    axes[0, col].plot(t[seg] * 1e3, x[seg], lw=0.7)
    axes[0, col].set(title=f"{name}: accelerometer signal", xlabel="time [ms]", ylabel="accel [g]", ylim=(-3, 3))

    f, X = spectrum(x)
    axes[1, col].plot(f, X, lw=0.7)
    axes[1, col].set(title="FFT spectrum", xlabel="frequency [Hz]", ylabel="amplitude", xlim=(0, 5000))

    f, E = envelope_spectrum(x)
    axes[2, col].plot(f, E, lw=0.9)
    for h in range(1, 5):
        axes[2, col].axvline(h * BPFO, c="r", ls="--", alpha=0.4)
    axes[2, col].set(title="Envelope spectrum (red = BPFO harmonics)", xlabel="frequency [Hz]",
                     ylabel="amplitude", xlim=(0, 500), ylim=(0, 0.15))
for a in axes.flat:
    a.grid(alpha=0.3)
finish(fig, "06_condition_monitoring")
