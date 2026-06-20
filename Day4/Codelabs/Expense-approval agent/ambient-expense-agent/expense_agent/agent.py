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

import datetime
import json
import base64
import os
from typing import Any, AsyncGenerator
from pydantic import BaseModel, Field

import google.auth
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.workflow import Workflow, START, node
from google.adk.events.event import Event
from google.adk.agents.context import Context
from google.adk.events.request_input import RequestInput
from google.genai import types

from expense_agent.config import THROTTLE_THRESHOLD, get_model

# Load environment variables
load_dotenv()

# Attempt to configure project automatically if not set
try:
    _, project_id = google.auth.default()
    if project_id and not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    pass

if not os.environ.get("GOOGLE_CLOUD_LOCATION"):
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
if not os.environ.get("GOOGLE_GENAI_USE_VERTEXAI"):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# ---------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------

class Expense(BaseModel):
    amount: float = Field(description="The total amount of the expense report")
    submitter: str = Field(description="The person who submitted the expense report")
    category: str = Field(description="The category of the expense (e.g. Travel, Meals, Software)")
    description: str = Field(description="A brief description of what the expense was for")
    date: str = Field(description="The date the expense occurred (YYYY-MM-DD)")


class RiskReview(BaseModel):
    risk_factors: list[str] = Field(description="Identified risk factors, if any")
    risk_score: int = Field(description="Risk score between 1 (lowest risk) and 10 (highest risk)")
    summary: str = Field(description="Detailed summary explaining the risk assessment and findings")


# ---------------------------------------------------------------------
# Workflow Nodes
# ---------------------------------------------------------------------

def parse_expense_report(ctx: Context, node_input: Any) -> Event:
    """Parses raw JSON input or base64-encoded Pub/Sub payloads into an Expense model."""
    raw_text = ""
    if isinstance(node_input, str):
        raw_text = node_input
    elif isinstance(node_input, dict):
        raw_text = json.dumps(node_input)
    elif hasattr(node_input, "parts") and node_input.parts:
        raw_text = "".join(part.text for part in node_input.parts if part.text)
    elif isinstance(node_input, list):
        raw_text = "".join(getattr(p, "text", "") for p in node_input)
    
    try:
        payload = json.loads(raw_text)
    except Exception:
        raise ValueError(f"Could not parse input as JSON: {raw_text}")
    
    # Handle Pub/Sub structure: payload might have "message" -> "data" or just "data"
    data_content = None
    if isinstance(payload, dict):
        if "message" in payload and isinstance(payload["message"], dict) and "data" in payload["message"]:
            data_content = payload["message"]["data"]
        elif "data" in payload:
            data_content = payload["data"]
        else:
            data_content = payload
    else:
        data_content = payload

    expense_dict = None
    if isinstance(data_content, str):
        try:
            decoded = base64.b64decode(data_content).decode("utf-8")
            expense_dict = json.loads(decoded)
        except Exception:
            try:
                expense_dict = json.loads(data_content)
            except Exception:
                raise ValueError(f"Could not decode or parse data content string: {data_content}")
    elif isinstance(data_content, dict):
        expense_dict = data_content
    else:
        raise ValueError(f"Invalid data content type: {type(data_content)}")

    expense = Expense(
        amount=float(expense_dict.get("amount", 0.0)),
        submitter=str(expense_dict.get("submitter", "Unknown")),
        category=str(expense_dict.get("category", "General")),
        description=str(expense_dict.get("description", "")),
        date=str(expense_dict.get("date", "")),
    )

    return Event(output=expense, state={"expense": expense.model_dump()})


def route_gate(node_input: Expense) -> Event:
    """Routes the expense report depending on whether the amount is below or above the threshold."""
    if node_input.amount < THROTTLE_THRESHOLD:
        return Event(output=node_input, route="auto_approve")
    else:
        return Event(output=node_input, route="requires_review")


