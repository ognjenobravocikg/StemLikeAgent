import os
import matplotlib
matplotlib.use("Agg")   
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
from collections import defaultdict

# This is AI coded !
SCORE_COLORS = {0:  "#d62728", 3:  "#ff7f0e", 5:  "#ffbb78", 7:  "#2ca02c", 10: "#1f77b4" }
CAP_ACCEPTED_COLOR  = "#2ca02c"
CAP_REJECTED_COLOR  = "#d62728"
TYPE_COLORS = {
    "word_problem": "#9467bd",
    "algebra":      "#8c564b",
    "geometry":     "#e377c2",
    "physics":      "#7f7f7f",
    "series":       "#bcbd22",
}


class EvolutionChart:
    """
    Panels:
        1 — Overall score progression across accepted mutations
        2 — Per-task score improvement (before vs after)
        3 — Capability attempt outcomes (accepted / rejected)
        4 — Score distribution before vs after (0/3/5/7/10)
    """

    def __init__(self, base_score: float):
        self.base_score = base_score
        self.mutations  = []   # list of dicts, one per mutation attempt

    def record_mutation(self,capability: str,question_short: str,task_type: str,score_before: float,
        score_after: float,
        overall_score: float,
        accepted: bool,
    ):
        self.mutations.append({
            "capability": capability, "question_short": question_short, "task_type": task_type,
            "score_before": score_before,"score_after": score_after,"overall_score": overall_score,
            "accepted": accepted,
        })

    # Panel pomagaci nemam pojma sta se desava ovde

    def _panel_score_progression(self, ax):
        accepted = [m for m in self.mutations if m["accepted"]]
        x      = list(range(len(accepted) + 1))
        scores = [self.base_score] + [m["overall_score"] for m in accepted]
        labels = ["baseline"] + [m["capability"] for m in accepted]

        ax.plot(x, scores, marker="o", color="#1f77b4", linewidth=2, zorder=3)

        for xi, (yi, lbl) in enumerate(zip(scores, labels)):
            ax.annotate(
                f"{yi:.2f}",
                xy=(xi, yi),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color="#1f77b4",
            )

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
        ax.set_ylim(0, 10.5)
        ax.set_ylabel("Overall score / 10")
        ax.set_title("Score progression (accepted mutations)")
        ax.axhline(10, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.grid(axis="y", alpha=0.3)

    def _panel_per_task(self, ax, initial_task_scores, final_task_scores, tasks):
        # Only show tasks that changed
        changed = [
            t for t in tasks
            if initial_task_scores.get(t["question"], 10) < 10
        ]

        if not changed:
            ax.text(0.5, 0.5, "All tasks were perfect at baseline",
                    ha="center", va="center", transform=ax.transAxes)
            ax.set_title("Per-task scores (before vs after)")
            return

        labels  = [t["question"][:35] + "…" for t in changed]
        before  = [initial_task_scores.get(t["question"], 0) for t in changed]
        after   = [final_task_scores.get(t["question"], 0)   for t in changed]
        x       = np.arange(len(changed))
        width   = 0.35

        bars_b = ax.bar(x - width/2, before, width, label="Before",
                        color="#aec7e8", edgecolor="white")
        bars_a = ax.bar(x + width/2, after,  width, label="After",
                        color="#1f77b4", edgecolor="white")

        for bar in bars_b:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.1,
                    str(int(h)), ha="center", va="bottom", fontsize=7)
        for bar in bars_a:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.1,
                    str(int(h)), ha="center", va="bottom", fontsize=7)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=7)
        ax.set_ylim(0, 12)
        ax.set_ylabel("Score / 10")
        ax.set_title("Per-task scores (before vs after)")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    def _panel_capability_outcomes(self, ax):
        counts = defaultdict(lambda: {"accepted": 0, "rejected": 0})
        for m in self.mutations:
            key = "accepted" if m["accepted"] else "rejected"
            counts[m["capability"]][key] += 1

        caps      = sorted(counts.keys())
        accepted  = [counts[c]["accepted"] for c in caps]
        rejected  = [counts[c]["rejected"] for c in caps]
        y         = np.arange(len(caps))

        ax.barh(y, accepted, color=CAP_ACCEPTED_COLOR, label="Accepted", alpha=0.85)
        ax.barh(y, rejected, left=accepted, color=CAP_REJECTED_COLOR,
                label="Rejected", alpha=0.85)

        ax.set_yticks(y)
        ax.set_yticklabels(caps, fontsize=8)
        ax.set_xlabel("Number of attempts")
        ax.set_title("Capability outcomes")
        ax.legend(fontsize=8)
        ax.grid(axis="x", alpha=0.3)

    def _panel_score_distribution(self, ax, initial_task_scores, final_task_scores):
        score_levels = [0, 3, 5, 7, 10]

        def dist(scores_dict):
            d = {s: 0 for s in score_levels}
            for s in scores_dict.values():
                bucket = max(sl for sl in score_levels if sl <= s)
                d[bucket] += 1
            return d

        before = dist(initial_task_scores)
        after  = dist(final_task_scores)

        x      = np.array([0, 1])
        bottom = np.zeros(2)

        for level in score_levels:
            heights = np.array([before[level], after[level]])
            ax.bar(x, heights, bottom=bottom,
                   color=SCORE_COLORS[level],
                   label=f"Score {level}",
                   edgecolor="white", width=0.4)
            for xi, (h, b) in enumerate(zip(heights, bottom)):
                if h > 0:
                    ax.text(x[xi], b + h/2, str(int(h)),
                            ha="center", va="center",
                            fontsize=8, color="white", fontweight="bold")
            bottom += heights

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Before", "After"], fontsize=10)
        ax.set_ylabel("Number of tasks")
        ax.set_title("Score distribution (all tasks)")
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(axis="y", alpha=0.3)

    # Public entry point

    def generate(self, initial_task_scores: dict, final_task_scores:   dict,
        tasks:               list,
        final_config:        dict,
    ):
        os.makedirs("experiments", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath  = f"experiments/evolution_chart_{timestamp}.png"
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            "Evolution Run — Math Reasoning Specialisation",
            fontsize=14, fontweight="bold", y=1.01,
        ) 

        self._panel_score_progression(axes[0][0])
        self._panel_per_task(axes[0][1], initial_task_scores, final_task_scores, tasks)
        self._panel_capability_outcomes(axes[1][0])
        self._panel_score_distribution(axes[1][1], initial_task_scores, final_task_scores)

        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"\nChart saved → {filepath}")

    def _adaptation_rate_str(self):
        total    = len(self.mutations)
        accepted = sum(1 for m in self.mutations if m["accepted"])
        if total == 0:
            return "0/0 (0%)"
        return f"{accepted}/{total} ({accepted/total*100:.0f}%)"