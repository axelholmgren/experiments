# Yaw-correction experiment

This test answers one question: for the same observations, does the calibrated
gimbal-yaw correction reduce the angular error of the published bearing ray?
It compares the actual raw and corrected `Marker` rays, not an error inferred
afterward from a yaw value.

## Before each run

Use a known target that stays visible and whose position is available in
`evolo/odom`. The default truth is LiDAR box `0` from
`/bounding_boxes/corrected`. Verify that this ID is the same physical target as
the visual detection before trusting the result. The default correction mode is
`absolute`; it includes the documented fixture-dependent +6.12° offset.

Build and source the packages:

```bash
cd ~/code/ros2_ws
colcon build --packages-select evolo_gimbal_calibration evolo_bearing evolo_bearing_error evolo_reference_markers pointcloud_preprocessing clustering_segmentation bb_dataass_tracking
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## Rosbag replay experiment

Terminal 1 is the umbrella launch: it starts the normal marker/RViz/reference
launch and the two comparison marker nodes in parallel (one raw, one corrected).
Each comparison condition gets its own CSV logger. The LiDAR preprocessing and
tracking launches are enabled by default.

```bash
ros2 launch evolo_bearing yaw_correction_experiment.launch.py \
  use_sim_time:=true run_id:=bag_2026_09_10_absolute \
  lidar_box_id:=0
```

Terminal 2 replays the bag once:

```bash
ros2 bag play <bag-directory> --clock
```

Stop Terminal 1 after the replay. Then compare the two files named in its log
output (the expected names begin `bearing_error_bag_2026_09_10_absolute_raw_` and
`bearing_error_bag_2026_09_10_absolute_corrected_`):

```bash
cd ~/code/ros2_ws/src/evolo_bearing_tracking
python3 analysis/plot_scripts/compare_yaw_correction.py \
  results/bearing_error_bag_2026_09_10_absolute_raw_bearing_experiment_raw_marker_vs_lidar_box_0_bounding_boxes_corrected_yaw_absolute.csv \
  results/bearing_error_bag_2026_09_10_absolute_corrected_bearing_experiment_corrected_marker_vs_lidar_box_0_bounding_boxes_corrected_yaw_absolute.csv
```

Use the actual filenames printed by the logger. The terminal output reports MAE, RMSE, median absolute error, and
the paired per-sample improvement. A positive paired improvement and lower
corrected MAE/RMSE support the correction. The command writes the paired CSV
under `results/` and the plot under `results/plots/`.

**Mean Absolute Error** is the average absolute bearing error in degrees.
Lower Mean Absolute Error is better. The comparison excludes a matched pair
when either raw or corrected bearing error exceeds 80°; pass
`--max-abs-error -1` to retain all matched pairs.

## Sign check

To test the opposite correction sign without changing the LUT, set
`negate_yaw_correction:=true` and add `negated` to `run_id` and the analysis
label. The raw ray remains uncorrected; only the corrected comparison ray uses
the negated correction.

## Required experiment matrix

Run every row with the same bag once per row; do not toggle a parameter halfway
through a replay. Keep the camera target, truth source, and all transforms
unchanged within a paired run.

| Test | Yaw range / motion | Mode | What it checks |
| --- | --- | --- | --- |
| A1 | Slow sweep across -95° to +82° | `absolute` | Main default-mode test |
| A2 | Hold at -80, -45, 0, +45, +75° | `absolute` | Static errors and repeatability |
| A3 | Sweep CW, then CCW | `absolute` | Backlash / approach-direction sensitivity |
| A4 | Same as A1 after a power cycle and re-zero | `absolute` | Boot-to-boot bias robustness |
| S1 | Repeat A1 | `shape` | Shape-only comparison without fixture offset |
| O1 | Below -95° or above +82° | `absolute` | Guard check: correction should be inactive |

For each test, record target range, target ID, camera/gimbal boot state, sweep
direction, and any dropped tracking. Exclude samples with a stale or mismatched
truth source; do not use the result to judge correction if raw and corrected
rows cannot be timestamp-paired.
