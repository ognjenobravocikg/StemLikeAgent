from capabilities.base import Capability
from llm.client import ask_llm
import sympy as sp
import re


class FormulaSolverCapability(Capability):
    name = "formula_solver"

    def _extract_equations(self, question):
        """Ask the LLM to extract equations from the problem as sympy-parseable strings."""
        extraction_prompt = f"""
Read this math problem and extract any equations or expressions
that need to be solved.

Return ONLY a Python list of strings, each being a valid sympy
expression. For example:
["x**2 + 5*x + 6", "2*x + 3 - 11"]

If there are no clear equations, return an empty list: []

Problem:
{question}
"""
        result = ask_llm(
            system_prompt=(
                "You extract mathematical equations from word problems. "
                "Return only a Python list of sympy-compatible strings."
            ),
            user_prompt=extraction_prompt,
        )

        # Parse the list from the response
        match = re.search(r"\[.*?\]", result, re.DOTALL)
        if not match:
            return []

        try:
            raw = match.group(0)
            # Safe eval: only strings inside a list
            equations = []
            items = re.findall(r'"([^"]+)"|\'([^\']+)\'', raw)
            for a, b in items:
                equations.append(a or b)
            return equations
        except Exception:
            return []

    def _solve_equations(self, equations):
        """Solve extracted equations using sympy and return readable results."""
        results = []
        x, y, z, n = sp.symbols("x y z n")

        for eq_str in equations:
            try:
                expr = sp.sympify(eq_str)
                # Try solving for each common variable
                for var in [x, y, z, n]:
                    if expr.has(var):
                        solutions = sp.solve(expr, var)
                        if solutions:
                            results.append(
                                f"Solving {eq_str} for {var}: "
                                f"{var} = {solutions}"
                            )
                        break
                else:
                    # No variable — just simplify/evaluate
                    simplified = sp.simplify(expr)
                    numerical = sp.N(simplified)
                    results.append(
                        f"Expression {eq_str} = {simplified} ≈ {numerical}"
                    )
            except Exception as e:
                results.append(f"Could not solve '{eq_str}': {e}")

        return results

    def process(self, question):
        equations = self._extract_equations(question)
        solved = self._solve_equations(equations) if equations else []

        if solved:
            symbolic_results = "\n".join(f"  - {r}" for r in solved)
            return f"""
The following symbolic/algebraic results were computed exactly
using a math engine (these are correct — use them):

SYMBOLIC RESULTS:
{symbolic_results}

Now solve the full problem using these results as grounding.

Problem:
{question}

Show your reasoning and state the final answer clearly.
"""
        else:
            return f"""
Solve this problem algebraically where possible.
Show all equation setup and solving steps.

Problem:
{question}
"""