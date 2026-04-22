# main.py
from langgraph.graph import StateGraph, START, END

from app.langgraph.agent1.node.node_1 import llm_node, token_counter_node
from app.langgraph.agent1.schema.sch_llm import LLMState

def add_a(state) -> dict:
    return {"text": state["text"] + "a"}


# 4. Build the graph
# ---------------------------
workflow = StateGraph(LLMState)
workflow.add_node("LLM_Model", llm_node)
workflow.add_node("Get_Token_Counter", token_counter_node)
workflow.add_edge(START, "LLM_Model")
workflow.add_edge("LLM_Model", "Get_Token_Counter")
workflow.add_edge("Get_Token_Counter", END)

# Compile once at module level
compiled_workflow = workflow.compile()
