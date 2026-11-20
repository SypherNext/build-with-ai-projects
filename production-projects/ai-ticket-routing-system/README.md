# AI Ticket Routing System (RouteBot)

Reference implementation for the "AI Ticket Routing System" Production
Project in Sypher's `build-with-ai` course. **RouteBot** is a multi-agent
support-ticket router built with LangGraph: a supervisor agent reads an
incoming ticket and decides which specialist (billing, technical, account,
or product) should handle it, the chosen specialist agent drafts a
resolution, and -- for tickets that span more than one specialty -- a
coordinator agent merges multiple specialist responses into one answer.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

- `app/state.py` -- the shared `RoutingState` / `SpecialistResponse` types (Build, Step 1)
- `app/prompts.py` -- the four specialist system prompts (Build, Step 2)
- `app/supervisor.py` -- the supervisor agent that decides routing (Build, Step 3)
- `app/specialists.py` -- the specialist agents that draft resolutions (Build, Step 4)
- `app/coordinator.py` -- merges responses for multi-specialty tickets (Build, Step 5)
- `app/graph.py` -- the LangGraph `StateGraph` wiring it all together (Build, Step 6)
- `app/runner.py` -- `route_ticket()`, the entrypoint used by both the demo script and the API (Build, Step 7)
- `app/fallback.py` / `app/cache.py` -- the routing fallback and in-memory response cache from the Deploy lesson
- `app/api.py` -- the FastAPI endpoint from the Deploy lesson

Note: the lesson's own Deploy stage doesn't include a Dockerfile or
docker-compose setup for this project -- only the FastAPI endpoint above --
so none is included here either.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # then add your ANTHROPIC_API_KEY
```

## Run the demo script

```bash
python -m app.runner
```

## Run the API locally

```bash
uvicorn app.api:app --reload --port 8000
```

```bash
curl -X POST http://localhost:8000/api/v1/route \
  -H "Content-Type: application/json" \
  -d '{"subject": "Refund for last month", "description": "I was charged twice for my subscription", "email": "customer@example.com"}'
```
