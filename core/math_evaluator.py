import json
import re


class MathEvaluator:
    TOLERANCE = 0.02

    def __init__(self, benchmark_path):
        with open(benchmark_path, "r") as f:
            self.tasks = json.load(f)

    def extract_number(self, text):
        """
        Extract the final numeric answer from LLM response.

        Priority order:
          1. Explicit 'Answer: X' line (most reliable)
          2. \\boxed{X}
          3. Last number after = or ≈ sign
          4. Last multi-digit or decimal number
             (avoids single digits like '2' from '2 decimal places')
          5. True last resort: any number
        """
        # 1. "Answer: 42" on its own line
        answer_match = re.search(
            r"(?:^|\n)\s*[Aa]nswer\s*[:\-=]\s*(-?\d[\d,]*(?:\.\d+)?)",
            text,
        )
        if answer_match:
            return float(answer_match.group(1).replace(",", ""))

        # 2. \boxed{42}
        boxed = re.findall(r"\\boxed\{([^}]+)\}", text)
        if boxed:
            try:
                return float(boxed[-1].replace(",", "").strip())
            except ValueError:
                pass

        # 3. Number immediately after = or ≈
        after_equals = re.findall(
            r"[=≈]\s*(-?\d[\d,]*(?:\.\d+)?)\s*(?:[a-zA-Z²³]|$|\n|\.|,)",
            text,
        )
        if after_equals:
            try:
                return float(after_equals[-1].replace(",", ""))
            except ValueError:
                pass

        # 4. Last number with 2+ digits or a decimal point
        meaningful = re.findall(
            r"-?\d{2,}(?:,\d{3})*(?:\.\d+)?|-?\d+\.\d+",
            text,
        )
        if meaningful:
            try:
                return float(meaningful[-1].replace(",", ""))
            except ValueError:
                pass

        # 5. True last resort: any number
        all_numbers = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)
        if all_numbers:
            try:
                return float(all_numbers[-1].replace(",", ""))
            except ValueError:
                pass

        return None

    def is_correct(self, extracted, expected):
        if extracted is None:
            return False
        if isinstance(expected, list):
            return any(self.is_correct(extracted, e) for e in expected)
        if expected == 0:
            return abs(extracted) < 0.01
        return abs(extracted - expected) / abs(expected) <= self.TOLERANCE

    def judge_answer(self, question, answer, expected=None):
        extracted = self.extract_number(answer)
        if expected is not None:
            if self.is_correct(extracted, expected):
                return 10.0
            elif extracted is not None:
                return 3.0
            else:
                return 0.0
        return 5.0

    def _run_task(self, agent, task):
        question = task["question"]
        expected = task.get("answer")
        answer = agent.run(question)
        score = self.judge_answer(question, answer, expected)
        return question, answer, score

    def evaluate_by_type(self, agent, task_type):
        """
        Run only tasks matching task_type.
        Returns (avg_score, {question: (score, answer)})
        """
        matching = [t for t in self.tasks if t.get("type") == task_type]
        if not matching:
            return 0.0, {}

        results = {}
        for task in matching:
            q, ans, score = self._run_task(agent, task)
            results[q] = (score, ans)
            print(f"    [{task_type.upper()}] score={score}/10")

        avg = sum(s for s, _ in results.values()) / len(results)
        return avg, results

    def score_all_tasks(self, agent):
        """
        Run the full benchmark and return {question: (score, answer)}.
        Used to build the initial per-task cache.
        """
        results = {}
        for task in self.tasks:
            q, ans, score = self._run_task(agent, task)
            t = task.get("type", "?").upper()
            print(f"  [{t}] score={score}/10")
            results[q] = (score, ans)
        return results