def auto_approve(node_input: Expense) -> Event:
    """Instantly auto-approves expenses under the threshold."""
    outcome = {
        "status": "APPROVED",
        "reason": f"Auto-approved (under ${THROTTLE_THRESHOLD})",
        "reviewer": "System",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    msg = f"Expense of ${node_input.amount:.2f} by {node_input.submitter} for {node_input.category} was auto-approved."
    return Event(
        output=outcome,
        state={"outcome": outcome},
        content=types.Content(role="model", parts=[types.Part.from_text(text=msg)])
    )


# ---------------------------------------------------------------------
# Security Controls
# ---------------------------------------------------------------------
import re

SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CC_PATTERN = re.compile(r'\b(?:\d{4}[ -]?){3}\d{4}\b')

PROMPT_INJECTION_KEYWORDS = [
    "ignore instruction", "ignore previous", "override rule", "bypass rule", 
    "force approval", "auto-approve", "system prompt", "system instruction",
    "ignore the rules", "bypass the audit", "do not audit"
]

def scrub_pii(text: str) -> tuple[str, list[str]]:
    """Scrubs SSNs and Credit Card numbers from text."""
    redacted = []
    scrubbed = text
    if SSN_PATTERN.search(scrubbed):
        scrubbed = SSN_PATTERN.sub('[REDACTED_SSN]', scrubbed)
        redacted.append('SSN')
    if CC_PATTERN.search(scrubbed):
        scrubbed = CC_PATTERN.sub('[REDACTED_CC]', scrubbed)
        redacted.append('Credit Card')
    return scrubbed, redacted

def detect_prompt_injection(text: str) -> bool:
    """Checks for prompt injection keywords in text."""
    normalized = text.lower()
    for phrase in PROMPT_INJECTION_KEYWORDS:
        if phrase in normalized:
            return True
    return False

def security_checkpoint(ctx: Context, node_input: Expense) -> Event:
    """Checkpoint node to scrub PII and check for prompt injection."""
    desc = node_input.description
    scrubbed_desc, redacted_categories = scrub_pii(desc)
    
    clean_expense = Expense(
        amount=node_input.amount,
        submitter=node_input.submitter,
        category=node_input.category,
        description=scrubbed_desc,
        date=node_input.date,
    )
    
    if detect_prompt_injection(scrubbed_desc):
        # Flag prompt injection, bypass LLM review, route to human
        risk_review = RiskReview(
            risk_factors=["POSSIBLE PROMPT INJECTION DETECTED"],
            risk_score=10,
            summary="Security Checkpoint: Bypassed LLM review due to suspected prompt injection in description."
        )
        return Event(
            output=risk_review,
            route="security_alert",
            state={
                "expense": clean_expense.model_dump(),
                "risk_review": risk_review.model_dump(),
                "redacted_categories": redacted_categories
            }
        )
        
    return Event(
        output=clean_expense,
        route="clean",
        state={
            "expense": clean_expense.model_dump(),
            "redacted_categories": redacted_categories
        }
    )

# Model-driven node reviewing expense for risk factors
llm_review = LlmAgent(
    name="llm_review",
    model=get_model(),
    instruction="""You are a financial risk auditor.
Analyze the following expense details for potential risk factors (e.g. duplicate submissions, high amounts for the category, vague descriptions, compliance issues):

Expense Details: {expense}

Provide your risk score, identify any risk factors, and summarize your findings in the requested schema.""",
    output_schema=RiskReview,
    output_key="risk_review",
)


@node(rerun_on_resume=True)
async def human_approval(ctx: Context, node_input: RiskReview) -> AsyncGenerator[Any, Any]:
    """Pauses the workflow to request human approval/rejection based on the LLM risk review."""
    if not ctx.resume_inputs or "decision" not in ctx.resume_inputs:
        risk_review_dict = ctx.state.get("risk_review", {})
        expense_dict = ctx.state.get("expense", {})
        redacted = ctx.state.get("redacted_categories", [])
        
        alert_flag = "⚠️ "
        if "POSSIBLE PROMPT INJECTION DETECTED" in risk_review_dict.get("risk_factors", []):
            alert_flag = "🚨 SECURITY ALERT: "
            
        message = (
            f"{alert_flag}Expense approval required for ${expense_dict.get('amount', 0.0):.2f} (submitted by {expense_dict.get('submitter', 'Unknown')}).\n"
            f"Risk Score: {risk_review_dict.get('risk_score', 0)}/10\n"
            f"Summary: {risk_review_dict.get('summary', 'No summary provided')}\n"
            f"Risk Factors: {', '.join(risk_review_dict.get('risk_factors', []))}\n"
        )
        if redacted:
            message += f"Redacted PII: {', '.join(redacted)}\n"
        message += f"Description: {expense_dict.get('description', '')}\n\n"
        message += "Please respond with 'APPROVED' or 'REJECTED' to finalize the report."
        
        yield RequestInput(
            interrupt_id="decision",
            message=message
        )
        return

    raw_decision = ctx.resume_inputs["decision"]
    if isinstance(raw_decision, dict):
        decision_text = str(raw_decision.get("decision") or raw_decision.get("response") or list(raw_decision.values())[0]).strip().upper()
    else:
        decision_text = str(raw_decision).strip().upper()
    status = "APPROVED" if "APPROVE" in decision_text else "REJECTED"

    outcome = {
        "status": status,
        "reason": f"Manual decision: {decision_text}",
        "reviewer": "Human",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    msg = f"Expense has been manually {status}. Feedback received: {decision_text}"
    yield Event(
        output=outcome,
        state={"outcome": outcome},
        content=types.Content(role="model", parts=[types.Part.from_text(text=msg)])
    )


# ---------------------------------------------------------------------
# Graph Definition
# ---------------------------------------------------------------------

root_agent = Workflow(
    name="expense_approval_workflow",
    edges=[
        (START, parse_expense_report),
        (parse_expense_report, route_gate),
        (route_gate, {
            "auto_approve": auto_approve,
            "requires_review": security_checkpoint
        }),
        (security_checkpoint, {
            "clean": llm_review,
            "security_alert": human_approval
        }),
        (llm_review, human_approval),
    ]
)

app = App(
    root_agent=root_agent,
    name="expense_approval_app",
)
