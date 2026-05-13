class CapabilitySelector:
    """
    Maps a (failure_type, task_type) pair to an ordered list of capabilities.
    The first capability not already active in active_config is returned,
    giving automatic fallback without abandoning the task.
    """

    # Base fallback lists for each failure type.
    FALLBACKS = {
        "math_reasoning": {
            "skipped_steps":       ["planner", "reflection", "critic"],
            "arithmetic_error":    ["formula_solver", "planner", "self_consistency"],
            "wrong_formula":       ["knowledge_retriever", "retrieval", "planner"],
            "geometry_error":      ["geometry_solver", "formula_solver", "knowledge_retriever"],
            "no_verification":     ["critic", "reflection", "planner"],
            "inconsistent_answer": ["self_consistency", "critic", "reflection"],
            "shallow_reasoning":   ["reflection", "planner", "critic"],
            "missing_detail":      ["retrieval", "knowledge_retriever", "reflection"],
        },
        "default": {
            "shallow_reasoning":   ["planner", "reflection"],
            "poor_structure":      ["planner", "reflection"],
            "factual_risk":        ["critic", "reflection"],
            "unclear_explanation": ["reflection", "critic"],
            "missing_detail":      ["retrieval", "reflection"],
        },
    }

    # Overrides for specific (failure_type, task_type) combinations.
    # formula_solver is designed for explicit equations, not prose word problems.
    # knowledge_retriever is better for physics where the formula is the problem.
    TASK_TYPE_OVERRIDES = {
        ("arithmetic_error", "word_problem"): ["reflection", "knowledge_retriever", "planner"],
        ("arithmetic_error", "physics"):      ["knowledge_retriever", "formula_solver", "planner"],
        ("wrong_formula",    "physics"):      ["knowledge_retriever", "retrieval", "formula_solver"],
        ("wrong_formula",    "word_problem"): ["knowledge_retriever", "reflection", "planner"],
        ("skipped_steps",    "physics"):      ["planner", "knowledge_retriever", "reflection"],
        ("skipped_steps",    "word_problem"): ["planner", "reflection", "knowledge_retriever"],
    }

    def select(self, failure_type, active_config, domain=None, task_type=None):
        """
        Return the first capability in the ranked fallback list that is
        not already active in active_config.

        Args:
            failure_type : string returned by FailureAnalyzer
            active_config: current best agent config dict
            domain       : optional domain string
            task_type    : optional task type (word_problem, geometry, etc.)

        Returns:
            capability name (str) or None if all options exhausted
        """
        normalized = (
            failure_type.strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        # Check task-type-specific override first
        if task_type:
            override_key = (normalized, task_type.lower())
            candidates = self.TASK_TYPE_OVERRIDES.get(override_key)
            if candidates:
                for cap in candidates:
                    if not active_config.get(cap, False):
                        return cap
                # All overrides exhausted — fall through to base mapping

        # Base domain mapping
        mapping = self.FALLBACKS.get(domain, self.FALLBACKS["default"])
        candidates = mapping.get(normalized)

        # Partial match if exact key not found
        if not candidates:
            for key, caps in mapping.items():
                if key in normalized or normalized in key:
                    candidates = caps
                    break

        if not candidates:
            return None

        for cap in candidates:
            if not active_config.get(cap, False):
                return cap

        return None