from capabilities.base import Capability

class CriticCapability(Capability):
    name = "critic"
    def process(self, question):

        return f"""
Answer the following question carefully.

After answering:
- review your own answer
- identify weaknesses
- improve the answer if necessary

Question:
{question}
"""