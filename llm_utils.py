import json
import re
from pydantic import BaseModel


def ask_structured(llm, prompt: str, model: type[BaseModel], tries: int = 3):
    """Ask the LLM a question and get back a filled-in Pydantic form."""
    schema = json.dumps(model.model_json_schema())
    full_prompt = (
        f"{prompt}\n\n"
        f"Respond with ONLY valid JSON that matches this schema. "
        f"No explanation, no markdown fences.\n{schema}"
    )
    last_error = None
    for _ in range(tries):
        text = llm.invoke(full_prompt).content
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            return model.model_validate_json(match.group(0))
        except Exception as e:
            last_error = e   # bad JSON, so ask again
    raise ValueError(f"LLM did not return valid JSON after {tries} tries: {last_error}")