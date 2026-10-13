from typing import TypedDict

from app.investigation import investigate_movement


class InvestigationState(TypedDict, total=False):
    request: dict
    result: dict


def build_workflow():
    """Build a minimal LangGraph graph when the optional AI dependency is installed."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as error:
        raise RuntimeError("Install the 'ai' extra to use LangGraph orchestration") from error

    def investigate(state: InvestigationState) -> InvestigationState:
        return {"result": investigate_movement(**state["request"])}

    graph = StateGraph(InvestigationState)
    graph.add_node("investigate", investigate)
    graph.add_edge(START, "investigate")
    graph.add_edge("investigate", END)
    return graph.compile()
