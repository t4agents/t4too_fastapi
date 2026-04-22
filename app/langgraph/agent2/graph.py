from langgraph.graph import StateGraph, START, END

from app.langgraph.agent2.nodes import (
    decide_route_node,
    general_node,
    init_state,
    rag_node,
    sql_node,
)
from app.langgraph.agent2.state import Agent2State


workflow = StateGraph(Agent2State)
workflow.add_node("Init", init_state)
workflow.add_node("DecideRoute", decide_route_node)
workflow.add_node("RAG", rag_node)
workflow.add_node("SQL", sql_node)
workflow.add_node("General", general_node)
workflow.add_edge(START, "Init")
workflow.add_edge("Init", "DecideRoute")
workflow.add_conditional_edges(
    "DecideRoute",
    lambda state: state.get("route", "rag"),
    {
        "rag": "RAG",
        "sql": "SQL",
        "general": "General",
    },
)
workflow.add_edge("RAG", END)
workflow.add_edge("SQL", END)
workflow.add_edge("General", END)

compiled_workflow = workflow.compile()
