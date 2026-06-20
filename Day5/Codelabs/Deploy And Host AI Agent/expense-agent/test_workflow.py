import asyncio
from pydantic import BaseModel
from google.adk.workflow import Workflow, START, DEFAULT_ROUTE, node
from google.adk.events import RequestInput
from google.adk.agents.context import Context

class State(BaseModel):
    expense_amount: float = 0.0
    status: str = "pending"
    human_review_input: str = ""

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

workflow = Workflow(
    name="expense_workflow",
    state_schema=State,
    edges=[
        (START, route_expense, {
            "auto_approve": auto_approve,
            "review": review_agent
        })
    ]
)

if __name__ == "__main__":
    print("Graph built successfully!")
