import numpy as np
import rclpy
from geometry_msgs.msg import (
    Point,
    QuaternionStamped,
    Transform,
    TransformStamped,
    Vector3,
    Vector3Stamped,
)
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from tf2_geometry_msgs import do_transform_vector3
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from visualization_msgs.msg import Marker

from bearing_error import bearing_error_2d

WORLD_FRAME = "evolo/map"
RAY_LENGTH = 300  # Arbitrary ray length for visualization


class BearingRayNode(Node):
    """
    Publishes camera bearing to the currently tracked target.

    Visualization as an ARROW marker.

    tracked_poi_image is a small rotation off the camera boresight, from
    yolo_action.py's detection bbox center. Not a world frame bearing on its
    own, it gets composed with the camera's TF orientation to get a real
    direction.
    """

    def __init__(self):
        super().__init__("bearing_ray_node")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.marker_publisher = self.create_publisher(
            Marker, "/evolo/gimbal_camera/target_bearing_marker", qos_profile=10
        )

        self.subscription = self.create_subscription(
            msg_type=QuaternionStamped,
            topic="/evolo/gimbal_camera/tracked_poi_image",
            callback=self.poi_callback,
            qos_profile=10,
        )

    def poi_callback(self, msg: QuaternionStamped):
        try:
            # TODO: Time() latest available tranform, should it be msg.header.stamp?
            transform = self.tf_buffer.lookup_transform(
                target_frame=WORLD_FRAME, source_frame=msg.header.frame_id, time=Time()
            )
        except TransformException as ex:
            self.get_logger().info(
                f"Could not transform {WORLD_FRAME} to {msg.header.frame_id}: {ex}"
            )
            return

        # Must be set before do_transform_vector3() as it overwrites
        # transform.transform.translation with (0,0,0)
        origin = Point(
            x=transform.transform.translation.x,
            y=transform.transform.translation.y,
            # z=0,
            z=transform.transform.translation.z,
        )

        # x is forward in camera link (not optical frame)
        forward = Vector3Stamped(vector=Vector3(x=1.0, y=0.0, z=0.0))

        # Quaternion for offset, wrapping for do_transform_vector3()
        offset_transform = TransformStamped(
            transform=Transform(rotation=msg.quaternion)
        )

        # offset -> target frame direction -> map frame
        target_frame_direction = do_transform_vector3(forward, offset_transform)
        bearing_vector = do_transform_vector3(target_frame_direction, transform)

        bearing = np.array(
            [bearing_vector.vector.x, bearing_vector.vector.y, bearing_vector.vector.z]
        )

        end_point = Point(
            x=origin.x + bearing[0] * RAY_LENGTH,
            y=origin.y + bearing[1] * RAY_LENGTH,
            # z=0,
            z=origin.z + bearing[2] * RAY_LENGTH,
        )

        # Populate marker
        marker = Marker()
        marker.header.frame_id = WORLD_FRAME
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.type = Marker.ARROW
        marker.action = Marker.ADD
        marker.points = [origin, end_point]
        marker.scale.x = 0.1  # ray size
        marker.scale.y = 1.0  # point width
        marker.scale.z = 1.0  # point length
        marker.color.a = 1.0
        marker.color.r = 1.0
        marker.lifetime = Duration(seconds=1).to_msg()

        self.marker_publisher.publish(marker)


def main():
    rclpy.init()
    node = BearingRayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
