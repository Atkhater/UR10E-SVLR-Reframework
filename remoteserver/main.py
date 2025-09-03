"""Main script to run the robot control loop.
Sends JSON data over a socket connection.
"""
import threading
import argparse
import json
import socket
import cv2
import time
import os
from control_loop import ControlLoop
from tools.read_json import read_robot_json
from uuid import uuid4

def simulation_controller(args, conn=None):
    if conn is None:
        print("No connection provided. Waiting for a client to connect...")
        host = "0.0.0.0"
        port = 8000
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(1)
        conn, addr = server.accept()
        print(f"Accepted connection from {addr}")
        server.close()
    
    # Load simulation image
    simulation_image_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "pictures",
        args.simulation_image_file,
    )
    image = cv2.imread(simulation_image_path)
    
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
                
        result = controller.run(image, user_input)
        if result is None:
            print("No action generated")
            break

        # Separate out action list and centroid data
        if isinstance(result, list):
            action_dict = result
            centroids = controller.prompt_generator.perception.environment_pos
        else:
            action_dict = result.get("actions", [])
            centroids = result.get("centroids", controller.prompt_generator.perception.environment_pos)
        action_id = str(uuid4())[:8]
        for idx, action in enumerate(action_dict):
            action["action_id"] = action_id
            action["step"] = idx + 1

        # Extract info
        object_list = controller.prompt_generator.environment_description_list
        user_cmd = controller.prompt_generator.user_command.replace("User Command:\n", "").strip()
        parsed_action = controller.last_action_type if hasattr(controller, "last_action_type") else "unknown"

        # Attach metadata to each action
# Attach metadata to each action
        for action in action_dict:
            action["objects_detected"] = controller.prompt_generator.environment_description_list
            action["user_command"] = user_input.strip()
            action["generated_action"] = getattr(controller, "last_action_type", "unknown")
            #action["centroids"] = centroids  # Attach centroids to each action


        print(f"Action with objects and command: {action_dict}")


        
        try:
            json_data = json.dumps(action_dict)
            conn.sendall(json_data.encode("utf-8"))
            print("Sent action to client.")
        except Exception as e:
            print("Error sending action data:", e)
            break

    if conn is not None:
        conn.close()
        print("Connection closed.")

# Checks if the computer IP is allowed
def handle_client(conn, addr, args):
    allowed_client_ip = "192.168.168.76" #Change this IP for your computer IP
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

#This isn't used. Used the simulation controller for real controller instead.
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
