Remodel of the system architecture of SVLR to fit our system needs.

Remote server files are for an external computing center (such as a remote server in the HMI2 lab). Handles VLM segmentation and LLM semantic and inferencing. Check the README in the remote server for more information.
# How to use

User interface is through the main PC. 
* Using VSCodes Remote Explorer (found on extensions), SSH directly to the IP of the remote server (in this case my log in).
* In the terminal, run `python main.py --show_image --simulation --simulation_image_file your_image.png` , where your_image.png is replaced with the image from the camera. The default name can be set. At this point, it will be waiting for a connection from the MainPC.
* Open up the terminal on the MainPC.
* In the terminal, `run ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur10e robot_ip:=_Insert_IP_Here_` to enable the controllers on the robot.
* In a new tab of the terminal, run the _remote_send_sim.py_ file via `python remote_send_sim.py`.
* This will connect the remote server code and the main PC code. The remote server will ask for user input, in which you can ask the robot to perform a task.
* After the user input, the system should handle the rest.

## Three System components
* **Main PC:** _urscripts_ files is found on the main PC. Our main communication hub. Captures input from vision, forwards image data, receives perception results, translates results into actional commands, sends commands, and ensures timing and sequence.
* **Remote Server:** _remoteserver_ is found on the remote server. SVLR VLM-LLM pipeline exists on remote server. Utilize SSH protocol and network sockets to communicate between Remote Server and Main PC.
* **UR10e Controller:** Controller allows the robot to move. Receieves our motion commands via URScript from the MainPC to give joint positions, velocities, and timing to the robot itself.

## Architecture
* **Robot Info:** This component includes a text-based description of the robot’s capabilities, provided to the LLM. It also contains the description and link to the robot tasks set, which is a collection of pre-programmed tasks. These tasks are selected and parametrized by the framework to execute the user’s instruction
* **Perception Module:** Identifies and retrieves objects in previously unseen environments.
* **LLM:** The LLM determines the sequence of tasks required to respond to the language instruction.
* **Action Manager:** The Action Manager executes the finalized tasks with their parameters and sends commands to the robot controller.

## JSON File
Includes the following parameters:
* **pos_end_effector** - End effector position to be controlled
  * **move** - Action of the end effector, move from A to B
* **gripper** - action of the gripper
  * **open** - open the gripper
  * **close** - close the gripper
* **action_id** - Allows grouping of actions into one id should multiple actions occur sequentially
* **step** - Allows seeing each step of the controlled sequence of actions
* **objects_detected** - What objects are detected in the environment
* **user_command** - The LLM input of the user
* **generated_action** - What action was generated e.g. "move" or "pick and place"
* **timestamp** - timestamp for troubleshooting purposes

## Robot Workflow

<img width="1109" height="546" alt="image" src="https://github.com/user-attachments/assets/3b51445f-ce4a-4620-a5ec-7f8aa9ea5c28" />

Presentation and Examples can be found on my google slide presentation

https://docs.google.com/presentation/d/1fFHMVcorjudS-x4gTP2paeiI849NgUsTP5x2PNdIvKo/edit?usp=sharing
