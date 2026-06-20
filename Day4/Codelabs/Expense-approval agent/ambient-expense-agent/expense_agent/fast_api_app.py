# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import uuid
import json
from typing import Any, Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from expense_agent.agent import root_agent

# Configure logging using standard Python logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("expense_approval_service")

# Setup telemetry: set otel_to_cloud=False
os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"] = "false"
os.environ["OTEL_TO_CLOUD"] = "false"

app = FastAPI(title="Ambient Expense-Approval Agent Service")

# Initialize Session Service & Runner
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, session_service=session_service, app_name="expense-approval")


def normalize_subscription(subscription_path: str) -> str:
    """Normalizes a fully-qualified subscription path down to a short name."""
    if subscription_path and "/" in subscription_path:
        return subscription_path.split("/")[-1]
    return subscription_path or "default-sub"


class PubSubMessage(BaseModel):
    data: Optional[str] = None
    messageId: Optional[str] = None
    publishTime: Optional[str] = None


class PubSubPayload(BaseModel):
    message: PubSubMessage
    subscription: Optional[str] = None


class ResumeRequest(BaseModel):
    user_id: str
    session_id: str
    decision: str


@app.post("/")
@app.post("/apps/expense_agent/trigger/pubsub")
async def handle_pubsub_event(payload: PubSubPayload):
    """Processes Pub/Sub push messages and runs the workflow."""
    logger.info(f"Received Pub/Sub payload: {payload.model_dump()}")
    
    # Normalize subscription path
    subscription_path = payload.subscription or "default-sub"
    user_id = normalize_subscription(subscription_path)
    
    message_id = payload.message.messageId or str(uuid.uuid4())
    session_id = message_id
    
    logger.info(f"Processing event for subscription: {user_id}, session_id: {session_id}")
    
    # Create the session in the session service
    await session_service.create_session(
        app_name="expense-approval",
        user_id=user_id,
        session_id=session_id
    )
    
    # Feed the entire payload as JSON string into the workflow runner
    message_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=json.dumps(payload.model_dump()))]
    )
    
    events = []
    try:
        async for event in runner.run_async(
            new_message=message_content,
            user_id=user_id,
            session_id=session_id
        ):
            events.append(event)
    except Exception as e:
        logger.exception("Error during workflow execution:")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

    # Fetch final session state to determine the outcome
    session = await session_service.get_session(
        app_name="expense-approval",
        user_id=user_id,
        session_id=session_id
    )
    
    outcome = session.state.get("outcome") if session else None
    risk_review = session.state.get("risk_review") if session else None
    
    response_data = {
        "user_id": user_id,
        "session_id": session_id,
        "completed": outcome is not None,
    }
    if outcome:
        response_data["outcome"] = outcome
    elif risk_review:
        response_data["status"] = "PAUSED_FOR_HITL"
        response_data["risk_review"] = risk_review
    else:
        response_data["status"] = "RUNNING"
        
    logger.info(f"Workflow execution response: {response_data}")
    return response_data


@app.post("/resume")
async def resume_hitl(request: ResumeRequest):
    """Resumes a paused workflow run with a human approval/rejection decision."""
    logger.info(f"Resuming HITL step for session: {request.session_id}, decision: {request.decision}")
    
    # Retrieve the paused session
    session = await session_service.get_session(
        app_name="expense-approval",
        user_id=request.user_id,
        session_id=request.session_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Construct the resume message with function response payload matching the interrupt_id
    resume_message = types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    name="decision",
                    id="decision",  # Matches the interrupt_id
                    response={"decision": request.decision}
                )
            )
        ]
    )
    
    events = []
    try:
        async for event in runner.run_async(
            new_message=resume_message,
            user_id=request.user_id,
            session_id=request.session_id
        ):
            events.append(event)
    except Exception as e:
        logger.exception("Error resuming workflow:")
        raise HTTPException(status_code=500, detail=f"Resuming workflow failed: {str(e)}")

    logger.info(f"Resumed events: {[e.model_dump() for e in events]}")

    # Fetch final outcome
    updated_session = await session_service.get_session(
        app_name="expense-approval",
        user_id=request.user_id,
        session_id=request.session_id
    )
    
    logger.info(f"Updated session state: {updated_session.state if updated_session else None}")
    outcome = updated_session.state.get("outcome") if updated_session else None
    
    return {
        "user_id": request.user_id,
        "session_id": request.session_id,
        "completed": outcome is not None,
        "outcome": outcome
    }
