#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from celerite.plot_setup import setup, get_figsize, COLOR_CYCLE
setup(auto=True)

parser = argparse.ArgumentParser()
parser.add_argument("platform")
parser.add_argument("--default", action="store_true")
parser.add_argument("--sparse", action="store_true")
parser.add_argument("--directory",
                    default=os.path.dirname(os.path.abspath(__file__)))
args = parser.parse_args()

# Compile into a matrix
lapack = False
if args.default:
    fn = os.path.join(args.directory,
                      "benchmark_{0}_default.csv".format(args.platform))
elif args.sparse:
    fn = os.path.join(args.directory,
                      "benchmark_{0}_sparse.csv".format(args.platform))
else:
    lapack = True
    fn = os.path.join(args.directory,
                      "benchmark_{0}.csv".format(args.platform))
    without_lapack = pd.read_csv(fn, comment="#")
    fn = os.path.join(args.directory,
                      "benchmark_{0}_lapack.csv".format(args.platform))
with_lapack = pd.read_csv(fn, comment="#")

with_lapack_matrix = np.empty((with_lapack.xi.max() + 1,
                               with_lapack.yi.max() + 1))
with_lapack_matrix[:] = np.nan
with_lapack_matrix[with_lapack.xi, with_lapack.yi] = with_lapack.comp_time

if lapack:
    without_lapack_matrix = np.empty((without_lapack.xi.max() + 1,
                                      without_lapack.yi.max() + 1))
    without_lapack_matrix[:] = np.nan
    without_lapack_matrix[without_lapack.xi, without_lapack.yi] = \
        without_lapack.comp_time

J = np.sort(np.array(with_lapack.j.unique()))
N = np.sort(np.array(with_lapack.n.unique()))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=get_figsize(1, 2), sharey=True)

for i, j in enumerate(J):
    x = N
    y = with_lapack_matrix[i]
    m = np.isfinite(y)
    ax1.plot(x[m], y[m], ".-", color=COLOR_CYCLE[i],
             label="{0:.0f}".format(j))

    if lapack:
        y = without_lapack_matrix[i]
        m = np.isfinite(y)
        ax1.plot(x[m], y[m], ".--", color=COLOR_CYCLE[i])

ax1.plot(N, 9e-2 * N / N[-1], "k", label=r"$\mathcal{O}(N)$")
ax1.legend(loc="lower right", bbox_to_anchor=(1.05, 0), fontsize=8)

for i, n in enumerate(N[::2]):
    x = J
    y = with_lapack_matrix[:, 2*i]
    m = np.isfinite(y)
    ax2.plot(x[m], y[m], ".-", color=COLOR_CYCLE[i % len(COLOR_CYCLE)],
             label="{0:.0f}".format(n))

    if lapack:
        y = without_lapack_matrix[:, 2*i]
        m = np.isfinite(y)
        ax2.plot(x[m], y[m], ".--", color=COLOR_CYCLE[i % len(COLOR_CYCLE)])
ax2.plot(J, 0.5 * J**2 / J[-1]**2, "k",
         label=r"$\mathcal{O}(J^2)$")
ax2.legend(loc="lower right", bbox_to_anchor=(1.05, 0), fontsize=8)


ax1.set_xscale("log")
ax2.set_xscale("log")
ax1.set_yscale("log")
ax1.set_xlim(N.min(), N.max())
ax2.set_xlim(1, J.max())
ax2.set_ylim(2e-5, 8.0)

ax1.set_ylabel("computational cost [seconds]")
ax1.set_xlabel("number of data points [$N$]")
ax2.set_xlabel("number of terms [$J$]")

fn = os.path.join(args.directory, "benchmark_{0}".format(args.platform))
if args.default:
    fn += "_default"
elif args.sparse:
    fn += "_sparse"
fig.savefig(fn + ".png", bbox_inches="tight", dpi=300)
fig.savefig(fn + ".pdf", bbox_inches="tight", dpi=300)
