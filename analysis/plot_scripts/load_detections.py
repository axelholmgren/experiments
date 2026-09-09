#!/usr/bin/env python3
"""Load a DetectionArray parquet into one row per detection.

detections is a JSON string per row (one frame), so it has to be parsed and
flattened by hand.
"""

import json
from pathlib import Path

import pandas as pd


def load_detections(
    bag_dir: Path, topic: str = "yolo_tracking", t0=None
) -> pd.DataFrame:
    yolo_tracking = pd.read_parquet(bag_dir / f"{topic}.parquet")
    if t0 is None:
        t0 = yolo_tracking["t_ns"].min()

    rows = []
    for t_ns, detections_json in zip(
        yolo_tracking["t_ns"], yolo_tracking["detections"]
    ):
        t = (t_ns - t0) / 1e9  # t in seconds
        for det in json.loads(detections_json):
            rows.append(
                {
                    "t": t,
                    "track_id": det["id"],
                    "class_id": det["class_id"],
                    "class_name": det["class_name"],
                    "score": det["score"],
                    "center_x": det["bbox"]["center"]["position"]["x"],
                    "center_y": det["bbox"]["center"]["position"]["y"],
                    "width": det["bbox"]["size"]["x"],
                    "height": det["bbox"]["size"]["y"],
                }
            )
    return pd.DataFrame(rows)
