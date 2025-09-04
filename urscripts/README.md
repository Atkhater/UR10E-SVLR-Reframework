# urscripts
**remote_send_sim** connects the host PC to the remote server. It receives a JSON file that contains the action commands (end effect moves, gripper states, and centroids), processes them, and then forwards it to the robot controller via **ur_rcv_sim**.

**ur_rcv_sim** connects to the UR robot and sends URScript commands to it. It also controls the Robotiq gripper through the commands sent via JSON file.
