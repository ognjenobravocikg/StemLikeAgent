import json
from datetime import datetime

class ExperimentTracker:
    def __init__(self):
        timestamp = (
            datetime.now()
            .strftime("%Y%m%d_%H%M%S")
        )

        self.filepath = (
            f"experiments/run_{timestamp}.json"
        )
        self.logs = []

    def log(self,base_config,mutation,candidate_config,score,accepted,failure_type):
        entry = {
            "base_config": base_config,
            "mutation": mutation,
            "candidate_config": candidate_config,
            "score": score,
            "accepted": accepted,
            "failure_type": failure_type,
        }
        self.logs.append(entry)

    def save(self):

        with open(
            self.filepath,
            "w"
        ) as f:

            json.dump(
                self.logs,
                f,
                indent=2,
            )

        print(
            f"Experiment saved to "
            f"{self.filepath}"
        )