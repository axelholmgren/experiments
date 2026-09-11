"""Launch the bearing-marker visualisation used for live runs and rosbag replay."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare("evolo_bearing")
    use_sim_time = LaunchConfiguration("use_sim_time")
    yaw_correction_mode = LaunchConfiguration("yaw_correction_mode")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use /clock; set true when replaying a bag with --clock.",
            ),
            DeclareLaunchArgument(
                "yaw_correction_mode",
                default_value="absolute",
                description="Yaw correction mode: shape or absolute.",
            ),
            DeclareLaunchArgument(
                "track_ids",
                default_value="",
                description=(
                    "Optional YOLO track IDs for selected bearing rays, for example "
                    "'[44,68,99]'. Leave empty to disable selected-ID rays."
                ),
            ),
            DeclareLaunchArgument(
                "rviz_config",
                default_value=PathJoinSubstitution(
                    [package_share, "config", "tracking_ray_evolo_smarcduino.rviz"]
                ),
                description="Absolute path to an RViz configuration file.",
            ),
            DeclareLaunchArgument(
                "lidar_boxes",
                default_value="false",
                description=(
                    "Start LiDAR preprocessing, clustering, and corrected "
                    "bounding-box tracking."
                ),
            ),
            Node(
                package="evolo_bearing",
                executable="bearing_marker_node",
                name="bearing_ray_node",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "yaw_correction_mode": yaw_correction_mode,
                    }
                ],
            ),
            Node(
                package="evolo_bearing",
                executable="bearing_marker_ids_node",
                name="bearing_ray_ids_node",
                condition=IfCondition(
                    PythonExpression(["'", LaunchConfiguration("track_ids"), "' != ''"])
                ),
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "track_ids": LaunchConfiguration("track_ids"),
                        "yaw_correction_mode": yaw_correction_mode,
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
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("pointcloud_preprocessing"),
                            "launch",
                            "pointcloud_preprocessing_launch_evolo.py",
                        ]
                    )
                ),
                condition=IfCondition(LaunchConfiguration("lidar_boxes")),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("clustering_segmentation"),
                            "launch",
                            "mapping_clustering_segmentation_launch.py",
                        ]
                    )
                ),
                condition=IfCondition(LaunchConfiguration("lidar_boxes")),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("bb_dataass_tracking"),
                            "launch",
                            "tracking_launch_evolo.py",
                        ]
                    )
                ),
                condition=IfCondition(LaunchConfiguration("lidar_boxes")),
            ),
        ]
    )
