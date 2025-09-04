Remodel of the system architecture of SVLR to fit out system needs.

Remote server files are for an external computing center (such as a remote server in the HMI2 lab). Handles VLM segmentation and LLM semantic and inferencing. Check the README in the remote server for more information.

## Three System components
* **Main PC:** _urscripts_ files is found on the main PC. Our main communication hub. Captures input from vision, forwards image data, receives perception results, translates results into actional commands, sends commands, and ensures timing and sequence.
* **Remote Server:** _remoteserver_ is found on the remote server. SVLR VLM-LLM pipeline exists on remote server. Utilize SSH protocol and network sockets to communicate between Remote Server and Main PC.
* **UR10e Controller:** Controller allows the robot to move. Receieves our motion commands via URScript from the MainPC to give joint positions, velocities, and timing to the robot itself.

## Architecture
• Robot Info: This component includes a text-based description of the robot’s capabilities, provided to the LLM. It also contains the description and link to the robot tasks set, which is a collection of pre-programmed tasks. These tasks are selected and parametrized by the framework to execute the user’s instruction
• Perception Module: Identifies and retrieves objects in previously unseen environments.
• LLM: The LLM determines the sequence of tasks required to respond to the language instruction.
• Action Manager: The Action Manager executes the finalized tasks with their parameters and sends commands to the robot controller.
