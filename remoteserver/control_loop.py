from src.llm import LLM
from src.prompt_generator import PromptGenerator
from src.action import ActionManager
from tools.read_json import read_robot_json

import argparse
import time
import torch


class ControlLoop:
    def __init__(self, args: argparse.Namespace):

        # Initialize the robot information
        self.robot_name = args.robot_name
        self.robot_info = read_robot_json(self.robot_name)

        # Save LLM parameters
        self.llm_temperature = args.llm_temperature
        self.llm_name = args.llm_name
        self.llm_provider = args.llm_provider
        self.llm_is_chat = args.llm_is_chat
        self.llm = None

        # Initialize the prompt generator
        self.prompt_generator = PromptGenerator(robot_info=self.robot_info)

        # Initialize action
        self.action = ActionManager(robot_info=self.robot_info)
        print("Control loop initialized")

    def run(self, image, user_input):
        start = time.time()
        print("Generating actions...")
        prompt = self.prompt_generator.run(user_input, image)

        # Store the original user command
        self.last_user_command = user_input

        print("Starting LLM")
        self.llm = LLM(
            model_name=self.llm_name,
            temperature=self.llm_temperature,
            provider=self.llm_provider,
            is_chat=self.llm_is_chat,
        )
        print(f"Generated Prompt:\n{self.llm.prompt_system.format(content=prompt)}")
        action_text = self.llm.run(prompt)

        self.llm = None
        torch.cuda.empty_cache()
        print(f"LLM Response:\n{action_text}")

        action_dict_list = self.action.run(
            action_text,
            self.prompt_generator.environment_description_list,
            self.prompt_generator.perception.environment_pos,
        )

        # Try extracting action type (like "pick_and_place")
        if isinstance(action_dict_list, list) and len(action_dict_list) > 0:
            self.last_action_type = self.action.extract_last_action_type(action_text)
        else:
            self.last_action_type = "unknown"

        print(f"Generated actions:\n{action_dict_list}")
        end = time.time()
        print(f"Control Loop - Time taken: {end - start}")
        return action_dict_list

