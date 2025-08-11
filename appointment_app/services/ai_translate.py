from typing import Optional
from openai import OpenAI
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class AITranslate:
    """
    Simple translator using OpenAI Chat Completions.
    Requires OPENAI_API_KEY in the environment.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found. "
                "Please ensure it's set in your .env file or environment variables.\n"
                f"Current .env path: {env_path.absolute()}"
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

    @staticmethod
    def _build_system_prompt(from_language: str, to_language: str, text: str) -> str:
        return (
            'You are a professional translator. Your task is to translate the following text '
            f'from {from_language} to {to_language}, preserving meaning, tone, and style.\n\n'
            'Text:\n'
            f'"{text}"\n\n'
            'Only return the translated text without additional commentary or formatting.'
        )

    def translate(self, from_language: str, to_language: str, text: str) -> str:
        """
        Translate `text` from `from_language` to `to_language`.
        Returns only the translated text (no extra commentary).
        """
        system_prompt = self._build_system_prompt(from_language, to_language, text)

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0,  # deterministic for translations
        )

        # Grab the assistant's message content safely
        content: Optional[str] = None
        if resp.choices and resp.choices[0].message:
            content = resp.choices[0].message.content

        if not content:
            raise RuntimeError("No translation returned by the model.")

        return content.strip()


# # Example usage:
# translator = Translate(model="gpt-4o-mini")
# result = translator.translate("English", "Arabic", "Welcome to our platform! We are glad to have you here.")
# print(result)