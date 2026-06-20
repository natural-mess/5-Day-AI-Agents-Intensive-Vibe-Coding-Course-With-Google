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

import asyncio
import json
import logging
import os
from pathlib import Path
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.events.request_input import RequestInput
from google.genai import types

from expense_agent.agent import root_agent

# Configure standard Python logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("trace_generator")

# Disable cloud telemetry
os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"] = "false"
os.environ["OTEL_TO_CLOUD"] = "false"


def format_events_for_trace(events):
    formatted = []
    for e in events:
        node_path = e.node_info.path if e.node_info else "unknown"
        node_name = node_path.split("/")[-1].split("@")[0]
        
        # Extract main text content if available
        text_content = ""
        if e.content and e.content.parts:
            text_content = "".join(p.text for p in e.content.parts if p.text)
            
        # Add details from actions
        actions_str = ""
        if e.actions:
            if e.actions.state_delta:
                actions_str += f" State update: {json.dumps(e.actions.state_delta)}."
            if e.actions.route:
                actions_str += f" Routed to: {e.actions.route}."
                
        desc_text = f"Node [{node_name}] executed.{actions_str}"
        if text_content:
            desc_text += f" Output: {text_content}"
            
        formatted.append({
            "author": node_name,
            "content": {
                "role": "model",
                "parts": [{"text": desc_text}]
            }
        })
    return formatted


async def run_case(case_dict):
    eval_id = case_dict.get("eval_case_id") or case_dict.get("eval_id")
    prompt_text = case_dict["prompt"]["parts"][0]["text"]
    expense_data = json.loads(prompt_text)
    
    logger.info(f"Running case: {eval_id} (amount: ${expense_data.get('amount')})")
    
    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, session_service=session_service, app_name="expense-approval")
    
    user_id = "test-sub"
    session_id = f"eval-session-{eval_id}"
    
    await session_service.create_session(
        app_name="expense-approval",
        user_id=user_id,
        session_id=session_id
    )
    
    message_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt_text)]
    )
    
    events = []
    paused = False
    
    async for event in runner.run_async(
        new_message=message_content,
        user_id=user_id,
        session_id=session_id
    ):
        events.append(event)
        if isinstance(event, RequestInput):
            paused = True
            logger.info(f"Workflow paused at HITL step for case: {eval_id}")
            
    if paused:
        # Automate decision: Reject prompt injections, approve clean requests
        desc = expense_data.get("description", "").lower()
        is_injection = any(kw in desc for kw in [
            "bypass rule", "override instruction", "force approval",
            "bypass all rules", "auto-approve"
        ])
        decision = "REJECTED" if is_injection else "APPROVED"
        logger.info(f"Automating decision: {decision} (suspected injection: {is_injection})")
        
        resume_message = types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        name="decision",
                        id="decision",
                        response={"decision": decision}
                    )
                )
            ]
        )
        
        async for event in runner.run_async(
            new_message=resume_message,
            user_id=user_id,
            session_id=session_id
        ):
            events.append(event)
            
    # Retrieve final session state
    session = await session_service.get_session(
        app_name="expense-approval",
        user_id=user_id,
        session_id=session_id
    )
    
    # Format case for the output EvaluationDataset
    outcome = session.state.get("outcome") if session else None
    final_text = ""
    if outcome:
        final_text = f"Status: {outcome.get('status')}, Reason: {outcome.get('reason')}, Reviewer: {outcome.get('reviewer')}."
    else:
        final_text = "Workflow finished without final outcome."
        
    final_response = {
        "role": "model",
        "parts": [{"text": final_text}]
    }
    
    formatted_trace = {
        "eval_id": eval_id,
        "prompt": case_dict["prompt"],
        "responses": [{"response": final_response}],
        "agent_data": {
            "turns": [
                {
                    "turn_index": 0,
                    "turn_id": "turn_0",
                    "events": [
                        {
                            "author": "user",
                            "content": case_dict["prompt"]
                        }
                    ] + format_events_for_trace(events)
                }
            ]
        }
    }
    
    return formatted_trace


async def main():
    dataset_path = Path("tests/eval/datasets/basic-dataset.json")
    output_path = Path("artifacts/traces/generated_traces.json")
    
    logger.info(f"Loading evaluation dataset from: {dataset_path}")
    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)
        
    eval_cases = dataset.get("eval_cases", [])
    logger.info(f"Found {len(eval_cases)} evaluation cases.")
    
    traces = []
    for case in eval_cases:
        trace = await run_case(case)
        traces.append(trace)
        
    output_dataset = {
        "eval_cases": traces
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing {len(traces)} populated traces to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_dataset, f, indent=2)
        
    logger.info("Trace generation complete.")


if __name__ == "__main__":
    asyncio.run(main())
