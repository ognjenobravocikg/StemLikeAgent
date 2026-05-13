import json


class Evaluator:
    def __init__(self, benchmark_path):
        with open(benchmark_path, "r") as f:
            self.tasks = json.load(f)

    def keyword_score(self, answer, keywords):
        score = 0
        answer_lower = answer.lower()
        for keyword in keywords:
            if keyword.lower() in answer_lower:
                score += 1
        return score / len(keywords)

    def evaluate(self, agent):
        total_score = 0
        for task in self.tasks:
            answer = agent.run(task["question"])
            score = self.keyword_score(
                answer,
                task["expected_keywords"]
            )
            total_score += score
        return total_score / len(self.tasks)