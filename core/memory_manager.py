import json

class MemoryManager:

    def __init__(self):

        self.memory_path = (
            "memory/evolution_memory.json"
        )

        with open(
            self.memory_path,
            "r"
        ) as f:

            self.memory = json.load(f)

    def record_result(
        self,
        capability,
        success,
    ):

        if success:
            self.memory[capability][
                "success"
            ] += 1

        else:
            self.memory[capability][
                "failure"
            ] += 1

        self.save()

    def get_capability_score(
        self,
        capability,
    ):

        stats = self.memory[capability]

        success = stats["success"]
        failure = stats["failure"]

        total = success + failure

        if total == 0:
            return 0.5

        return success / total

    def rank_capabilities(
        self,
        capabilities,
    ):

        ranked = sorted(
            capabilities,
            key=lambda c:
            self.get_capability_score(c),
            reverse=True,
        )

        return ranked

    def save(self):

        with open(
            self.memory_path,
            "w"
        ) as f:

            json.dump(
                self.memory,
                f,
                indent=2,
            )