'''
Aly Khater
HMI2 Lab
This script connects a UR10e robot system to a remote perception server over TCP.
It receives JSON-encoded action commands (end-effector moves, gripper states,
and detected object centroids, etc.), processes them, and forwards robot commands
to the robot controller. 

Key functionality:
- Maintains a socket client connection to the perception server.
- Parses incoming JSON actions, data, and filters duplicates.
- Translates end effector positions into robot base frame coordinates
- Translates gripper values into human-readable "open"/"close" states.
- Saves received actions to a JSONL log file for replay or debugging.
- Uses camera intrinsics and extrinsics to transform 2D image pixel coordinates 
  (u, v, depth) into 3D positions in the robot’s base frame.
- Prints raw and transformed centroid data for validation and debugging.
- Interfaces with the robot controller.
'''

import socket
import json
from datetime import datetime
import numpy as np
import cv2
import os
from ur_rcv_sim import send_named_command  

#Camera Matrix via Camera Calibration.
K = np.array([
    [912.339721679688, 0.0,                 655.437561035156],
    [0.0,               911.811584472656,   370.901947021484],
    [0.0,               0.0,                 1.0]
])

K_inv = np.linalg.inv(K)

# Distortion coefficients (k1, k2, p1, p2, k3)
#Had values previously using instrinsics of camera, leaving here incase someone reuses.
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

#Undistort pixels according to distortion matrix.
def undistort_pixel(u, v):
    points = np.array([[[u, v]]], dtype=np.float32)
    undistorted = cv2.undistortPoints(points, K, dist_coeffs, P=K)
    return undistorted[0][0]  # Returns (u', v')

#Transforms a pixel to camera frame
def pixel_to_camera_frame(u, v, depth=1.0):
    pixel = np.array([u, v, 1.0])
    cam_coords = K_inv @ pixel
    return (cam_coords * depth).tolist()
#Transforms camera to robot frame
def camera_to_robot_frame(cam_coords):
    return (R_camera_to_base @ np.array(cam_coords) + T_camera_to_base).tolist()

#Main function to connect to the remote server, receive data via json, and translate data into a readable format.
def run_client():
    #Create a socket to connect to the remote server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "192.168.168.42" #Remote server IP
    server_port = 8000
    last_action_no_timestamp = None
    actions = [] #Empty action dictionary

    #Waits until connection is formed to the remote server
    try:
        client.connect((server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}")

        while True:
            #Size of the data received in the JSON file. Increase the value to increase the size of data transfer (bit sizes).
            data = client.recv(4096)
            #No data received, closes connection.
            if not data:
                print("No data received. Closing connection.")
                break

            #Data received, parses data
            try:
                action_data = json.loads(data.decode("utf-8"))
                #Transforms into a readable dictionary
                if isinstance(action_data, dict):
                    action_data = [action_data]

                for action_dict in action_data:
                    #Prints action from the remote server before parsing.
                    print(f"\nRaw action received: {action_dict}")
                    #Gets the end effector position key
                    pose_cmd = action_dict.get("pos_end_effector")
                    #Translates data into a move action
                    action_dict["pos_end_effector"] = "move" if isinstance(pose_cmd, list) else str(pose_cmd)
                    #Gets the gripper key
                    gripper_value = action_dict.get("gripper", None)
                    #Translates gripper data to open and close
                    action_dict["gripper"] = "close" if gripper_value == 220 else "open" if gripper_value == 30 else "unknown"

                    #Debugging purposes, attaches a time stamp to the action
                    current_action_no_timestamp = {
                        "pos_end_effector": action_dict["pos_end_effector"],
                        "gripper": action_dict["gripper"]
                    }
                    
                    #Checks if action is repeated. If not, continues
                    if current_action_no_timestamp != last_action_no_timestamp:
                        action_dict["timestamp"] = datetime.now().isoformat()
                        actions.append(action_dict)

                        # Save action
                        with open("received_actions.jsonl", "a") as f:
                            f.write(json.dumps(action_dict) + "\n")

                        # Send to robot
                        print(f"Simplified command: {action_dict}")
                        send_named_command(action_dict["pos_end_effector"]) 

                        # Centroid conversion
                        centroids = action_dict.get("objects_detected", {})
                        for name, (u, v, z) in centroids.items():
                            #measured depth from robot to object. Currently flat
                            z_m = .42
                            #cam_coords = pixel_to_camera_frame(u, v, z_m)
                            #Grabs the undistorted pixels
                            u_undist, v_undist = undistort_pixel(u, v)
                            #Transforms pixels to the camera coordinates
                            cam_coords = pixel_to_camera_frame(u_undist, v_undist, z_m)
                            #Transforms to base coordinates
                            base_coords = camera_to_robot_frame(cam_coords)
                            #Prints the centroid position relative to the robot base frame.
                            print(f"{name} (pixel): ({u:.1f}, {v:.1f}, {z:.1f}) --> Robot base: {base_coords}")

                        last_action_no_timestamp = current_action_no_timestamp
                    #Skips current step in the dictionary if it is repeated
                    else:
                        print("Duplicate action skipped.")
            #If not valid JSON, discards.
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
