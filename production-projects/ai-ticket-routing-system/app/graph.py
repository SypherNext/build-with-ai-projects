# app/graph.py
from langgraph.graph import StateGraph, END
from app.state import RoutingState
from app.supervisor import supervisor_route
from app.specialists import call_specialist
from app.coordinator import coordinate_responses


def routing_node(state: RoutingState) -> dict:
    result = supervisor_route(state["subject"], state["description"])
    return {"routing_decision": result["decision"], "messages": [f"Routed: {result['decision']}"]}


def specialist_node(state: RoutingState) -> dict:
    decision = state["routing_decision"]
    if decision == "multi":
        responses = []
        for spec in ["billing", "technical", "account", "product"]:
            resp = call_specialist(spec, state["subject"], state["description"])
            responses.append(resp)
        resolution = coordinate_responses(responses, state["subject"])
        return {"specialist_responses": responses, "final_resolution": resolution, "status": "resolved"}
    else:
        resp = call_specialist(decision, state["subject"], state["description"])
        return {"specialist_responses": [resp], "final_resolution": resp["response"], "status": "resolved"}


def build_routing_graph():
    workflow = StateGraph(RoutingState)
    workflow.add_node("route", routing_node)
    workflow.add_node("handle", specialist_node)
    workflow.set_entry_point("route")
    workflow.add_edge("route", "handle")
    workflow.add_edge("handle", END)
    return workflow.compile()
