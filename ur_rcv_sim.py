import socket
import robotiq_gripper
import time

# Robot connection details
robotIP = "192.168.168.5"
PRIMARY_PORT = 30001
new_line = "\n"

gripper_ip = "192.168.168.5"
gripper_port = 63352

gripper = robotiq_gripper.RobotiqGripper()
gripper.connect(gripper_ip, gripper_port, True)

#DONT unCOMMENT UNLESS NEEDED
gripper.activate()

def send_urscript_command(command: str):
    """
    Sends a URScript command to the robot.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((robotIP, PRIMARY_PORT))
        command += new_line
        s.sendall(command.encode('utf-8'))
        #s.close()
        print("URScript command sent successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        
def send_named_command(command):
    if command == "go_to_glove":
        print("Going to glove position")
    elif command == "move":
        print("Received generic move command (ignored numeric pose)")
    elif command == "reset_pose":
        print("Returning to neutral pose")
    else:
        print(f"Unknown command: {command}")

def send_pose_as_command(pose):
    """
    Formats a URScript command using the given pose and sends it to the robot.
    """
    new_pose_str = ", ".join(str(val) for val in pose)
    command = f"movel(p[{new_pose_str}], a=0.1, v=0.1, t=5)"
    print(f"Sending robot command: {command}")
    send_urscript_command(command)


def control_gripper(gripper_value):
    """
    Controls the Robotiq gripper based on the given value.
    """


    if gripper_value >= 200:
        #time.sleep(25)
        print("Closing gripper...")
        gripper.move_and_wait_for_pos(255, 100, 10)
    else:
        print("Opening gripper...")
        gripper.move_and_wait_for_pos(0, 100, 10)

    #gripper.disconnect()
    print("Gripper action complete.")

if __name__ == "__main__":
    # Test pose and gripper command
    initial_pose = [.160,.960,.426,3.131,-0.396,0.009]
    next_pose = [-0.027607652818406048, 1.0096836942414482, -0.0040000000000000036,3.131,-0.396,0.009]
    test_pose = [0.16095035287528445, 1.0370682512043379, -0.0040000000000000036,3.131,-0.396,0.009]
    test_gripper_value = 220  # Change to <200 to test opening
    open_gripper = 20
    send_pose_as_command(test_pose)
    time.sleep(7)
    control_gripper(test_gripper_value)
    time.sleep(5)
    send_pose_as_command(initial_pose)
    time.sleep(7)
    send_pose_as_command(next_pose)
    time.sleep(7)
    control_gripper(open_gripper)
