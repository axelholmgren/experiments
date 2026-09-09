#!/usr/bin/env python3
"""Compare logged bearing error with and without the yaw correction."""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS_DIR = Path.home() / "code/experiments/results/"
DEFAULT_CSV = "bearing_error.csv"

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bench_experiments"))
from gimbal_yaw_correction import PSI_MAX, PSI_MIN, correct_yaw  # noqa: E402


def plot_bearing_error(errors: pd.DataFrame, gimbal: pd.DataFrame, name: str,
                       out_path: Path):
    if gimbal.empty:
        raise ValueError("no gimbal_yaw_deg data in this csv")

    psi = gimbal["gimbal_yaw_deg"].to_numpy()
    raw_error = gimbal["angle_error_deg"].to_numpy()
    correction = correct_yaw(psi)
    correction_delta = np.asarray(correction.yaw_deg) - psi
    corrected_error = (raw_error - correction_delta + 180.0) % 360.0 - 180.0
    in_domain = np.asarray(correction.valid)
    magnitude_improvement = np.abs(raw_error) - np.abs(corrected_error)

    fig, (ax_yaw, ax_hist, ax_improvement) = plt.subplots(
        3, 1, figsize=(11, 11)
    )

    ax_yaw.axhline(0.0, color="0.2", linewidth=1.0)
    ax_yaw.axvspan(PSI_MIN, PSI_MAX, color="tab:green", alpha=0.08,
                   label="calibrated range")
    ax_yaw.plot(psi, raw_error, ".", color="0.55", alpha=0.45,
                markersize=3, label="raw ray")
    ax_yaw.plot(psi[in_domain], corrected_error[in_domain], ".",
                color="tab:green", alpha=0.55, markersize=3,
                label="correction applied")
    ax_yaw.set_ylabel("signed bearing error [deg]")
    ax_yaw.set_title(
        f"Raw vs yaw-corrected bearing error ({in_domain.sum()}/{len(psi)} in range)\n"
        f"{name}"
    )
    ax_yaw.legend(loc="best")

    bins = np.histogram_bin_edges(
        np.concatenate((raw_error, corrected_error)), bins=40
    )
    ax_hist.hist(raw_error, bins=bins, histtype="step", linewidth=1.8,
                 color="0.35", label=f"raw (RMS {np.std(raw_error):.2f}°)")
    ax_hist.hist(corrected_error, bins=bins, histtype="step", linewidth=1.8,
                 color="tab:green",
                 label=f"corrected (RMS {np.std(corrected_error):.2f}°)")
    ax_hist.axvline(0.0, color="0.2", linewidth=1.0)
    ax_hist.set_ylabel("sample count")
    ax_hist.set_title("Error distribution")
    ax_hist.legend(loc="best")

    ax_improvement.axhline(0.0, color="0.2", linewidth=1.0)
    ax_improvement.axvspan(PSI_MIN, PSI_MAX, color="tab:green", alpha=0.08)
    ax_improvement.plot(psi[in_domain], magnitude_improvement[in_domain], ".",
                        color="tab:green", alpha=0.55, markersize=3)
    ax_improvement.set_xlabel("raw gimbal yaw [deg]")
    ax_improvement.set_ylabel("reduction in |error| [deg]")
    ax_improvement.set_title("Positive values indicate a smaller corrected error")

    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", default=DEFAULT_CSV, help="csv name in results/")
    args = parser.parse_args()

    csv_path = RESULTS_DIR / args.csv
    errors = pd.read_csv(csv_path)
    errors["t"] = errors["t"] - errors["t"].min()  # seconds from the start of the run

    # Rows without raw GCU yaw cannot be compared with the calibration model.
    gimbal = errors.dropna(subset=["gimbal_yaw_deg"])

    print(f"samples: {len(errors)}  ({len(gimbal)} with gimbal_yaw_deg)")
    print(f"signed mean : {errors['angle_error_deg'].mean():+.2f} deg   (calibration offset)")
    print(f"median |err|: {errors['angle_error_deg'].abs().median():.2f} deg")
    print(f"median miss : {errors['miss_distance_m'].median():.1f} m")
    print()
    group_col = "track_id" if "track_id" in errors and errors["track_id"].notna().any() else "marker_id"
    print(f"{group_col:<10}{'n':>7}{'signed mean':>14}{'median |err|':>15}")
    for key, rows in errors.groupby(group_col):
        print(
            f"{key!s:<10}{len(rows):>7}{rows['angle_error_deg'].mean():>+13.2f}°"
            f"{rows['angle_error_deg'].abs().median():>14.2f}°"
        )

    plot_bearing_error(errors, gimbal, csv_path.stem, RESULTS_DIR / f"{csv_path.stem}.png")
    plt.show()


if __name__ == "__main__":
    main()
