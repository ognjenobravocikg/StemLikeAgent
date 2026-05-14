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

        if config.get("planner"):
            capabilities.append(PlannerCapability())
        if config.get("critic"):
            capabilities.append(CriticCapability())
        if config.get("reflection"):
            capabilities.append(ReflectionCapability())
        if config.get("retrieval"):
            capabilities.append(RetrievalCapability())
        if config.get("knowledge_retriever"):
            capabilities.append(KnowledgeRetrieverCapability())
        if config.get("formula_solver"):
            capabilities.append(FormulaSolverCapability())
        if config.get("geometry_solver"):
            capabilities.append(GeometrySolverCapability())


        if config.get("self_consistency"):
            capabilities.append(SelfConsistencyCapability())

        return capabilities