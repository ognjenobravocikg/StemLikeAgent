from capabilities.base import Capability

class PlannerCapability(Capability):
    name = "planner"
    def process(self, question):
        return f'''
Break this problem into clear reasoning steps.

Question:
{question}

Then answer carefully.
'''