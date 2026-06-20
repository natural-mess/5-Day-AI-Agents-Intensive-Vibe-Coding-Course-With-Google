import os
import json
import google.auth

from pydantic import BaseModel
from google.adk.workflow import Workflow, START, node
from google.adk.events import RequestInput
from google.adk.agents.context import Context
from google.adk.apps import App

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

class State(BaseModel):
    expense_amount: float = 0.0
    status: str = "pending"
    human_review_input: str = ""

@node
def parse_message(ctx: Context):
    # Attempt to read the message from context events
    try:
        # The latest event is usually the user message
        text = ctx.last_event.content.parts[0].text
        if "50" in text:
            return {"expense_amount": 50.0}
        elif "150" in text:
            return {"expense_amount": 150.0}
    except Exception:
        pass
    return {"expense_amount": 0.0}

@node
def route_expense(ctx: Context, expense_amount: float):
    if expense_amount < 100:
        ctx.route = "auto_approve"
    else:
        ctx.route = "review"

@node
def auto_approve(expense_amount: float):
    return {"status": "approved"}

@node
def review_agent(human_review_input: str):
    if not human_review_input:
        # Request human input and pause
        return RequestInput(message="Expense is over $100. Please review.")
    return {"status": human_review_input}

expense_workflow = Workflow(
    name="expense_workflow",
    state_schema=State,
    edges=[
        (START, parse_message),
        (parse_message, route_expense),
        (route_expense, {
            "auto_approve": auto_approve,
            "review": review_agent
        })
    ]
)

app = App(
    root_agent=expense_workflow,
    name="expense-agent"
)
