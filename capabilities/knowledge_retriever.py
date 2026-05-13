from capabilities.base import Capability
from llm.client import ask_llm
from tools.search_tool import SearchTool


# Hardcoded reference bank for common math/physics laws.
# Used as fallback when web search is unavailable or too slow.
KNOWLEDGE_BANK = {
    "quadratic": (
        "Quadratic formula: for ax² + bx + c = 0, "
        "x = (-b ± √(b²-4ac)) / 2a. "
        "Discriminant D = b²-4ac: D>0 two real roots, D=0 one root, D<0 no real roots."
    ),
    "pythagorean": (
        "Pythagorean theorem: a² + b² = c² where c is the hypotenuse. "
        "Common triples: (3,4,5), (5,12,13), (8,15,17)."
    ),
    "newton": (
        "Newton's laws: "
        "1st: object at rest stays at rest unless acted on by a net force. "
        "2nd: F = ma (force = mass × acceleration). "
        "3rd: every action has an equal and opposite reaction."
    ),
    "kinematics": (
        "Kinematic equations (constant acceleration): "
        "v = u + at, "
        "s = ut + ½at², "
        "v² = u² + 2as, "
        "s = (u+v)/2 × t. "
        "Where u=initial velocity, v=final velocity, a=acceleration, s=displacement, t=time."
    ),
    "energy": (
        "Energy: KE = ½mv² (kinetic), PE = mgh (gravitational potential). "
        "Conservation of energy: total energy is constant in a closed system. "
        "Work = Force × distance × cos(θ)."
    ),
    "probability": (
        "Probability basics: P(A) = favourable outcomes / total outcomes. "
        "P(A and B) = P(A) × P(B) if independent. "
        "P(A or B) = P(A) + P(B) - P(A and B). "
        "Combinations: C(n,r) = n! / (r!(n-r)!). "
        "Permutations: P(n,r) = n! / (n-r)!."
    ),
    "arithmetic_series": (
        "Arithmetic series: sum = n/2 × (first + last) = n/2 × (2a + (n-1)d). "
        "nth term = a + (n-1)d. Where a=first term, d=common difference, n=number of terms."
    ),
    "geometric_series": (
        "Geometric series: sum = a(1-rⁿ)/(1-r) for r≠1. "
        "nth term = a × r^(n-1). "
        "Infinite sum (|r|<1): a / (1-r)."
    ),
    "logarithm": (
        "Logarithm rules: log(ab) = log(a)+log(b), log(a/b) = log(a)-log(b), "
        "log(aⁿ) = n×log(a). "
        "Change of base: log_b(x) = ln(x)/ln(b)."
    ),
    "derivative": (
        "Differentiation rules: d/dx(xⁿ) = nxⁿ⁻¹, d/dx(eˣ) = eˣ, "
        "d/dx(ln x) = 1/x, d/dx(sin x) = cos x, d/dx(cos x) = -sin x. "
        "Product rule: (fg)' = f'g + fg'. Chain rule: d/dx f(g(x)) = f'(g(x))g'(x)."
    ),
}


class KnowledgeRetrieverCapability(Capability):
    name = "knowledge_retriever"

    def __init__(self):
        self.search_tool = SearchTool()

    def _identify_topic(self, question):
        """Ask LLM to identify the math/physics topic of the problem."""
        prompt = f"""
What is the main math or physics topic needed to solve this problem?

Choose the single best match from:
quadratic, pythagorean, newton, kinematics, energy, probability,
arithmetic_series, geometric_series, logarithm, derivative, geometry, other

Return ONLY the topic keyword.

Problem:
{question}
"""
        result = ask_llm(
            system_prompt="You identify math and physics topics.",
            user_prompt=prompt,
        )
        return result.strip().lower().split()[0]

    def _get_knowledge(self, topic, question):
        """Return relevant theory from the bank, or fall back to web search."""
        # Check local knowledge bank first
        for key, knowledge in KNOWLEDGE_BANK.items():
            if key in topic or topic in key:
                return knowledge, "knowledge_bank"

        # Fall back to web search for unknown topics
        try:
            query = f"{topic} formula theorem definition math"
            result = self.search_tool.search(query, num_results=2)
            if result:
                return result, "web_search"
        except Exception:
            pass

        return None, None

    def process(self, question):
        topic = self._identify_topic(question)
        knowledge, source = self._get_knowledge(topic, question)

        if knowledge:
            return f"""
RELEVANT THEORY ({source}):
Topic: {topic}

{knowledge}

---
Use the theory above to guide your solution.
Apply the correct formula and show all substitution steps.

Problem:
{question}
"""
        else:
            return f"""
Solve this problem. Identify and state any relevant formulas
or theorems before applying them.

Problem:
{question}
"""