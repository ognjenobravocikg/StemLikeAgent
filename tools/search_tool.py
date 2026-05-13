import os
import requests
from dotenv import load_dotenv

load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

class SearchTool:
    def search(self,query,num_results=3):
        url = "https://google.serper.dev/search"
        
        payload = {"q": query}
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        response = requests.post(url,json=payload,headers=headers)

        data = response.json()

        organic = data.get("organic",[])
        snippets = []

        for result in organic[:num_results]:
            title = result.get(
                "title",
                ""
            )

            snippet = result.get(
                "snippet",
                ""
            )

            snippets.append(
                f"TITLE: {title}\n"
                f"SNIPPET: {snippet}"
            )

        return "\n\n".join(snippets)