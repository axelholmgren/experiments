# Evolo bearing tracking

Implementation and evaluation code for the master's thesis *Uncertainty-Aware
Bearings-Only Tracking of Maritime Targets from a Hydrofoiling Unmanned Surface
Vessel*.

## Layout

- `evolo_gimbal_calibration/` — calibrated yaw correction and gimbal
  experiment assets.
- `evolo_bearing/` — bearing rays, launch files, and RViz configuration.
- `evolo_reference_markers/` — fixed and Smarcduino reference-marker nodes.
- `evolo_bearing_error/` — bearing-error geometry and CSV logger.
- `scripts/` — compatibility shell launchers.
- `analysis/` — offline plotting and analysis scripts.
- `docs/` — replay and experiment workflows.
- `results/` — generated CSV and PNG output, intentionally ignored by Git.

## Build and launch

The ROS packages live under the main workspace, so build them normally:

```bash
source /opt/ros/humble/setup.bash
source ~/code/ros2_ws/install/setup.bash

cd ~/code/ros2_ws
colcon build --packages-select evolo_gimbal_calibration evolo_bearing evolo_reference_markers evolo_bearing_error
source install/setup.bash
```

For rosbag replay:

```bash
ros2 launch evolo_bearing markers.launch.py use_sim_time:=true
ros2 bag play <bag-directory> --clock
```

The existing entry point remains available:

```bash
cd ~/code/ros2_ws/src/evolo_bearing_tracking/scripts
./launch_markers.sh
```

See `docs/rosbag_workflows.md` for the bearing-error CSV workflow.
