#!/usr/bin/env bash
# Compatibility wrapper for the installed ROS 2 launch file.
#
# Build once after changing nodes or launch/config files:
#   cd ~/code/ros2_ws && colcon build --packages-select evolo_gimbal_calibration evolo_bearing evolo_reference_markers
#
# Optional environment variables:
#   SIM_TIME=true                 # default; use with `ros2 bag play --clock`
#   TRACK_IDS='[44,68,99]'        # default is empty: no selected-ID rays
#
# An optional first argument remains an RViz config path.  A bare name is
# resolved from ~/.rviz2 for compatibility with the old script.

SIM_TIME="${SIM_TIME:-true}"
TRACK_IDS="${TRACK_IDS:-}"

source /opt/ros/humble/setup.bash
source "$HOME/code/ros2_ws/install/setup.bash"

if ! ros2 pkg prefix evolo_bearing >/dev/null 2>&1; then
    echo "evolo_bearing is not built. Run:" >&2
    echo "  cd $HOME/code/ros2_ws && colcon build --packages-select evolo_gimbal_calibration evolo_bearing evolo_reference_markers" >&2
    exit 1
fi

LAUNCH_ARGS=("use_sim_time:=$SIM_TIME" "track_ids:=$TRACK_IDS")
if [[ -n "${1:-}" ]]; then
    RVIZ_CONFIG="$1"
    [[ "$RVIZ_CONFIG" == */* ]] || RVIZ_CONFIG="$HOME/.rviz2/$RVIZ_CONFIG"
    if [[ ! -f "$RVIZ_CONFIG" ]]; then
        echo "no such rviz config: $RVIZ_CONFIG" >&2
        exit 1
    fi
    LAUNCH_ARGS+=("rviz_config:=$RVIZ_CONFIG")
fi

exec ros2 launch evolo_bearing markers.launch.py "${LAUNCH_ARGS[@]}"
