from capabilities.base import Capability
from llm.client import ask_llm
import sympy as sp
import re


class GeometrySolverCapability(Capability):
    name = "geometry_solver"

    # Map shape names to their area/perimeter formulas using sympy
    SHAPE_FORMULAS = {
        "circle": {
            "area": lambda r: sp.pi * r**2,
            "circumference": lambda r: 2 * sp.pi * r,
            "params": ["radius"],
        },
        "rectangle": {
            "area": lambda l, w: l * w,
            "perimeter": lambda l, w: 2 * (l + w),
            "diagonal": lambda l, w: sp.sqrt(l**2 + w**2),
            "params": ["length", "width"],
        },
        "triangle": {
            "area": lambda b, h: sp.Rational(1, 2) * b * h,
            "hypotenuse": lambda a, b: sp.sqrt(a**2 + b**2),
            "params": ["base", "height"],
        },
        "square": {
            "area": lambda s: s**2,
            "perimeter": lambda s: 4 * s,
            "diagonal": lambda s: s * sp.sqrt(2),
            "params": ["side"],
        },
        "sphere": {
            "volume": lambda r: sp.Rational(4, 3) * sp.pi * r**3,
            "surface_area": lambda r: 4 * sp.pi * r**2,
            "params": ["radius"],
        },
        "cylinder": {
            "volume": lambda r, h: sp.pi * r**2 * h,
            "surface_area": lambda r, h: 2 * sp.pi * r * (r + h),
            "params": ["radius", "height"],
        },
    }

    def _extract_geometry_info(self, question):
        """Ask LLM to extract shape, dimensions, and target computation."""
        prompt = f"""
Read this geometry problem and extract:
1. The shape name (circle, rectangle, triangle, square, sphere, cylinder)
2. The numeric values for its dimensions
3. What is being asked (area, perimeter, volume, circumference, diagonal, hypotenuse, surface_area)

Return ONLY a JSON object like this example:
{{"shape": "circle", "params": {{"radius": 5}}, "target": "area"}}

If it's not a geometry problem, return: {{}}

Problem:
{question}
"""
        result = ask_llm(
            system_prompt=(
                "You extract geometry information from math problems. "
                "Return only a JSON object."
            ),
            user_prompt=prompt,
        )

        match = re.search(r"\{[^{}]+\}", result)
        if not match:
            return {}
        try:
            import json
            return json.loads(match.group(0))
        except Exception:
            return {}

    def _compute(self, info):
        """Run the exact computation using sympy."""
        if not info:
            return None

        shape = info.get("shape", "").lower()
        params = info.get("params", {})
        target = info.get("target", "")

        if shape not in self.SHAPE_FORMULAS:
            return None

        formulas = self.SHAPE_FORMULAS[shape]

        if target not in formulas:
            return None

        try:
            param_values = [
                sp.Rational(str(v))
                for v in params.values()
            ]
            result = formulas[target](*param_values)
            exact = sp.simplify(result)
            numerical = float(sp.N(exact, 6))
            return {
                "shape": shape,
                "target": target,
                "params": params,
                "exact": str(exact),
                "numerical": numerical,
            }
        except Exception as e:
            return {"error": str(e)}

    def process(self, question):
        info = self._extract_geometry_info(question)
        result = self._compute(info)

        if result and "error" not in result:
            return f"""
GEOMETRY COMPUTATION (exact, computed by math engine):

Shape: {result['shape']}
Dimensions: {result['params']}
Target: {result['target']}
Exact result: {result['exact']}
Numerical result: ≈ {result['numerical']}

Use these exact values in your solution. Do not re-derive them.

Now explain the solution fully and state the final answer.

Problem:
{question}
"""
        else:
            return f"""
This appears to be a geometry problem. Solve it carefully:

1. Identify the shape and its dimensions
2. Write out the relevant formula
3. Substitute the values exactly
4. Compute step by step

Problem:
{question}
"""