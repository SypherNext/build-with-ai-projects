# app/state.py
from typing import TypedDict, List, Optional, Literal


class SpecialistResponse(TypedDict):
    specialist: str
    response: str
    confidence: float
    resolution: Optional[str]


class RoutingState(TypedDict):
    ticket_id: str
    subject: str
    description: str
    customer_email: str
    routing_decision: Optional[str]  # billing, technical, account, product, multi
    specialist_responses: List[SpecialistResponse]
    final_resolution: Optional[str]
    status: str
    messages: List[str]
