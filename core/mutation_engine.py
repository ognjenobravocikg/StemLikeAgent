import copy

class MutationEngine:

    def mutate(
        self,
        config,
        capability_name,
    ):

        new_config = copy.deepcopy(config)

        new_config[capability_name] = True

        return new_config