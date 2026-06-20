import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import google.auth
from google.adk.sessions import VertexAiSessionService
from vertexai.preview.reasoning_engines import ReasoningEngine

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize ADK Service
service = VertexAiSessionService()

# Ensure we have the proper credentials and project initialized globally
_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

AGENT_RUNTIME_ID = os.getenv("AGENT_RUNTIME_ID", "")
APP_NAME = "expense-agent"
USER_ID = "default-user"

class ActionRequest(BaseModel):
    action: str
    interrupt_id: str

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/pending")
async def get_pending():
    """Lists all sessions, fetches history, and identifies unresolved adk_request_input events."""
    try:
        response = service.list_sessions(app_name=APP_NAME, user_id=USER_ID)
        sessions_metadata = getattr(response, "sessions", response) # handle both models and raw list
        
        pending_approvals = []
        
        # Iterate over sessions
        for s_meta in sessions_metadata:
            session_id = getattr(s_meta, "id", s_meta.get("id")) if isinstance(s_meta, dict) else s_meta.id
            
            # Fetch full history
            full_session = service.get_session(
                app_name=APP_NAME, 
                user_id=USER_ID, 
                session_id=session_id
            )
            
            if not full_session or not full_session.events:
                continue
                
            # Track function calls and responses
            calls = {}
            responses = set()
            expense_payload = {}
            
            # Simple heuristic: last known expense payload
            if full_session.state and "expense_amount" in full_session.state:
                expense_payload["amount"] = full_session.state["expense_amount"]
                
            for event in full_session.events:
                # If there's an action, track state delta
                if event.actions and event.actions.state_delta:
                    if "expense_amount" in event.actions.state_delta:
                        expense_payload["amount"] = event.actions.state_delta["expense_amount"]
                
                # Check model content for function calls
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.function_call:
                            if part.function_call.name == "adk_request_input":
                                calls[part.function_call.id] = part.function_call
                        if part.function_response:
                            if part.function_response.name == "adk_request_input":
                                responses.add(part.function_response.id)
            
            # Identify unresolved
            for call_id, call in calls.items():
                if call_id not in responses:
                    # Unresolved interrupt!
                    pending_approvals.append({
                        "session_id": session_id,
                        "interrupt_id": call_id,
                        "expense_amount": expense_payload.get("amount", "Unknown"),
                        "args": call.args
                    })
                    
        return {"pending": pending_approvals}
    except Exception as e:
        print(f"Error fetching pending: {e}")
        return {"pending": []}

@app.post("/api/action/{session_id}")
async def resolve_action(session_id: str, payload: ActionRequest):
    """Resumes the paused session on Agent Runtime."""
    if not AGENT_RUNTIME_ID:
        raise HTTPException(status_code=500, detail="AGENT_RUNTIME_ID env var not set")
        
    try:
        # Load the reasoning engine using the deployed runtime ID
        engine = ReasoningEngine(AGENT_RUNTIME_ID)
        
        # Build the function_response part precisely as requested
        resume_message = {
            "role": "user",
            "parts": [
                {
                    "function_response": {
                        "id": payload.interrupt_id,
                        "name": "adk_request_input",
                        "response": {
                            "approved": payload.action == "approved",
                            "human_review_input": payload.action
                        }
                    }
                }
            ]
        }
        
        # Stream query back to the reasoning engine
        # We must use the specific argument signature of stream_query
        response = engine.stream_query(
            message=resume_message,
            user_id=USER_ID,
            session_id=session_id
        )
        
        final_text = ""
        for event in response:
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text
                        
        return {"status": "success", "agent_response": final_text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
