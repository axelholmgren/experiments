#!/usr/bin/env python3
"""PROTOTYPE: plot manual screen readings beside the matching logged data.

This is a time-alignment and sign-convention check, not a hand audit.  The
manual file has no LiDAR truth or world-frame boresight, so this plot must not
be interpreted as hand-derived correction points on the correction LUT.
"""

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HFOV_DEG = 57.1
SCREEN_WIDTH_MM = 205.0
CROSSHAIR_MM = SCREEN_WIDTH_MM / 2.0
MATCH_TOLERANCE_S = 0.080

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HAND_DATA = (
    REPOSITORY_ROOT / "evolo_gimbal_calibration/experiment_data/hand_derived bearing angles.md"
)
DEFAULT_LOGGED_CSV = (
    REPOSITORY_ROOT / "results/bearing_error_rosbag2_2026_08_17-12_20_02_yaw_correction.csv"
)
DEFAULT_OUTPUT = REPOSITORY_ROOT / "results/plots/hand_derived_bearing_demo.png"

ROW = re.compile(
    r"^\|\s*(?P<screen>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"(?P<gimbal>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"(?P<elapsed>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"(?P<time>-?\d+(?:\.\d+)?)\s*\|\s*$"
)


def load_manual_measurements(path: Path) -> pd.DataFrame:
    """Read the numeric rows of the small Markdown measurement table."""
    records = []
    for line in path.read_text().splitlines():
        match = ROW.match(line)
        if match:
            records.append({key: float(value) for key, value in match.groupdict().items()})
    if not records:
        raise ValueError(f"no measurement rows found in {path}")
    data = pd.DataFrame(records).rename(columns={"time": "time_ros_s"})
    data["manual_raw_gimbal_yaw_deg"] = -data["gimbal"]
    data["image_angle_deg"] = -(
        (data["screen"] - CROSSHAIR_MM) / SCREEN_WIDTH_MM * HFOV_DEG
    )
    return data.sort_values("time_ros_s")


def nearest_logged_rows(manual: pd.DataFrame, logged_path: Path) -> pd.DataFrame:
    """Pair each manual timestamp once with its closest logged sample."""
    logged = pd.read_csv(logged_path).sort_values("t")
    required = {"t", "gimbal_yaw_deg", "corrected_yaw_deg", "angle_error_deg"}
    missing = required - set(logged.columns)
    if missing:
        raise ValueError(f"{logged_path} is missing {sorted(missing)}")
    pairs = pd.merge_asof(
        manual,
        logged[list(required)].sort_values("t"),
        left_on="time_ros_s",
        right_on="t",
        direction="nearest",
        tolerance=MATCH_TOLERANCE_S,
    )
    pairs["match_delta_ms"] = (pairs["time_ros_s"] - pairs["t"]).abs() * 1000.0
    return pairs


def plot(pairs: pd.DataFrame, output: Path, show: bool) -> None:
    relative_time = pairs["time_ros_s"] - pairs["time_ros_s"].min()
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(11, 9))

    axes[0].plot(relative_time, pairs["manual_raw_gimbal_yaw_deg"], "o",
                 label="manual gimbal yaw (sign normalized)")
    axes[0].plot(relative_time, pairs["gimbal_yaw_deg"], "x",
                 label="nearest logged raw gimbal yaw")
    axes[0].plot(relative_time, pairs["corrected_yaw_deg"], ".",
                 label="nearest logged corrected yaw")
    axes[0].set_ylabel("yaw [deg]")
    axes[0].set_title("Prototype: manual readings aligned to logged yaw data")
    axes[0].legend(loc="best")

    axes[1].axhline(0.0, color="0.35", linewidth=0.8)
    axes[1].plot(relative_time, pairs["image_angle_deg"], "o-", color="tab:purple")
    axes[1].set_ylabel("image angle [deg]")
    axes[1].set_title("Screen-derived horizontal image angle")

    axes[2].axhline(0.0, color="0.35", linewidth=0.8)
    axes[2].plot(relative_time, pairs["angle_error_deg"], "o-", color="tab:red")
    axes[2].set(xlabel="seconds from first manual reading",
                ylabel="logged error [deg]",
                title="Logged ray-minus-LiDAR-truth error (not a hand correction)")

    for axis in axes:
        axis.grid(alpha=0.25)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved {output}")
    if show:
        plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hand-data", type=Path, default=DEFAULT_HAND_DATA)
    parser.add_argument("--logged-csv", type=Path, default=DEFAULT_LOGGED_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    pairs = nearest_logged_rows(load_manual_measurements(args.hand_data), args.logged_csv)
    print(pairs[["time_ros_s", "manual_raw_gimbal_yaw_deg", "gimbal_yaw_deg",
                 "image_angle_deg", "match_delta_ms"]].to_string(index=False))
    unmatched = pairs["t"].isna().sum()
    if unmatched:
        print(f"Warning: {unmatched} manual row(s) have no logged match within 80 ms")
    plot(pairs, args.output, args.show)


if __name__ == "__main__":
    main()
