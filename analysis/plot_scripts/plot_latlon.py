#!/usr/bin/env python3
"""Plot smarcduino vs evolo lat/long trajectories.
Reads /smarcduino/latlon data/ros_bags/rosbag2_2026_08_17-12_20_02/smarcduino_latlon.parquet from and evolo/smarc/latlon data/ros_bags/rosbag2_2026_08_17-12_20_02/evolo_smarc_latlon.parquet
Outputs
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROS_BAG = Path.home() / "code/data/ros_bags/rosbag2_2026_08_17-12_20_02"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
PLOTS_DIR = RESULTS_DIR / "plots"


def main():
    bag_dir = ROS_BAG
    smarcduino = pd.read_parquet(bag_dir / "smarcduino_latlon.parquet")
    evolo = pd.read_parquet(bag_dir / "evolo_smarc_latlon.parquet")

    plt.figure()
    plt.title(f"Latitude/Longitude Trajectory\n{bag_dir.name}")
    plt.plot(smarcduino["longitude"], smarcduino["latitude"], "-o", markersize=2, label="smarcduino")
    plt.plot(smarcduino["longitude"].iloc[0], smarcduino["latitude"].iloc[0], "*")
    plt.plot(evolo["longitude"], evolo["latitude"], "-o", markersize=2, label="evolo")
    plt.plot(evolo["longitude"].iloc[0], evolo["latitude"].iloc[0], "*")
    plt.xlabel("longitude")
    plt.ylabel("latitude")
    plt.legend()

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PLOTS_DIR / "latlon_trajectory.png"
    plt.savefig(out_path, dpi=300)
    print(f"Saved {out_path}")
    plt.show()


if __name__ == "__main__":
    main()
