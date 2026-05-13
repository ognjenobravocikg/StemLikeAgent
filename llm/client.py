import os
import time

from dotenv import load_dotenv
from litellm import completion

load_dotenv()

API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

MODEL = ("openrouter/openai/gpt-oss-20b:free")


def ask_llm(
    system_prompt,
    user_prompt,
    retries=3,
):

    for attempt in range(retries):

        try:

            response = completion(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                api_key=API_KEY,
                base_url=(
                    "https://openrouter.ai/api/v1"
                ),
            )

            return (
                response
                .choices[0]
                .message.content
            )

        except Exception as e:

            print(
                f"LLM ERROR: {e}"
            )

            if attempt < retries - 1:

                wait_time = (
                    2 ** attempt
                )

                print(
                    f"Retrying in "
                    f"{wait_time}s..."
                )

                time.sleep(wait_time)

            else:

                return (
                    "LLM request failed."
                )