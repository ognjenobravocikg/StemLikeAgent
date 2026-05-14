class CapabilitySelector:

    # Base fallback lists for each failure type.
    FALLBACKS = { "math_reasoning": {
            "skipped_steps": ["planner", "reflection", "critic"], "arithmetic_error": ["formula_solver", "planner", "self_consistency"],
            "wrong_formula": ["knowledge_retriever", "retrieval", "planner"], "geometry_error": ["geometry_solver", "formula_solver", "knowledge_retriever"],
            "no_verification": ["critic", "reflection", "planner"],
            "inconsistent_answer": ["self_consistency", "critic", "reflection"],
            "shallow_reasoning": ["reflection", "planner", "critic"],
            "missing_detail":["retrieval", "knowledge_retriever", "reflection"],
        },
        "default": {
            "shallow_reasoning": ["planner", "reflection"], "poor_structure": ["planner", "reflection"],
            "factual_risk": ["critic", "reflection"], "unclear_explanation": ["reflection", "critic"],
            "missing_detail": ["retrieval", "reflection"],
        },
    }

    # Overrides for specific failure_type to task_type combinations.
    # formula_solver is designed for explicit equations, not word problems.
    # knowledge_retriever is better for physics where the formula is the problem.
    TASK_OVERRIDERINGS = {
        ("arithmetic_error", "word_problem"): ["reflection", "knowledge_retriever", "planner"],
        ("arithmetic_error", "physics"): ["knowledge_retriever", "formula_solver", "planner"],
        ("wrong_formula", "physics"): ["knowledge_retriever", "retrieval", "formula_solver"],
        ("wrong_formula", "word_problem"): ["knowledge_retriever", "reflection", "planner"],
        ("skipped_steps", "physics"): ["planner", "knowledge_retriever", "reflection"],
        ("skipped_steps", "word_problem"): ["planner", "reflection", "knowledge_retriever"],
    }

    def select(self, failure_type, active_config, domain=None, task_type=None):
        """
        Return the first capability in the ranked fallback list that is
        not already active in active_config.

        failure_type is a string returned by FailureAnalyzer. For example, "arithmetic_error" or "shallow_reasoning" and/or such
        active_config is the current best agent config dict

        """
        normalized = ( failure_type.strip().lower().replace("-", "_").replace(" ", "_"))

        # Check task-type-specific override first
        if task_type:
            override_key = (normalized, task_type.lower())
            candidates = self.TASK_OVERRIDERINGS.get(override_key)
            if candidates:
                for cap in candidates:
                    if not active_config.get(cap, False):
                        return cap
                # Svaki override je crkao, predji na fallback

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