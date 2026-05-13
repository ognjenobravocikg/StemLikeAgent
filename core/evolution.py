from core.stem_agent import StemAgent
from core.failure_analyzer import FailureAnalyzer
from core.capability_selector import CapabilitySelector
from core.mutation_engine import MutationEngine
from core.experiment_tracker import ExperimentTracker
from core.memory_manager import MemoryManager

ALL_CAPABILITIES = [
    "planner", "critic", "reflection", "retrieval",
    "self_consistency", "formula_solver",
    "geometry_solver", "knowledge_retriever",
]

# Capability pairs that must never be active together.
# formula/geometry_solver receive already-transformed text from planner,
# which breaks their equation/shape extraction logic.
INCOMPATIBLE_PAIRS = [
    frozenset(["formula_solver",   "planner"]),
    frozenset(["geometry_solver",  "planner"]),
    frozenset(["self_consistency", "retrieval"]),
]


class EvolutionEngine:

    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.tracker = ExperimentTracker()
        self.memory_manager = MemoryManager()
        self.failure_analyzer = FailureAnalyzer()
        self.capability_selector = CapabilitySelector()
        self.mutation_engine = MutationEngine()

        self.mutation_attempts = 0
        self.mutation_successes = 0

    def _is_incompatible(self, active_config, new_capability):
        """Return True if new_capability conflicts with any already-active capability."""
        active = {k for k, v in active_config.items() if v}
        for pair in INCOMPATIBLE_PAIRS:
            if new_capability in pair:
                other = (pair - {new_capability}).pop()
                if other in active:
                    return True
        return False

    def evolve(self, base_agent):
        best_agent = base_agent
        domain = base_agent.config.get("domain", None)

        print("\n--- Baseline evaluation ---")
        task_scores = self.evaluator.score_all_tasks(best_agent)
        best_score = (
            sum(s for s, _ in task_scores.values()) / len(task_scores)
        )
        print(f"Base score: {best_score:.2f}/10\n")

        ranked_capabilities = self.memory_manager.rank_capabilities(
            ALL_CAPABILITIES
        )
        print(f"Memory-ranked capabilities: {ranked_capabilities}\n")

        for task in self.evaluator.tasks:
            question = task["question"]
            task_type = task.get("type", "unknown")
            current_score, current_answer = task_scores[question]

            # ── Skip tasks already solved ──────────────────────────────────
            if current_score >= 10.0:
                continue

            print(f"[{task_type.upper()}] score={current_score}/10 → analysing...")

            failure_type = self.failure_analyzer.analyze(
                question, current_answer, current_score, domain=domain
            )
            print(f"  Weakness      : {failure_type}")

            # Pass active config + task_type so selector can skip
            # already-active caps and use task-type-specific fallbacks.
            capability_name = self.capability_selector.select(
                failure_type, best_agent.config,
                domain=domain, task_type=task_type
            )

            if not capability_name:
                print("  All options already active or no match — skipping.\n")
                continue

            # Incompatible pair check
            if self._is_incompatible(best_agent.config, capability_name):
                print(
                    f"  {capability_name} conflicts with an active capability"
                    f" — skipping.\n"
                )
                continue

            print(f"  Trying        : {capability_name}")

            new_config = self.mutation_engine.mutate(
                best_agent.config, capability_name
            )
            candidate_agent = StemAgent(config=new_config)

            # ── Evaluate ONLY on same-type tasks ───────────────────────────
            # Baseline for this type using cached scores
            type_tasks = [
                t for t in self.evaluator.tasks
                if t.get("type") == task_type
            ]
            type_baseline = (
                sum(task_scores[t["question"]][0] for t in type_tasks)
                / len(type_tasks)
            )

            print(
                f"  Evaluating on [{task_type}] tasks only "
                f"(baseline={type_baseline:.2f})..."
            )
            candidate_type_score, candidate_type_results = (
                self.evaluator.evaluate_by_type(candidate_agent, task_type)
            )
            print(
                f"  Type result   : {type_baseline:.2f} → "
                f"{candidate_type_score:.2f}"
            )

            self.mutation_attempts += 1

            # ── Regression guard ───────────────────────────────────────────
            # Reject if any previously-perfect task in this type dropped.
            regression = False
            for t in type_tasks:
                q = t["question"]
                prev = task_scores[q][0]
                new  = candidate_type_results[q][0]
                if prev >= 10.0 and new < 10.0:
                    print(f"  REGRESSION: {q[:60]}...")
                    regression = True
                    break

            accepted = (not regression) and (candidate_type_score > type_baseline)

            if accepted:
                self.mutation_successes += 1
                print(f"  ACCEPTED — improvement on [{task_type}] tasks.")
                best_agent = candidate_agent

                # Update cached scores for same-type tasks only
                task_scores.update(candidate_type_results)
                best_score = (
                    sum(s for s, _ in task_scores.values()) / len(task_scores)
                )
                print(f"  New overall score: {best_score:.2f}/10")
            else:
                print("  Rejected.")

            self.memory_manager.record_result(capability_name, accepted)

            self.tracker.log(
                base_config=best_agent.config,
                mutation=capability_name,
                candidate_config=new_config,
                score=candidate_type_score,
                accepted=accepted,
                failure_type=failure_type,
            )

            # Re-rank after each memory update
            ranked_capabilities = self.memory_manager.rank_capabilities(
                ALL_CAPABILITIES
            )

            success_rate = (
                self.mutation_successes / self.mutation_attempts * 100
                if self.mutation_attempts else 0
            )
            print(
                f"  Adaptation rate: "
                f"{self.mutation_successes}/{self.mutation_attempts} "
                f"({success_rate:.0f}%)\n"
            )

        self.tracker.save()

        final_rate = (
            self.mutation_successes / self.mutation_attempts * 100
            if self.mutation_attempts else 0
        )
        print(
            f"\nFinal adaptation rate: "
            f"{self.mutation_successes}/{self.mutation_attempts} "
            f"({final_rate:.0f}%)"
        )

        return best_agent, best_score