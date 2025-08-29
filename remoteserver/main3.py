import threading
import argparse
import json
import socket
import cv2
import time
import os
from control_loop import ControlLoop
# Ensure you import read_robot_json if not already imported
from tools.read_json import read_robot_json

def simulation_controller(args, conn=None):
    # If no connection is provided, wait for a client connection.
    if conn is None:
        print("No connection provided. Waiting for a client to connect...")
        host = "0.0.0.0"
        port = 8000
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(1)  # Listen for one connection
        conn, addr = server.accept()
        print(f"Accepted connection from {addr}")
        server.close()
    
    # Read and send the initial pose (e.g., from a JSON file)
    init_pose = read_robot_json(args.robot_name)["init_pose"]
    init_pose_json = json.dumps(init_pose)
    print(f"Initial pose: {init_pose_json}")
    
    try:
        # Send the initial pose before starting simulation
        conn.sendall(init_pose_json.encode("utf-8"))
        print("Sent initial pose to client.")
    except Exception as e:
        print("Error sending initial pose:", e)
    
    # Build the path to the simulation image
    simulation_image_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "pictures",
        args.simulation_image_file,
    )
    image = cv2.imread(simulation_image_path)
    
    # Initialize the control loop
    controller = ControlLoop(args)
    
    while True:
        if args.show_image:
            cv2.imshow("Loaded Image", image)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()
        print("Write 'stop' if you want to stop the program")
        user_input = input("User input: ")
        if user_input.lower() == "stop":
            break
        
        action_dict = controller.run(image, user_input)
        if action_dict is None:
            print("No action generated")
            break
        
        print(f"Action: {action_dict}")
        
        # Send the action dictionary as JSON
        try:
            json_data = json.dumps(action_dict)
            conn.sendall(json_data.encode("utf-8"))
            print("Sent action to client.")
        except Exception as e:
            print("Error sending action data:", e)
            break
        
        # Optionally, return to the initial pose after each action
        try:
            conn.sendall(init_pose_json.encode("utf-8"))
            print("Returned to initial pose.")
        except Exception as e:
            print("Error sending initial pose:", e)
            break

    if conn is not None:
        conn.close()
        print("Connection closed.")

def handle_client(conn, addr, args):
    allowed_client_ip = "192.168.168.76"  # Replace with your actual client IP
    if addr[0] != allowed_client_ip:
        print(f"Rejected connection from {addr[0]}. Only accepting connections from {allowed_client_ip}.")
        conn.close()
        return
    print(f"Accepted connection from {addr}")
    simulation_controller(args, conn)

def start_server(args):
    host = "0.0.0.0"  # Listen on all interfaces
    port = 8000       # Server port for simulation data
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)  # Allow up to 5 queued connections
    print(f"Server listening on {host}:{port}")
    
    try:
        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, args))
            client_thread.daemon = True  # Ensure thread does not block process termination
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        server.close()
        print("Server socket closed.")

def real_controller(args):
    # Placeholder for the real controller logic when not in simulation mode
    print("Running real controller... (not implemented)")

def main():
    parser = argparse.ArgumentParser(description="Run the robot control loop")
    
    # Robot and server info
    parser.add_argument("--robot_name", type=str, default="UR10", help="Name of the robot")
    parser.add_argument("--server", type=str, default="127.0.0.1", help="Robot server address")
    parser.add_argument("--port", type=int, default=65500, help="Robot server port")
    parser.add_argument("--buffer", type=int, default=1024, help="Server buffer size")
    
    # Camera
    parser.add_argument("--camera_topic", type=str, default="", help="Camera ros topic")
    parser.add_argument("--camera_device", type=str, default="/dev/video2", help="Camera device")
    parser.add_argument("--camera_width", type=int, default=640, help="Camera width")
    parser.add_argument("--camera_height", type=int, default=480, help="Camera height")
    
    # LLM
    parser.add_argument("--llm_name", type=str, default="microsoft/Phi-3-mini-4k-instruct", help="LLM name")
    parser.add_argument("--llm_provider", type=str, default="HuggingFace", help="LLM provider: HuggingFace or OpenAI")
    parser.add_argument("--llm_temperature", type=float, default=0.1, help="LLM temperature: float between 0.1 and 1.0")
    parser.add_argument("--llm_is_chat", action="store_true", help="The LLM is a Chat model")
    
    # Simulation
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode")
    parser.add_argument("--simulation_image_file", type=str, default="test.png", help="Simulation image file")
    
    # Image
    parser.add_argument("--show_image", action="store_true", help="Show the captured image")
    parser.add_argument("--save_image", action="store_true", help="Save the captured image")
    
    args = parser.parse_args()
    
    # If simulation mode is active, start the server to send JSON data.
    if args.simulation:
        start_server(args)
    else:
        real_controller(args)

if __name__ == "__main__":
    main()
