from capabilities.base import Capability

class ReflectionCapability(Capability):
    name = "reflection"
    def process(self, question):

        return f"""
Answer the question carefully.

Then reflect on:
- possible mistakes
- missing reasoning
- unclear explanations

Improve the answer before finalizing.

Question:
{question}
"""