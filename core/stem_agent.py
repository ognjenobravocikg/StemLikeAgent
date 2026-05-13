from llm.client import ask_llm
from core.capability_factory import (CapabilityFactory)

class StemAgent:
    def __init__(self, config):
        self.config = config
        self.capabilities = (
            CapabilityFactory.build_from_config(
                config
            )
        )

    def build_prompt(self, question):
        processed_question = question

        for capability in self.capabilities:
            processed_question = (
                capability.process(
                    processed_question
                )
            )
            
        return processed_question

    def run(self, question):
        print(
            f"RUNNING QUESTION: "
            f"{question}"
        )

        prompt = self.build_prompt(question)

        answer = ask_llm(
            system_prompt=(
                "You are a helpful "
                "research assistant."
            ),
            user_prompt=prompt,
        )

        return answer