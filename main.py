from core.stem_agent import StemAgent
from core.math_evaluator import MathEvaluator
from core.evolution import EvolutionEngine
import json


def main():
    evaluator = MathEvaluator("benchmarks/math_tasks.json")

    with open("configs/base_agent.json", "r") as f:
        config = json.load(f)

    stem_agent = StemAgent(config=config)

    evolution_engine = EvolutionEngine(evaluator)

    specialized_agent, final_score = evolution_engine.evolve(stem_agent)

    print("\n" + "="*50)
    print(f"FINAL SCORE: {final_score:.2f}/10")
    print("="*50)

    # Just a show off test at the end to see how the specialized agent does on a question, step by step
    test_question = (
        "A sphere has a radius of 3 m. "
        "What is its volume? Round to 2 decimal places."
    )

    print(f"\nTEST QUESTION: {test_question}")

    answer = specialized_agent.run(test_question)
    print(f"\nSPECIALIZED AGENT ANSWER:\n{answer}")

    print(f"\nFINAL CONFIG: {specialized_agent.config}")


if __name__ == "__main__":
    main()