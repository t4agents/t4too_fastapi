# main.py
from pydantic import BaseModel
from typing_extensions import TypedDict
# ---------------------------
# 1. Request schema
# ---------------------------
class LLMRequest(BaseModel):
    prompt: str

# ---------------------------
# 2. Define the state for LangGraph
# ---------------------------
class LLMState(TypedDict):
    prompt: str
    llm_output: str
    token_count: int

class State(TypedDict):
    text: str
