from capabilities.planner import PlannerCapability
from capabilities.critic import CriticCapability
from capabilities.reflection import ReflectionCapability
from capabilities.retrieval import RetrievalCapability
from capabilities.self_consistency import SelfConsistencyCapability
from capabilities.formula_solver import FormulaSolverCapability
from capabilities.geometry_solver import GeometrySolverCapability
from capabilities.knowledge_retriever import KnowledgeRetrieverCapability


class CapabilityFactory:

    @staticmethod
    def build_from_config(config):
        capabilities = []

        # --- existing capabilities ---
        if config.get("planner"):
            capabilities.append(PlannerCapability())

        if config.get("critic"):
            capabilities.append(CriticCapability())

        if config.get("reflection"):
            capabilities.append(ReflectionCapability())

        if config.get("retrieval"):
            capabilities.append(RetrievalCapability())

        # --- new math-specialized capabilities ---
        if config.get("knowledge_retriever"):
            # Goes first: injects theory before solving
            capabilities.append(KnowledgeRetrieverCapability())

        if config.get("formula_solver"):
            # Runs after knowledge injection, before final answer
            capabilities.append(FormulaSolverCapability())

        if config.get("geometry_solver"):
            capabilities.append(GeometrySolverCapability())

        if config.get("self_consistency"):
            # Goes last: validates the final answer
            capabilities.append(SelfConsistencyCapability())

        return capabilities