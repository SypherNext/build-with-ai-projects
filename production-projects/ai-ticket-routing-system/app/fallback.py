# app/fallback.py
def routing_fallback(state: dict) -> str:
    if state.get("routing_decision") == "multi":
        return "technical"  # Default to technical if supervisor is unsure
    return state["routing_decision"]
