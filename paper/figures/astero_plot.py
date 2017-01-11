#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import pickle
import corner
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter

import emcee3

from plot_setup import setup, get_figsize, COLORS

setup()
np.random.seed(42)

# Helpers
def format_filename(name):
    base = "astero-{0}-".format(kicid)
    return base + name + ".pdf"

kicid = 11615890
uHz_conv = 1e-6 * 24 * 60 * 60

# Save the current state of the GP and data
with open("astero-{0}.pkl".format(kicid), "rb") as f:
    gp, fit_y, freq, power_all, power_some = pickle.load(f)

backend = emcee3.backends.HDFBackend("astero-{0}.h5".format(kicid))

# Compute the relevant autocorrelation times
samples = backend.get_coords()
mean_traces = np.mean(samples[:, :, 3:5], axis=1)
tau = emcee3.autocorr.integrated_time(mean_traces, c=3, axis=0)
tau = np.max(tau)
burnin = int(10 * tau)

tau2 = emcee3.autocorr.integrated_time(mean_traces[burnin:], c=3, axis=0)
print("tau: {0}".format(tau2))
print("N_ind: {0}".format(np.prod(samples.shape[:2]) / tau2))

# Plot the traces
names = list(gp.get_parameter_names())
for i in range(len(names)):
    name = names[i].split(":")[-1]
    if name.startswith("log"):
        name = "log("+name[4:]+")"
    names[i] = name.replace("_", " ")
fig, axes = plt.subplots(samples.shape[-1] + 1, 1, sharex=True,
                         figsize=get_figsize(samples.shape[-1]//2, 2))
for i in range(samples.shape[-1]):
    axes[i].plot(samples[:, :, i], color="k", alpha=0.3, rasterized=True)
    axes[i].set_ylabel(names[i])
    axes[i].yaxis.set_major_locator(plt.MaxNLocator(5))
    axes[i].axvline(burnin, color=COLORS["MODEL_1"])

axes[-1].plot(backend.get_log_probability(), color="k", alpha=0.3,
              rasterized=True)
axes[-1].set_ylabel("log(prob)")
axes[-1].yaxis.set_major_locator(plt.MaxNLocator(5))
axes[-1].axvline(burnin, color=COLORS["MODEL_1"])

fig.savefig(format_filename("trace"))
plt.close(fig)

# Trim the burnin
samples = backend.get_coords(discard=burnin, flat=True)

# Compute the model predictions
time_grid = np.linspace(0, 1.4, 5000)
n = 1000
psds = np.empty((n, len(freq)))
acors = np.empty((n, len(time_grid)))
for i, j in enumerate(np.random.randint(len(samples), size=n)):
    s = samples[j]
    gp.set_parameter_vector(s)
    psds[i] = gp.kernel.get_psd(2*np.pi*freq)
    acors[i] = gp.kernel.get_value(time_grid)

# Plot the predictions
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=get_figsize(1, 2))

q = np.percentile(psds, [16, 50, 84], axis=0)
ax1.fill_between(freq / uHz_conv, q[0], q[2], color="k", alpha=0.3)
ax1.plot(freq / uHz_conv, q[1], "k", alpha=0.8)
ax1.set_yscale("log")
ax1.set_xlabel(r"$f\,[\mu \mathrm{Hz}]$")
ax1.set_ylabel(r"$S(f)$")

q = np.percentile(acors, [16, 50, 84], axis=0)
ax2.fill_between(time_grid * 24, q[0], q[2], color="k", alpha=0.3)
ax2.plot(time_grid * 24, q[1], "k", alpha=0.8)
ax2.set_xlabel(r"$\tau$ [hours]")
ax2.set_ylabel(r"$k(\tau)$")

fig.savefig(format_filename("model"))
plt.close(fig)

# Plot constraints on nu-max and delta-nu
s = np.exp(samples[:, 3:5])/uHz_conv
nu_max_pub = 171.94, 3.62
delta_nu_pub = 13.28, 0.29
fig = corner.corner(s, smooth=0.7, smooth1d=1.0,
                    labels=[r"$\nu_\mathrm{max}$", r"$\Delta \nu$"])
fig.axes[2].errorbar(nu_max_pub[0], delta_nu_pub[0],
                     xerr=nu_max_pub[1], yerr=delta_nu_pub[1],
                     fmt=".", color=COLORS["MODEL_1"], capsize=0,
                     lw=2, mec="none")
fig.savefig(format_filename("numax_deltanu_corner"), bbox_inches="tight")
plt.close(fig)

# Plot full corner plot
fig = corner.corner(samples, smooth=0.7, smooth1d=1.0, labels=names)
fig.savefig(format_filename("full_corner"), bbox_inches="tight")
plt.close(fig)

# Make comparison plot
fig, axes = plt.subplots(3, 1, sharex=True, figsize=get_figsize(2.5, 2))

freq_uHz = freq / uHz_conv
axes[0].plot(freq_uHz, np.sqrt(power_all), "k", alpha=0.3, rasterized=True)
axes[0].plot(freq_uHz, np.sqrt(gaussian_filter(power_all, 5)), "k",
             rasterized=True)

axes[1].plot(freq_uHz, np.sqrt(power_some), "k", alpha=0.3, rasterized=True)
axes[1].plot(freq_uHz, np.sqrt(gaussian_filter(power_some, 5)), "k",
             rasterized=True)

q = np.percentile(psds, [16, 50, 84], axis=0)
axes[2].fill_between(freq_uHz, q[0], q[2], color="k", alpha=0.3,
                     rasterized=True)
axes[2].plot(freq_uHz, q[1], "k", alpha=0.8, rasterized=True)

for ax in axes:
    ax.set_yscale("log")
    ax.set_ylim(2.0, 1e4)

axes[0].set_ylabel("periodogram; all data")
axes[1].set_ylabel("periodogram; 3\% of data")
axes[2].set_ylabel("posterior psd; 3\% of data")
axes[2].set_xlabel("frequency [$\mu$Hz]")

fig.savefig(format_filename("comparisons"), bbox_inches="tight", dpi=300)
plt.close(fig)