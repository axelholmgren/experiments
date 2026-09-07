#!/usr/bin/env bash
# Launch the marker nodes and rviz. Ctrl-C stops all of them.
#
# Set SIM_TIME=true when replaying a bag with `ros2 bag play --clock`:
#     SIM_TIME=true ./launch_markers.sh
#
# Pass another rviz config as the first argument (a bare name is looked up in
# ~/.rviz2), otherwise DEFAULT_CONFIG below is used:
#     ./launch_markers.sh some_other.rviz
#
# Track ids are per bag, so set them for the bag being replayed:
#     TRACK_IDS=[44,68,99] ./launch_markers.sh

DEFAULT_CONFIG="tracking_ray_evolo_smarcduino.rviz"

SCRIPTS="$(dirname "$(realpath "$0")")"
SIM_TIME="${SIM_TIME:-false}"
TRACK_IDS="${TRACK_IDS:-[44,68,99]}"

RVIZ_CONFIG="${1:-$DEFAULT_CONFIG}"
[[ "$RVIZ_CONFIG" == */* ]] || RVIZ_CONFIG="$HOME/.rviz2/$RVIZ_CONFIG"
if [[ ! -f "$RVIZ_CONFIG" ]]; then
    echo "no such rviz config: $RVIZ_CONFIG" >&2
    exit 1
fi
echo "rviz config: $RVIZ_CONFIG"

source /opt/ros/humble/setup.bash
source "$HOME/code/ros2_ws/install/setup.bash"

ROS_ARGS=(--ros-args -p use_sim_time:="$SIM_TIME")

# kill every child (nodes + rviz) when this script exits
trap 'kill 0' EXIT

python3 "$SCRIPTS/bearing_marker_node.py" "${ROS_ARGS[@]}" &
python3 "$SCRIPTS/bearing_marker_ids_node.py" "${ROS_ARGS[@]}" -p track_ids:="$TRACK_IDS" &
python3 "$SCRIPTS/smarcduino_marker_node.py" "${ROS_ARGS[@]}" &
python3 "$SCRIPTS/smarcduino_waraps_position_marker_node.py" "${ROS_ARGS[@]}" &
python3 "$SCRIPTS/fixed_position_marker_node.py" "${ROS_ARGS[@]}" &

rviz2 -d "$RVIZ_CONFIG" "${ROS_ARGS[@]}" &

wait
