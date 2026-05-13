from llm.client import ask_llm


class FailureAnalyzer:

    MATH_PROMPT = """
You are analysing why an AI gave a WRONG answer to a math problem.
The score is 3/10, meaning the model produced a number but it was incorrect.

QUESTION:
{question}

AI ANSWER:
{answer}

Choose the SINGLE best failure category from this list:

CATEGORIES:
- skipped_steps       : The problem needed multiple distinct calculation stages
                        (e.g. find rate, then apply it; find time for each part
                        separately; compute interest step by step) but the model
                        jumped to a final number without doing each stage.
                        USE THIS for: pipe/tank problems, average speed across
                        segments, simple/compound interest, mixture problems.

- arithmetic_error    : The model set up the right equation or method but
                        produced the wrong numeric result due to a calculation
                        mistake. The approach was correct, the number is wrong.
                        USE THIS for: algebra where the formula is right but
                        the solved value is wrong; arithmetic slips.

- wrong_formula       : The model used the wrong formula or theorem entirely.
                        The approach itself was incorrect from the start.

- geometry_error      : Any geometry problem (circle, rectangle, triangle,
                        sphere, square, cylinder) where the final number is
                        wrong. Includes wrong formula AND wrong calculation.

- inconsistent_answer : The working shown in the answer contradicts the final
                        number stated. The model's own steps do not lead to
                        the answer it gave.

STRICT RULES — read carefully:
1. NEVER choose no_verification. It is not a valid category here.
2. For ANY geometry shape problem with a wrong number → geometry_error.
3. For multi-step word problems (pipes, rates, interest, mixtures) where
   the model did not clearly do each step → skipped_steps.
4. For algebra where the equation setup looks right but x is wrong → arithmetic_error.
5. Return ONLY the single category keyword. Nothing else.

Your answer:
"""

    DEFAULT_PROMPT = """
Analyse why this AI answer is wrong or incomplete.

QUESTION: {question}
ANSWER: {answer}
SCORE: {score}/10

Choose ONE:
- shallow_reasoning
- poor_structure
- factual_risk
- unclear_explanation
- missing_detail

Return ONLY the keyword.
"""

    def analyze(self, question, answer, score, domain=None):
        if domain == "math_reasoning":
            prompt = self.MATH_PROMPT.format(
                question=question,
                answer=answer,
            )
            system = (
                "You identify the root cause of wrong math answers. "
                "Follow the rules exactly. Return one keyword only."
            )
        else:
            prompt = self.DEFAULT_PROMPT.format(
                question=question,
                answer=answer,
                score=score,
            )
            system = "You analyse AI answer quality."

        result = ask_llm(system_prompt=system, user_prompt=prompt)

        normalized = (
            result.strip()
            .lower()
            .split()[0]
            .replace("-", "_")
            .rstrip(".,:")
        )
        return normalized