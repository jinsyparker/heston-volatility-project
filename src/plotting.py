"""Plotting utilities for the project notebooks."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "heston_matplotlib_cache"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline, griddata


def ensure_dir(path: str | Path) -> Path:
    """Create and return a directory path."""
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def fit_iv_surface(
    df: pd.DataFrame,
    outdir: str | Path = "reports/figures",
    smoothing: float = 0.01,
) -> pd.DataFrame:
    """Fit a smooth IV curve by expiry and save per-expiry plots."""
    out = ensure_dir(outdir)
    records = []

    for expiry, sub in df.groupby("expiry"):
        sub = sub.dropna(subset=["moneyness", "iv_clamped"]).sort_values("moneyness")
        if len(sub) < 6:
            continue
        x = sub["moneyness"].to_numpy(dtype=float)
        y = sub["iv_clamped"].to_numpy(dtype=float)
        unique_x, idx = np.unique(x, return_index=True)
        unique_y = y[idx]
        if len(unique_x) < 4:
            continue

        try:
            spline = UnivariateSpline(unique_x, unique_y, s=smoothing, k=3)
        except Exception:
            spline = UnivariateSpline(unique_x, unique_y, s=max(smoothing, 0.1), k=1)

        grid = np.linspace(unique_x.min(), unique_x.max(), 120)
        fitted = spline(grid)
        if np.isnan(fitted).any():
            continue

        records.append(
            pd.DataFrame(
                {
                    "expiry": pd.to_datetime(expiry),
                    "T": float(sub["T"].iloc[0]),
                    "moneyness": grid,
                    "iv_fit": fitted,
                }
            )
        )

        plt.figure(figsize=(7, 4))
        plt.scatter(x, y, s=12, alpha=0.45, label="Market IV")
        plt.plot(grid, fitted, linewidth=2, label="Smoothed fit")
        plt.axvline(1.0, linestyle="--", linewidth=0.8)
        plt.title(f"IV smile fit - {pd.to_datetime(expiry).date()}")
        plt.xlabel("Moneyness (K/S0)")
        plt.ylabel("Implied volatility")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out / f"iv_fit_{pd.to_datetime(expiry).date()}.png", dpi=220)
        plt.close()

    if not records:
        raise RuntimeError("No IV fits were produced.")
    return pd.concat(records, ignore_index=True)


def plot_iv_surface(iv_fit_df: pd.DataFrame, outdir: str | Path = "reports/figures") -> None:
    """Save 3D and contour plots of a fitted IV surface."""
    out = ensure_dir(outdir)
    t_vals = iv_fit_df["T"].to_numpy(dtype=float)
    m_vals = iv_fit_df["moneyness"].to_numpy(dtype=float)
    iv_vals = iv_fit_df["iv_fit"].to_numpy(dtype=float)

    t_grid, m_grid = np.mgrid[t_vals.min() : t_vals.max() : 40j, m_vals.min() : m_vals.max() : 80j]
    iv_grid = griddata((t_vals, m_vals), iv_vals, (t_grid, m_grid), method="cubic")

    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(t_grid, m_grid, iv_grid, cmap="viridis", linewidth=0, antialiased=True)
    ax.set_xlabel("Maturity T")
    ax.set_ylabel("Moneyness K/S0")
    ax.set_zlabel("IV")
    ax.set_title("Smoothed implied-volatility surface")
    plt.tight_layout()
    plt.savefig(out / "iv_surface_3d.png", dpi=250)
    plt.close()

    plt.figure(figsize=(7.5, 4.5))
    contour = plt.contourf(t_grid, m_grid, iv_grid, levels=14)
    plt.xlabel("Maturity T")
    plt.ylabel("Moneyness K/S0")
    plt.title("Smoothed implied-volatility surface")
    cbar = plt.colorbar(contour)
    cbar.set_label("IV")
    plt.tight_layout()
    plt.savefig(out / "iv_surface_contour.png", dpi=250)
    plt.close()


def plot_heston_fit(strikes, target_iv, model_iv, expiry, outdir: str | Path = "reports/figures") -> None:
    """Plot calibrated Heston IVs against the target smile."""
    out = ensure_dir(outdir)
    plt.figure(figsize=(8, 4.8))
    plt.plot(strikes, target_iv, "o-", label="Target market smile")
    plt.plot(strikes, model_iv, "x--", label="Calibrated Heston MC")
    plt.title(f"Heston calibration - {pd.to_datetime(expiry).date()}")
    plt.xlabel("Strike")
    plt.ylabel("Implied volatility")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(out / f"heston_fit_{pd.to_datetime(expiry).date()}.png", dpi=250)
    plt.close()
