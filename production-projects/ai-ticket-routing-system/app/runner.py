# app/runner.py
from app.graph import build_routing_graph
from app.state import RoutingState
import uuid


def route_ticket(subject: str, description: str, email: str) -> dict:
    graph = build_routing_graph()
    initial = RoutingState(
        ticket_id=uuid.uuid4().hex[:12],
        subject=subject,
        description=description,
        customer_email=email,
        specialist_responses=[],
        status="pending",
        messages=[],
    )
    return graph.invoke(initial)


if __name__ == "__main__":
    result = route_ticket(
        "API timeout error",
        "Our API calls timeout after 30 seconds",
        "dev@company.com",
    )
    print(f"Routed to: {result['routing_decision']}")
    print(f"Resolution: {result['final_resolution'][:100]}")
