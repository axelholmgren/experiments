#!/usr/bin/env python3
"""Plot YOLOE tracking over time.
Each row is a yolo_msgs/msg/DetectionArray with class_id, class_name, score, id, bbox: {"center{"position}}
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

from load_detections import load_detections

BAGS_DIR = Path.home() / "code/data/ros_bags"
ROS_BAG = BAGS_DIR / "rosbag2_2026_08_17-12_20_02"
RESULTS_DIR = Path.home() / "code/experiments/results/"


# def load_detections(bag_dir: Path) -> pd.DataFrame:
#     yolo_tracking = pd.read_parquet(bag_dir / "yolo_tracking.parquet")
#     t0 = yolo_tracking["t_ns"].min()

#     # detections is a JSON string per row, reconstrcting into a pd.Dataframe
#     rows = []
#     for t_ns, detections_json in zip(
#         yolo_tracking["t_ns"], yolo_tracking["detections"]
#     ):
#         t = (t_ns - t0) / 1e9  # t in seconds
#         for det in json.loads(detections_json):
#             rows.append(
#                 {
#                     "t": t,
#                     "track_id": det["id"],
#                     "class_id": det["class_id"],
#                     "class_name": det["class_name"],
#                     "score": det["score"],
#                     "center_x": det["bbox"]["center"]["position"]["x"],
#                     "center_y": det["bbox"]["center"]["position"]["y"],
#                     "width": det["bbox"]["size"]["x"],
#                     "height": det["bbox"]["size"]["y"],
#                 }
#             )
#     return pd.DataFrame(rows)


def add_gimbal_mode(target: pd.DataFrame, bag_dir: Path, t0) -> pd.DataFrame:
    """Tag each target frame with the gimbal mode in effect at that time.

    The gimbal only follows the target in IMG_POI mode; in OFF / RPY /
    GEOPOINT / ODOM_POI it is pointing at something else.
    """
    fb = pd.read_parquet(
        bag_dir / "evolo_gimbal_camera_gimbal_fb.parquet", columns=["t_ns", "gimbal_mode"]
    )
    fb["t"] = (fb["t_ns"] - t0) / 1e9
    return pd.merge_asof(
        target.sort_values("t"), fb[["t", "gimbal_mode"]].sort_values("t"), on="t"
    )


def plot_track_timeline(
    dets: pd.DataFrame, target: pd.DataFrame, bag_dir: Path, out_path: Path
):
    spans = dets.groupby("track_id").agg(
        t_min=("t", "min"), t_max=("t", "max"), class_name=("class_name", "first")
    )
    spans = spans.sort_values("t_min")

    classes = sorted(spans["class_name"].unique())
    colors = {cls: color for cls, color in zip(classes, plt.get_cmap("tab10").colors)}

    plt.figure(figsize=(10, max(4, 0.18 * len(spans))))
    plt.title(f"Track Timeline\n{bag_dir.name}")
    for row_idx, (track_id, row) in enumerate(spans.iterrows()):
        plt.barh(
            row_idx,
            row["t_max"] - row["t_min"],
            left=row["t_min"],
            color=colors[row["class_name"]],
        )
    # mark when each track was the target yolo_action locked onto (yolo_target),
    # red while the gimbal was actually slewing to it (GIMBAL_MODE_IMG_POI),
    # black while it was selected but the gimbal was in some other mode
    row_of = {track_id: i for i, track_id in enumerate(spans.index)}
    is_target = target[target["track_id"].isin(row_of)]
    followed = is_target["gimbal_mode"] == "IMG_POI"
    for mask, color in [(~followed, "black"), (followed, "red")]:
        plt.scatter(
            is_target["t"][mask],
            is_target["track_id"][mask].map(row_of),
            marker="|",
            color=color,
            s=8,
        )

    plt.yticks(range(len(spans)), spans.index)
    plt.xlabel("time [s]")
    plt.ylabel("track id")
    handles = [patches.Rectangle((0, 0), 1, 1, color=colors[cls]) for cls in classes]
    for color in ["black", "red"]:
        handles.append(plt.Line2D([], [], marker="|", color=color, linestyle="none"))
    plt.legend(handles, classes + ["target (selected)", "target (gimbal tracking)"])
    plt.tight_layout()

    plt.savefig(out_path)
    print(f"Saved {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag", nargs="?", default=ROS_BAG.name, help="bag dir name")
    args = parser.parse_args()

    bag_dir = BAGS_DIR / args.bag
    t0 = pd.read_parquet(bag_dir / "yolo_tracking.parquet", columns=["t_ns"])["t_ns"].min()
    dets = load_detections(bag_dir, t0=t0)
    target = load_detections(bag_dir, "yolo_target", t0=t0)
    target = add_gimbal_mode(target, bag_dir, t0)
    plot_track_timeline(
        dets, target, bag_dir, RESULTS_DIR / f"track_timeline_{args.bag}.png"
    )
    plt.show()


if __name__ == "__main__":
    main()
