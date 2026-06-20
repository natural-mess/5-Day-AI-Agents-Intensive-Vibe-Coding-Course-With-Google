# ruff: noqa
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

import os
import google.auth

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events import Event, EventActions
from google.adk.workflow import Workflow, START
from google.genai import types
from pydantic import BaseModel, Field

# Force Vertex AI configuration to bypass depleted AI Studio prepayment credits
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
except Exception:
    pass


# Define Pydantic model for structured classification
class Classification(BaseModel):
    is_shipping_related: bool = Field(
        description="True if the user's query is about shipping rates, tracking, delivery, or returns. False otherwise."
    )
    reason: str = Field(description="A brief explanation for the classification.")


# 1. Preprocess Node: Extracts the query text and stores it in session state
def preprocess_query(ctx: Context, node_input: types.Content) -> Event:
    query = ""
    if node_input and node_input.parts:
        query = node_input.parts[0].text or ""
    return Event(
        output=query,
        actions=EventActions(state_delta={"original_query": query}),
    )


# 2. Classifier Node: LLM Agent to classify the query string
classifier = LlmAgent(
    name="classifier",
    model="gemini-3.5-flash",
    instruction=(
        "You are a routing classifier. Determine if the user's query is related to "
        "shipping (rates, tracking, delivery, returns) or unrelated. "
        "Provide your output strictly adhering to the schema."
    ),
    output_schema=Classification,
)


# 3. Router Node: Function node to route based on classifier results
def route_classification(node_input: dict) -> Event:
    is_shipping = node_input.get("is_shipping_related", False)
    if is_shipping:
        return Event(output=node_input, actions=EventActions(route="shipping"))
    return Event(output=node_input, actions=EventActions(route="unrelated"))


# Callback to safely initialize the state variable and avoid KeyErrors
async def initialize_state(callback_context: CallbackContext) -> None:
    state = callback_context.state
    if "original_query" not in state:
        state["original_query"] = ""


# 4. Shipping FAQ Agent Node: LLM Agent with knowledge of shipping policies
shipping_faq_agent = LlmAgent(
    name="shipping_faq_agent",
    model="gemini-3.5-flash",
    instruction="""You are a helpful, friendly, and enthusiastic customer support representative for a shipping company. 
Answer the user's shipping question: "{original_query}"

Based on these policies:
- Shipping Rates (Respond with excitement!):
  - Standard Shipping: $5.00 flat rate (3-5 business days). 🚚
  - Express Shipping: $15.00 flat rate (1-2 business days). ⚡
  - Free Shipping: FREE standard shipping on all orders over **$50.00**! 🎉
  - (When answering shipping rates, be very playful, use emojis, and make sure to highlight the free shipping threshold!)

- Tracking:
  - Tracking numbers look like 'TRK' followed by 6 digits (e.g., TRK123456).
  - If the user provides a tracking number, report the mock status: "In Transit - Estimated Delivery: 2 days".
  - If they ask about tracking but don't provide a tracking number, ask them to provide one.

- Delivery:
  - Deliveries are made Monday through Saturday, from 8 AM to 8 PM.
  - No deliveries on Sundays or major holidays.

- Returns:
  - Returns are accepted within 30 days of delivery.
  - Return shipping is free using our pre-paid return label.
  - Refunds are processed within 5-7 business days after we receive the returned item.

Be polite, professional, clear, and bring positive energy!""",
    before_agent_callback=initialize_state,
)


# 5. Decline Node: Function node to politely decline answering unrelated queries
def decline_node(node_input: dict) -> Event:
    message = (
        "I'm sorry, but I can only help you with shipping-related inquiries "
        "(such as rates, tracking, delivery, or returns). How can I assist you "
        "with your shipping needs today?"
    )
    return Event(
        output=message,
        content=types.Content(role="model", parts=[types.Part.from_text(text=message)]),
    )


# Assemble the Graph Workflow
root_agent = Workflow(
    name="customer_support_agent",
    edges=[
        (START, preprocess_query),
        (preprocess_query, classifier),
        (classifier, route_classification),
        (
            route_classification,
            {"shipping": shipping_faq_agent, "unrelated": decline_node},
        ),
    ],
    description="Customer support routing agent for a shipping company.",
)

app = App(
    root_agent=root_agent,
    name="app",
)
