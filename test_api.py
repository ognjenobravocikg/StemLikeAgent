from llm.client import ask_llm

response = ask_llm(
    "You are helpful.",
    "Say hello."
)

print(response)