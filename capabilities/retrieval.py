from capabilities.base import Capability
from tools.search_tool import (SearchTool)

class RetrievalCapability(Capability):
    name = "retrieval"
    def __init__(self):
        self.search_tool = SearchTool()

    def process(self, question):
        print(f"SEARCHING WEB FOR: {question}")
        evidence = self.search_tool.search(question)

        enhanced_prompt = f"""
Use the following retrieved web evidence
when answering.

WEB EVIDENCE:
{evidence}

QUESTION:
{question}

Answer carefully using the evidence.
"""
        
        return enhanced_prompt