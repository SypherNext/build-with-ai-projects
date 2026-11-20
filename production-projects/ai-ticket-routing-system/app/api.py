# app/api.py
from fastapi import FastAPI
from app.runner import route_ticket
from pydantic import BaseModel

app = FastAPI(title="RouteBot API")


class TicketRequest(BaseModel):
    subject: str
    description: str
    email: str


@app.post("/api/v1/route")
def route(ticket: TicketRequest):
    result = route_ticket(ticket.subject, ticket.description, ticket.email)
    return {
        "ticket_id": result["ticket_id"],
        "routed_to": result["routing_decision"],
        "resolution": result["final_resolution"],
        "status": result["status"],
    }
