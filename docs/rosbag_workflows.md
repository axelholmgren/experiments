# Rosbag bearing workflow

Build the bearing packages once after changing their nodes or launch files:

```bash
cd ~/code/ros2_ws
colcon build --packages-select evolo_gimbal_calibration evolo_bearing evolo_reference_markers evolo_bearing_error
```

For a replay, source the main workspace and launch the normal detected-target
ray without selected track IDs:

```bash
source /opt/ros/humble/setup.bash
source ~/code/ros2_ws/install/setup.bash

ros2 launch evolo_bearing markers.launch.py use_sim_time:=true track_ids:="[]"
```

In a second terminal, replay the bag with ROS time:

```bash
ros2 bag play <bag-directory> --clock
```

The normal ray is `/evolo/gimbal_camera/target_bearing_marker`.  The optional
selected-ID ray is `/evolo/gimbal_camera/selected_bearing_marker`.

For an offline yaw comparison, record one run with correction disabled:

```bash
ros2 param set /bearing_ray_node apply_yaw_correction false
ros2 run evolo_bearing_error bearing_error_node --ros-args \
  -p use_sim_time:=true \
  -p bag:=rosbag2_YYYY_MM_DD-HH_MM_SS_raw_yaw
```

The plot script calculates the calibrated correction from this raw CSV only
within `[-95, +82]` degrees.  It does not require a second corrected run.
