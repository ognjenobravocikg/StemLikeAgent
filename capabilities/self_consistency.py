from capabilities.base import Capability
from llm.client import ask_llm
import re
from collections import Counter


class SelfConsistencyCapability(Capability):
    name = "self_consistency"

    NUM_SAMPLES = 3

    REASONING_STYLES = [
        "Solve this step-by-step, showing all arithmetic clearly.",
        "Work through this carefully. Write out every intermediate value.",
        "Think about what the problem is asking first, then solve it methodically.",
    ]

    def _extract_number(self, text):
        """Pull the last number out of an LLM response."""
        # Look for boxed answer first: \boxed{42}
        boxed = re.findall(r"\\boxed\{([^}]+)\}", text)
        if boxed:
            try:
                return float(boxed[-1].replace(",", ""))
            except ValueError:
                pass

        # Fall back to last standalone number in text
        numbers = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)
        if numbers:
            try:
                return float(numbers[-1].replace(",", ""))
            except ValueError:
                pass

        return None

    def process(self, question):
        answers = []

        for style in self.REASONING_STYLES:
            prompt = f"{style}\n\nQuestion:\n{question}"
            response = ask_llm(
                system_prompt=(
                    "You are a precise math solver. "
                    "Always end your answer with the final number only, "
                    "on its own line, like: Answer: 42"
                ),
                user_prompt=prompt,
            )
            number = self._extract_number(response)
            if number is not None:
                answers.append(number)

        if not answers:
            return question

        # Majority vote
        count = Counter(answers)
        majority_answer = count.most_common(1)[0][0]

        return f"""
Solve this math problem. Multiple independent reasoning paths
have suggested the answer is likely: {majority_answer}

Use that as a reference but show your full working.

Question:
{question}

End with: Answer: <number>
"""