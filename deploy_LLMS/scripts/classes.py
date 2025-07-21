from pydantic import BaseModel

class PromptInput(BaseModel):
    prompt: str
    system_prompt: str = ""
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 256