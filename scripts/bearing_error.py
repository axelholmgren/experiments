"""Geometry helpers for comparing a measured bearing with a known target."""

import math


def bearing_error_2d(origin, bearing, truth):
    """Return signed yaw error (degrees) and horizontal miss distance (metres).
    Ignoring Z to project down to 2d
    """
    target_x = truth[0] - origin[0]
    target_y = truth[1] - origin[1]
    target_range = math.hypot(target_x, target_y)
    bearing_length = math.hypot(bearing[0], bearing[1])

    if target_range == 0.0 or bearing_length == 0.0:
        return None

    ray_x = bearing[0] / bearing_length
    ray_y = bearing[1] / bearing_length
    expected_x = target_x / target_range
    expected_y = target_y / target_range

    angle_error_rad = math.atan2(
        ray_x * expected_y - ray_y * expected_x,
        ray_x * expected_x + ray_y * expected_y,
    )
    miss_distance_m = target_range * abs(math.sin(angle_error_rad))
    return math.degrees(angle_error_rad), miss_distance_m


def bearing_error_3d(origin, bearing, truth):
    """Return 3D angular error (degrees) and shortest line miss distance (m).

    ``origin``, ``bearing``, and ``truth`` are ``(x, y, z)`` tuples in the
    same map frame. The angular error is unsigned because a 3D angle has no
    single left/right sign.
    """
    target_x = truth[0] - origin[0]
    target_y = truth[1] - origin[1]
    target_z = truth[2] - origin[2]
    target_range = math.sqrt(target_x**2 + target_y**2 + target_z**2)
    bearing_length = math.sqrt(bearing[0] ** 2 + bearing[1] ** 2 + bearing[2] ** 2)

    if target_range == 0.0 or bearing_length == 0.0:
        return None

    ray_x = bearing[0] / bearing_length
    ray_y = bearing[1] / bearing_length
    ray_z = bearing[2] / bearing_length

    dot = (ray_x * target_x + ray_y * target_y + ray_z * target_z) / target_range
    angle_error_rad = math.acos(max(-1.0, min(1.0, dot)))

    # |target_vector x unit_ray| is the closest distance to the bearing line.
    miss_distance_m = math.sqrt(
        (target_y * ray_z - target_z * ray_y) ** 2
        + (target_z * ray_x - target_x * ray_z) ** 2
        + (target_x * ray_y - target_y * ray_x) ** 2
    )
    return math.degrees(angle_error_rad), miss_distance_m
