from core.stem_agent import StemAgent
from core.failure_analyzer import FailureAnalyzer
from core.capability_selector import CapabilitySelector
from core.mutation_engine import MutationEngine
from core.experiment_tracker import ExperimentTracker
from core.memory_manager import MemoryManager
from core.evolution_chart import EvolutionChart


CAPABILITIES = [
    "planner",
    "critic",
    "reflection",
    "retrieval",
    "self_consistency",
    "formula_solver",
    "geometry_solver",
    "knowledge_retriever"
]

BAD_PAIRS = [
    {"formula_solver", "planner"},
    {"geometry_solver", "planner"},
    {"self_consistency", "retrieval"}
]

MAX_RETRIES = 3


class EvolutionEngine:

    def __init__(self, evaluator):
        self.evaluator = evaluator

        self.tracker = ExperimentTracker()
        self.memory_manager = MemoryManager()

        self.failure_analyzer = FailureAnalyzer()
        self.selector = CapabilitySelector()
        self.mutator = MutationEngine()

        self.total_tries = 0
        self.good_mutations = 0

    # If pairs are in conflict, we skip them to avoid combinatorial explosion and wasted tries. 
    def _conflicts(self, cfg, cap):
        enabled = []

        for k, v in cfg.items():
            if v:
                enabled.append(k)

        for pair in BAD_PAIRS:
            if cap not in pair:
                continue

            for x in pair:
                if x != cap and x in enabled:
                    return True

        return False

    def _avg_score(self, scores):
        vals = []
        for _, (score, _) in scores.items():
            vals.append(score)
        if not vals:
            return 0

        return sum(vals) / len(vals)

    def evolve(self, base_agent):
        agent = base_agent

        domain = None
        if "domain" in agent.config:
            domain = agent.config["domain"]

        print("\nstarting baseline run...\n")

        task_scores = self.evaluator.score_all_tasks(agent)

        initial_scores = {}
        for q, (s, _) in task_scores.items():
            initial_scores[q] = s

        best_score = self._avg_score(task_scores)

        print("base score =", round(best_score, 2))

        chart = EvolutionChart(base_score=best_score)

        # main task at hand
        for task in self.evaluator.tasks:
            q = task["question"]
            t = task.get("type", "unknown")

            curr_score, curr_answer = task_scores[q]

            if curr_score >= 10:
                continue

            print("\n" + "-" * 50)
            print(t.upper(), "|", curr_score, "/10")
            print(q[:80])

            tried = set()

            retry = 0

            while retry < MAX_RETRIES:

                retry += 1

                print("\nretry", retry)

                merged_cfg = dict(agent.config)

                for c in tried:
                    merged_cfg[c] = True

                failure = self.failure_analyzer.analyze(
                    q,
                    curr_answer,
                    curr_score,
                    domain=domain
                )

                print("failure:", failure)

                # POPRAVI KASNIJE
                capability = self.selector.select(
                    failure,
                    merged_cfg,
                    domain=domain,
                    task_type=t
                )

                if capability is None:
                    print("nothing left to try")
                    break

                if self._conflicts(agent.config, capability):
                    print(capability, "conflicts with current setup")
                    tried.add(capability)
                    continue

                print("trying", capability)

                new_cfg = self.mutator.mutate(
                    agent.config,
                    capability
                )

                candidate = StemAgent(config=new_cfg)

                score, answer, extracted = self.evaluator.run_single(candidate,task)

                print("score:", curr_score, "->", score, "| got:", extracted, "| expected:", task.get("answer"))

                self.total_tries += 1

                accepted = score > curr_score

                self.memory_manager.record_result(
                    capability,
                    accepted
                )

                self.tracker.log(
                    base_config=agent.config,
                    mutation=capability,
                    candidate_config=new_cfg,
                    score=score,
                    accepted=accepted,
                    failure_type=failure
                )

                if accepted:

                    old = curr_score

                    self.good_mutations += 1

                    curr_score = score
                    curr_answer = answer

                    agent = candidate

                    task_scores[q] = (score, answer)

                    best_score = self._avg_score(task_scores)

                    print("accepted")
                    print("overall:", round(best_score, 2))

                    chart.record_mutation(
                        capability=capability,
                        question_short=q[:50],
                        task_type=t,
                        score_before=old,
                        score_after=score,
                        overall_score=best_score,
                        accepted=True
                    )

                else:
                    tried.add(capability)

                    print("rejected")

                    chart.record_mutation(
                        capability=capability,
                        question_short=q[:50],
                        task_type=t,
                        score_before=curr_score,
                        score_after=score,
                        overall_score=best_score,
                        accepted=False
                    )

                if self.total_tries > 0:
                    rate = (
                        self.good_mutations /
                        self.total_tries
                    ) * 100
                else:
                    rate = 0

                print(
                    "adaptation:",
                    self.good_mutations,
                    "/",
                    self.total_tries,
                    f"({rate:.0f}%)"
                )

                if curr_score >= 10:
                    print("solved")
                    break

        self.tracker.save()

        final_scores = {}
        for q, (s, _) in task_scores.items():
            final_scores[q] = s

        active_caps = []

        for k, v in agent.config.items():
            if v:
                active_caps.append(k)

        print("\n" + "=" * 50)
        print(
            "FINAL ADAPTATION RATE:",
            self.good_mutations,
            "/",
            self.total_tries
        )

        print("active:", active_caps)
        print("=" * 50)

        chart.generate(
            initial_task_scores=initial_scores, final_task_scores=final_scores,
            tasks=self.evaluator.tasks,
            final_config=agent.config
        )

        return agent, best_score