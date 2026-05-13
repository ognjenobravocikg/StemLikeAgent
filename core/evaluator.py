import json
from llm.client import ask_llm

class Evaluator:
    def __init__(self, benchmark_path):
        with open(benchmark_path, "r") as f:
            self.tasks = json.load(f)

    def judge_answer(
        self,
        question,
        answer,
    ):

        evaluation_prompt = f"""
Evaluate this AI answer.

QUESTION:
{question}

ANSWER:
{answer}

Score from 1-10 for:
1. factual accuracy
2. completeness
3. reasoning depth
4. clarity

Return ONLY a single number.
"""

        result = ask_llm(
            system_prompt="You are a strict evaluator.",
            user_prompt=evaluation_prompt,
        )
        try:
            return float(result.strip())
        except:
            return 5.0

    def evaluate(self, agent):

        total_score = 0
        for task in self.tasks:
            print(f"RUNNING QUESTION: {task['question']}")
            answer = agent.run(task["question"])
            score = self.judge_answer(
                task["question"],
                answer,
            )
            print(f"SCORE: {score}")
            total_score += score
        return total_score / len(self.tasks)