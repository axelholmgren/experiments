#!/usr/bin/env python3
"""Pair raw and corrected bearing-error CSVs and report whether correction helps."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load(path: Path, condition: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    required = {"t", "angle_error_deg"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    data = data.dropna(subset=["t", "angle_error_deg"]).copy()
    data["condition"] = condition
    # IDs let selected-ray runs avoid matching two different targets.  The
    # ordinary one-ray marker has neither, so use one common group for it.
    if "track_id" in data and data["track_id"].notna().any():
        data["group"] = "track:" + data["track_id"].fillna("").astype(str)
    elif "marker_id" in data:
        data["group"] = "marker:" + data["marker_id"].astype(str)
    else:
        data["group"] = "all"
    return data.sort_values("t")


def pair(raw: pd.DataFrame, corrected: pd.DataFrame, tolerance: float) -> pd.DataFrame:
    pairs = []
    for group in sorted(set(raw.group) & set(corrected.group)):
        left = raw[raw.group == group].sort_values("t").reset_index(drop=True)
        right = corrected[corrected.group == group].sort_values("t").reset_index(drop=True)
        right_times = right.t.to_numpy()
        used_right = set()
        # merge_asof can match one corrected sample to many raw samples.  That
        # distorts the mean with repeated camera frames, so choose the closest
        # eligible counterpart once and retire it from the candidate set.
        for _, raw_row in left.iterrows():
            first = np.searchsorted(right_times, raw_row.t - tolerance, side="left")
            last = np.searchsorted(right_times, raw_row.t + tolerance, side="right")
            candidates = list(range(first, last))
            candidates = [
                i for i in candidates
                if 0 <= i < len(right) and i not in used_right
            ]
            if not candidates:
                continue
            right_index = min(candidates, key=lambda i: abs(right_times[i] - raw_row.t))
            used_right.add(right_index)
            corrected_row = right.iloc[right_index]
            pairs.append({
                "group": group,
                "t_raw": raw_row.t,
                "t_corrected": corrected_row.t,
                "time_difference_s": corrected_row.t - raw_row.t,
                "angle_error_deg_raw": raw_row.angle_error_deg,
                "angle_error_deg_corrected": corrected_row.angle_error_deg,
                "gimbal_yaw_deg": raw_row.get("gimbal_yaw_deg", np.nan),
            })
    if not pairs:
        raise ValueError("no samples matched; check target IDs and replay clock")
    result = pd.DataFrame(pairs)
    result["abs_error_raw_deg"] = result.angle_error_deg_raw.abs()
    result["abs_error_corrected_deg"] = result.angle_error_deg_corrected.abs()
    result["improvement_deg"] = (
        result.abs_error_raw_deg - result.abs_error_corrected_deg
    )
    return result


def metrics(values: pd.Series) -> tuple[float, float, float]:
    return values.abs().mean(), np.sqrt(np.mean(values ** 2)), values.abs().median()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_csv", type=Path)
    parser.add_argument("corrected_csv", type=Path)
    parser.add_argument("--match-tolerance", type=float, default=0.08,
                        help="maximum raw/corrected timestamp difference [s]")
    parser.add_argument(
        "--max-abs-error", type=float, default=80.0,
        help=("exclude a matched pair if either |bearing error| exceeds this "
              "many degrees; use a negative value to disable (default: %(default)s)"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/plots"),
        help="directory for the PNG plot (default: %(default)s)",
    )
    parser.add_argument(
        "--paired-output-dir", type=Path, default=Path("results"),
        help="directory for the paired CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--label", default="yaw_correction_comparison",
        help="short basename for the paired CSV and plot (default: %(default)s)",
    )
    args = parser.parse_args()

    pairs = pair(load(args.raw_csv, "raw"), load(args.corrected_csv, "corrected"),
                 args.match_tolerance)
    matched_count = len(pairs)
    if args.max_abs_error >= 0:
        pairs = pairs[
            (pairs.angle_error_deg_raw.abs() <= args.max_abs_error)
            & (pairs.angle_error_deg_corrected.abs() <= args.max_abs_error)
        ].copy()
    if pairs.empty:
        raise ValueError("no matched pairs remain after the bearing-error filter")
    raw_mae, raw_rmse, raw_median = metrics(pairs.angle_error_deg_raw)
    corr_mae, corr_rmse, corr_median = metrics(pairs.angle_error_deg_corrected)
    improvement = pairs.improvement_deg
    print(f"matched pairs: {len(pairs)} of {matched_count}")
    if args.max_abs_error >= 0:
        print(f"filter: both |bearing errors| ≤ {args.max_abs_error:g} deg")
    print("                    raw       corrected       change")
    print(f"Mean Absolute Error [deg] {raw_mae:8.3f}    {corr_mae:8.3f}    {corr_mae - raw_mae:+8.3f}")
    print(f"RMSE [deg]       {raw_rmse:8.3f}    {corr_rmse:8.3f}    {corr_rmse - raw_rmse:+8.3f}")
    print(f"median |e| [deg] {raw_median:8.3f}    {corr_median:8.3f}    {corr_median - raw_median:+8.3f}")
    print(f"paired improvement: mean {improvement.mean():+.3f} deg; "
          f"improved samples {(improvement > 0).mean() * 100:.1f}%")
    print("MAE = Mean Absolute Error: the average |bearing error|; lower is better.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.paired_output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.label).name
    paired_csv_path = args.paired_output_dir / f"{stem}_paired.csv"
    plot_path = args.output_dir / f"{stem}.png"
    pairs.to_csv(paired_csv_path, index=False)
    fig, axes = plt.subplots(3, 1, figsize=(11, 11))
    yaw = pd.to_numeric(pairs.gimbal_yaw_deg, errors="coerce").to_numpy()
    has_yaw = np.isfinite(yaw)
    if has_yaw.any():
        # This is the yaw/error panel from plot_bearing_error.py, except the
        # two series are independently measured rays from the same replay.
        axes[0].axhline(0, color="0.2", lw=1)
        axes[0].axvspan(-95, 82, color="tab:green", alpha=.08,
                        label="calibrated range")
        axes[0].plot(yaw[has_yaw], pairs.angle_error_deg_raw[has_yaw], ".",
                     color="0.55", alpha=.45, markersize=3, label="raw ray")
        axes[0].plot(yaw[has_yaw], pairs.angle_error_deg_corrected[has_yaw], ".",
                     color="tab:green", alpha=.55, markersize=3,
                     label="corrected ray")
        axes[0].set(xlabel="raw gimbal yaw [deg]", ylabel="signed bearing error [deg]",
                    title="Raw and corrected bearing error versus gimbal yaw")
        axes[0].legend(loc="best")
    else:
        axes[0].text(.5, .5, "No gimbal_yaw_deg column available",
                     ha="center", va="center", transform=axes[0].transAxes)
        axes[0].set_axis_off()

    bins = np.histogram_bin_edges(
        np.r_[pairs.angle_error_deg_raw, pairs.angle_error_deg_corrected], bins=40
    )
    axes[1].hist(pairs.angle_error_deg_raw, bins=bins, histtype="step", lw=1.8,
                 label=f"raw (Mean Absolute Error {raw_mae:.2f}°)")
    axes[1].hist(pairs.angle_error_deg_corrected, bins=bins, histtype="step", lw=1.8,
                 label=f"corrected (Mean Absolute Error {corr_mae:.2f}°)")
    axes[1].axvline(0, color="0.2", lw=1)
    axes[1].set(xlabel="signed bearing error [deg]", ylabel="sample count")
    axes[1].legend()
    axes[2].hist(improvement, bins=40, color="tab:green", alpha=.75)
    axes[2].axvline(0, color="0.2", lw=1)
    axes[2].set(xlabel="|raw error| − |corrected error| [deg]", ylabel="matched pairs",
                title="Positive means the correction helped")
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150)
    print(f"paired CSV: {paired_csv_path}")
    print(f"plot: {plot_path}")


if __name__ == "__main__":
    main()
