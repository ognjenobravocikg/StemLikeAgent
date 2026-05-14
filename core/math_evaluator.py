import json
import re


class MathEvaluator:
    def __init__(self, benchmark_path):
        with open(benchmark_path, "r") as f:
            self.tasks = json.load(f)

    def extract_number(self, text):
        """
        Pull the final numeric answer out of an LLM response.

        Priority:
          1. Explicit 'Answer: X' line
          2. \\boxed{X}
          3. Last number after a = or ≈ sign
          4. Last multi-digit or decimal number
             (avoids single digits like '2' from '2 decimal places')
          5. Any number as last resort
        """
        # 1. "Answer: 42" on its own line
        m = re.search(
            r"(?:^|\n)\s*[Aa]nswer\s*[:\-=]\s*(-?\d[\d,]*(?:\.\d+)?)",
            text,
        )
        if m:
            return float(m.group(1).replace(",", ""))

        # 2. \boxed{42}
        boxed = re.findall(r"\\boxed\{([^}]+)\}", text)
        if boxed:
            try:
                return float(boxed[-1].replace(",", "").strip())
            except ValueError:
                pass

        # 3. Number after = or ≈
        after_eq = re.findall(
            r"[=≈]\s*(-?\d[\d,]*(?:\.\d+)?)\s*(?:[a-zA-Z²³]|$|\n|\.|,)",
            text,
        )
        if after_eq:
            try:
                return float(after_eq[-1].replace(",", ""))
            except ValueError:
                pass

        # 4. Last multi-digit or decimal number
        meaningful = re.findall(
            r"-?\d{2,}(?:,\d{3})*(?:\.\d+)?|-?\d+\.\d+",
            text,
        )
        if meaningful:
            try:
                return float(meaningful[-1].replace(",", ""))
            except ValueError:
                pass

        # 5. Any number
        all_nums = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)
        if all_nums:
            try:
                return float(all_nums[-1].replace(",", ""))
            except ValueError:
                pass

        return None

    # !!! Ne svidja mi se kako ovo trenutno radi, pokusaj da popravis sa boljim ocenjivanjem, mozda bi bilo dobro da se stigne i neki
    # djavo za specificno ocenjivanje po matematickoj klasii !!!

    def _relative_error(self, extracted, expected):
        """Return relative error, handling zero expected values."""
        if isinstance(expected, list):
            return min(self._relative_error(extracted, e) for e in expected)
        if expected == 0:
            return 0.0 if abs(extracted) < 0.01 else float("inf")
        return abs(extracted - expected) / abs(expected)

    def judge_answer(self, question, answer, expected=None):
        """
        Return a score in {0, 3, 5, 7, 10}.

        Thresholds (relative error):
            ≤ 2%    10  correct
            < 20%   7   right approach
            ≤ 100%  5   right ballpark
            > 100%  3   wrong approach
            no num  0   could not extract any number
        """
        extracted = self.extract_number(answer)

        if expected is None:
            return 5.0  # no ground truth — neutral score
        if extracted is None:
            return 0.0

        rel = self._relative_error(extracted, expected)

        if rel <= 0.02:
            return 10.0
        if rel < 0.20:
            return 7.0
        if rel <= 1.00:
            return 5.0
        return 3.0


    def _run_task(self, agent, task):
        question = task["question"]
        expected = task.get("answer")
        answer   = agent.run(question)
        score    = self.judge_answer(question, answer, expected)
        return question, answer, score

    # Run benchmark and score all tasks as question: (socre, answer). Used later by cache
    def score_all_tasks(self, agent):
        results = {}
        for task in self.tasks:
            q, ans, score = self._run_task(agent, task)
            t = task.get("type", "?").upper()
            extracted = self.extract_number(ans)
            print(
                f"  [{t}] score={score}/10"
                f"  (got {extracted}, expected {task.get('answer')})"
            )
            results[q] = (score, ans)
        return results

    def run_single(self, agent, task):
        q, ans, score = self._run_task(agent, task)
        extracted = self.extract_number(ans)
        return score, ans, extracted