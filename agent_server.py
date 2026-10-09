"""FastAPI chat endpoint and the English browser workspace."""
import argparse
import copy
import logging
import os
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
INITIAL_STATE = {
    "messages": [], "profile": {}, "candidates": [],
    "checker_feedback": None, "session_complete": False,
}


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    session_complete: bool
    profile: dict[str, Any] = Field(default_factory=dict)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    checker_feedback: dict[str, Any] | None = None
    steps: list[str] = Field(default_factory=list)


def create_api(demo=False, workflow=None):
    @asynccontextmanager
    async def lifespan(api):
        if not demo and api.state.workflow is None:
            from agents.workflow import app
            api.state.workflow = app
        yield

    api = FastAPI(title="Pharmacy Assistant", version="1.1.0", lifespan=lifespan)
    api.state.workflow = workflow
    sessions = {}
    # Serialize local consultations so two requests cannot overwrite a session.
    consultation_lock = threading.Lock()

    @api.get("/status")
    def status():
        return {"mode": "demo" if demo else "live", "live_chat": api.state.workflow is not None}

    @api.post("/chat", response_model=ChatResponse)
    def chat_endpoint(request: ChatRequest):
        if not request.query.strip():
            raise HTTPException(422, "Please enter a message.")
        if api.state.workflow is None:
            raise HTTPException(503, "Guided demo mode. Start the configured server in live mode to send messages.")
        session_id = request.session_id or str(uuid.uuid4())
        with consultation_lock:
            current_state = copy.deepcopy(sessions.get(session_id, INITIAL_STATE))
            current_state["messages"].append(("user", request.query.strip()))
            current_state["session_complete"] = False
            final_state, steps = current_state, []
            try:
                for mode, update in api.state.workflow.stream(current_state, stream_mode=["updates", "values"]):
                    if mode == "values":
                        final_state = update
                    else:
                        steps.extend(update.keys())
            except Exception:
                logging.exception("Consultation workflow failed")
                raise HTTPException(500, "The consultation could not be completed. Please retry your message.")
            reply = next((message for message in reversed(final_state["messages"]) if isinstance(message, str)), "Please ask a pharmacist to review your question.")
            complete = final_state.get("session_complete", False)
            if complete:
                sessions.pop(session_id, None)
            else:
                sessions[session_id] = final_state
            return ChatResponse(
                reply=reply, session_id=session_id, session_complete=complete,
                profile=final_state.get("profile", {}),
                candidates=final_state.get("candidates", []),
                checker_feedback=final_state.get("checker_feedback"), steps=steps,
            )

    @api.delete("/sessions/{session_id}")
    def reset_session(session_id: str):
        with consultation_lock:
            sessions.pop(session_id, None)
        return {"reset": True}

    @api.get("/")
    def root():
        return RedirectResponse("/ui/")

    api.mount("/ui", StaticFiles(directory=ROOT / "web", html=True), name="ui")
    return api


api = create_api(demo=os.getenv("PHARMACY_DEMO") == "1")

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser(description="Pharmacy Assistant API and English UI")
    parser.add_argument("--demo", action="store_true", help="Serve guided examples using only the UI dependencies")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    uvicorn.run(create_api(demo=args.demo), host="127.0.0.1", port=args.port)
