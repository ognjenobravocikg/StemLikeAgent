import re

from llm.client import ask_llm


class FailureAnalyzer:

    VALID_FAILURES = {
        "skipped_steps",
        "arithmetic_error",
        "wrong_formula",
        "geometry_error",
        "no_verification",
        "inconsistent_answer",
        "shallow_reasoning",
        "missing_detail",
    }

    def analyze(self, question, answer, score, domain=None):
        if score >= 10:
            return "no_verification"

        failure = self._ask_classifier(question, answer, score, domain)
        if failure:
            return failure

        return self._fallback(question, answer, score)

    def _ask_classifier(self, question, answer, score, domain):
        labels = ", ".join(sorted(self.VALID_FAILURES))

        prompt = f"""
Classify the main reason this math/STEM answer did not receive a perfect score.

Use exactly one of these labels:
{labels}

Guidance:
- skipped_steps: reasoning jumps over important steps
- arithmetic_error: method is mostly right but computation is wrong
- wrong_formula: wrong theorem/formula/model was chosen
- geometry_error: geometry-specific shape/dimension/formula issue
- no_verification: answer looks close but lacks checking or final validation
- inconsistent_answer: reasoning and final answer disagree
- shallow_reasoning: answer is too thin to trust
- missing_detail: answer is incomplete or does not provide a usable numeric result

Domain: {domain}
Score: {score}/10

Question:
{question}

Answer:
{answer}

Return only the label.
"""

        result = ask_llm(
            system_prompt=(
                "You are a failure classifier for mathematical reasoning. "
                "Return only one allowed label."
            ),
            user_prompt=prompt,
        )

        return self._normalize(result)

    def _normalize(self, text):
        if not text:
            return None

        normalized = (text.strip().lower().replace("-", "_").replace(" ", "_"))
        normalized = re.sub(r"[^a-z_]", "", normalized)

        if normalized in self.VALID_FAILURES:
            return normalized

        for failure in self.VALID_FAILURES:
            if failure in normalized:
                return failure

        return None

    def _fallback(self, question, answer, score):
        q = question.lower()
        a = answer.lower() if answer else ""

        if not answer or "llm request failed" in a:
            return "missing_detail"

        has_number = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?", answer)
        if not has_number:
            return "missing_detail"

        if self._has_inconsistent_final(answer):
            return "inconsistent_answer"

        if any(word in q for word in ["circle", "rectangle", "triangle", "sphere", "cylinder", "cube", "ladder", "radius", "area", "volume"]):
            return "geometry_error"

        if any(word in q for word in ["force", "acceleration", "velocity", "kinetic", "projectile", "height", "mass", "energy"]):
            return "wrong_formula" if score <= 5 else "no_verification"

        if any(word in q for word in ["formula", "log", "root", "solve for", "equation", "sequence", "series"]):
            return "arithmetic_error" if score >= 5 else "wrong_formula"

        if score == 7:
            return "no_verification"

        if score == 5:
            return "arithmetic_error"

        if score <= 3:
            return "wrong_formula"

        return "shallow_reasoning"

    def _has_inconsistent_final(self, answer):
        explicit = re.findall(
            r"(?:^|\n)\s*[Aa]nswer\s*[:\-=]\s*(-?\d[\d,]*(?:\.\d+)?)",
            answer,
        )
        if not explicit:
            return False

        numbers = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", answer)
        if len(numbers) < 2:
            return False

        final = explicit[-1].replace(",", "")
        previous = numbers[-2].replace(",", "")

        return final != previous
