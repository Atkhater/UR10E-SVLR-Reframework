import socket
import json
from datetime import datetime
import numpy as np
import cv2
import os

# from ur_rcv_sim import send_named_command  # Uncomment this on your system


K = np.array([
    [912.339721679688, 0.0,                 655.437561035156],
    [0.0,               911.811584472656,   370.901947021484],
    [0.0,               0.0,                 1.0]
])

K_inv = np.linalg.inv(K)

# Distortion coefficients (k1, k2, p1, p2, k3)
dist_coeffs = np.array([0,0,0,0,0])
image_size = (1280, 720)

# Camera-to-base transform (camera mounted on TCP)
R_camera_to_base = np.array([
    [1,  0,  0],
    [0, -1,  0],
    [0,  0, -1]
])
#T_camera_to_base = np.array([0.158, 0.957, 0.600])  # meters, SIM
T_camera_to_base = np.array([0.160, 1.030, 0.416])  # meters, REAL

def undistort_pixel(u, v):
    points = np.array([[[u, v]]], dtype=np.float32)
    undistorted = cv2.undistortPoints(points, K, dist_coeffs, P=K)
    return undistorted[0][0]  # Returns (u', v')

def pixel_to_camera_frame(u, v, depth=1.0):
    pixel = np.array([u, v, 1.0])
    cam_coords = K_inv @ pixel
    return (cam_coords * depth).tolist()

def camera_to_robot_frame(cam_coords):
    return (R_camera_to_base @ np.array(cam_coords) + T_camera_to_base).tolist()

def run_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "192.168.168.42"
    server_port = 8000
    last_action_no_timestamp = None
    actions = []

    try:
        client.connect((server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}")

        while True:
            data = client.recv(4096)
            if not data:
                print("No data received. Closing connection.")
                break

            try:
                action_data = json.loads(data.decode("utf-8"))
                if isinstance(action_data, dict):
                    action_data = [action_data]

                for action_dict in action_data:
                    print(f"\nRaw action received: {action_dict}")

                    pose_cmd = action_dict.get("pos_end_effector")
                    action_dict["pos_end_effector"] = "move" if isinstance(pose_cmd, list) else str(pose_cmd)
                    gripper_value = action_dict.get("gripper", None)
                    action_dict["gripper"] = "close" if gripper_value == 220 else "open" if gripper_value == 30 else "unknown"

                    current_action_no_timestamp = {
                        "pos_end_effector": action_dict["pos_end_effector"],
                        "gripper": action_dict["gripper"]
                    }

                    if current_action_no_timestamp != last_action_no_timestamp:
                        action_dict["timestamp"] = datetime.now().isoformat()
                        actions.append(action_dict)

                        # Save action
                        with open("received_actions.jsonl", "a") as f:
                            f.write(json.dumps(action_dict) + "\n")

                        # Send to robot
                        print(f"Simplified command: {action_dict}")
                        # send_named_command(action_dict["pos_end_effector"])  # Uncomment this

                        # Centroid conversion
                        centroids = action_dict.get("objects_detected", {})
                        for name, (u, v, z) in centroids.items():
                            z_m = .42
                            #cam_coords = pixel_to_camera_frame(u, v, z_m)
                            u_undist, v_undist = undistort_pixel(u, v)
                            cam_coords = pixel_to_camera_frame(u_undist, v_undist, z_m)
                            base_coords = camera_to_robot_frame(cam_coords)
                            print(f"{name} (pixel): ({u:.1f}, {v:.1f}, {z:.1f}) --> Robot base: {base_coords}")

                        last_action_no_timestamp = current_action_no_timestamp
                    else:
                        print("Duplicate action skipped.")

            except json.JSONDecodeError:
                print("Received data is not valid JSON:", data)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        print("Connection to server closed.")

    print("\nAll received actions:", actions)

if __name__ == "__main__":
    run_client()
