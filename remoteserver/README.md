# Remote Server
**actions** contains the actions allowable for the robotic system. The actions are "move_to", "pick_and_place", "open_gripper", and "close_gripper". Defines the poses for each of the actions.

**pictures** contains many pictures utilized for scenarios for our system. Add new pictures to this folder via camera to try new scenarios.

**similarity_model** the sentence transformers model.

**src** contains the action file to parse action texts into an action dictionary <{'action': 'action_name', param: ['param1', 'param2'...]> to create a list to be sent through a JSON file. Contains the action manager to determine what actions the robot needs to do through the similarity model. Also contains the LLM and VLM models for inferencing.

**calibration.yaml** contains camera instrinsics.

**control_loop** contains our main action generation, with a generated prompt from the LLM to create the action dictionary.

**main.py** contains all of our main code that is ran on the remote server. Establishes connection between host PC and remote server, utilizing sockets. Uses an image from the **pictures** folder to load our image into the VLM and utilizes OpenCV to show the image. Establishes the JSON file to be sent over to the host PC. The JSON file contains our action dictionary, centroid positions, timestamps, and action_id.  

