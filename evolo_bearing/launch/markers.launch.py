"""Launch the bearing-marker visualisation used for live runs and rosbag replay."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare("evolo_bearing")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use /clock; set true when replaying a bag with --clock.",
            ),
            DeclareLaunchArgument(
                "track_ids",
                default_value="[]",
                description="Optional YOLO track IDs for selected bearing rays.",
            ),
            DeclareLaunchArgument(
                "rviz_config",
                default_value=PathJoinSubstitution(
                    [package_share, "config", "tracking_ray_evolo_smarcduino.rviz"]
                ),
                description="Absolute path to an RViz configuration file.",
            ),
            Node(
                package="evolo_bearing",
                executable="bearing_marker_node",
                name="bearing_ray_node",
                parameters=[{"use_sim_time": use_sim_time}],
            ),
            Node(
                package="evolo_bearing",
                executable="bearing_marker_ids_node",
                name="bearing_ray_ids_node",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "track_ids": LaunchConfiguration("track_ids"),
                    }
                ],
            ),
            Node(
                package="evolo_reference_markers",
                executable="smarcduino_marker_node",
                name="smarcduino_position_marker_node",
                parameters=[{"use_sim_time": use_sim_time}],
            ),
            Node(
                package="evolo_reference_markers",
                executable="smarcduino_waraps_position_marker_node",
                name="smarcduino_waraps_position_marker_node",
                parameters=[{"use_sim_time": use_sim_time}],
            ),
            Node(
                package="evolo_reference_markers",
                executable="fixed_position_marker_node",
                name="fixed_position_marker_node",
                parameters=[{"use_sim_time": use_sim_time}],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                arguments=["-d", LaunchConfiguration("rviz_config")],
                parameters=[{"use_sim_time": use_sim_time}],
            ),
        ]
    )
