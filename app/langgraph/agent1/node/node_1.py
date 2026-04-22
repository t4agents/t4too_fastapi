from app.langgraph.agent1.tools.llm import llm, token_counter
from app.langgraph.agent1.schema.sch_llm import LLMState

# ---------------------------
# 3. Node wrappers
# ---------------------------
def llm_node(state: LLMState) -> dict:
    # Call your existing LLM function
    output = llm(state["prompt"])
    return {"llm_output": output, "prompt": state["prompt"]}

def token_counter_node(state: LLMState) -> dict:
    count = token_counter(state["prompt"])
    return {"token_count": count, "llm_output": state["llm_output"], "prompt": state["prompt"]}

# ---------------------------
