#!/usr/bin/env python3

import sys
from pathlib import Path

from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_types_from_msg, get_typestore

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path.home() / "code/ros2_ws/src/smarc2/scripts/rosbag_analyzer"))
from rosbag_types import SmarcRosbagTypestore

smarc_types = SmarcRosbagTypestore()
typestore = smarc_types.construct_custom_typestore()

# geographic_msgs isn't part of rosbags' built-in ROS2_HUMBLE store or the
# smarc2 custom messages, but the latlon topics use it, so register it here.
geopoint_msg_path = Path("/opt/ros/humble/share/geographic_msgs/msg/GeoPoint.msg")
typestore.register(
    get_types_from_msg(geopoint_msg_path.read_text(), "geographic_msgs/msg/GeoPoint")
)

# Path to the directory with the rosbag. Not the rosbag itself
# due to the way ros2 records bags now.
# file ='src/smarc2/scripts/rosbag_analyzer/rosbag2_2024_10_15-11_47_37'
# Rosbag with following of tender vessel
file = Path("~/ros_logs/AXL/CAM/rosbag2_2026_08_17-12_20_02/").expanduser()

states = {}
states["smarcduino_lat"] = []
states["smarcduino_long"] = []
states["evolo_lat"] = []
states["evolo_long"] = []

events = {}
events["t"] = []

# Create reader instance and open for reading.
with Reader(file) as reader:
    # Topic and msgtype information is available on .connections list.
    for reader_connection in reader.connections:
        print(reader_connection.topic, reader_connection.msgtype)

    # Iterate over messages.
    for connection, timestamp, rawdata in reader.messages():
        if connection.topic == "/parameter_events":
            msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
            events["t"].append(msg.stamp.sec + 1e-9 * msg.stamp.nanosec)
        if connection.topic == "/smarcduino/latlon":
            msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
            states["smarcduino_lat"].append(msg.latitude)
            states["smarcduino_long"].append(msg.longitude)
        if connection.topic == "/evolo/smarc/latlon":
            msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
            states["evolo_lat"].append(msg.latitude)
            states["evolo_long"].append(msg.longitude)

    print("Bag read")

events["trig"] = np.ones(len(events["t"]))

fig = plt.figure()
plt.title("Latitude/Longitude Trajectory")
plt.plot(states["smarcduino_long"], states["smarcduino_lat"], label="smarcduino")
plt.plot(states["smarcduino_long"][0], states["smarcduino_lat"][0], "*")
plt.plot(states["evolo_long"], states["evolo_lat"], label="evolo")
plt.plot(states["evolo_long"][0], states["evolo_lat"][0], "*")
plt.xlabel("longitude")
plt.ylabel("latitude")
plt.legend()
print("should show plot")

plt.show()
