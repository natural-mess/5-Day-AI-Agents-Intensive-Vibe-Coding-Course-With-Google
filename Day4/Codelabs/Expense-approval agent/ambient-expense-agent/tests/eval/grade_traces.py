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

import json
import logging
import os
import yaml
from pathlib import Path
from google import genai
from google.genai import types

# Configure standard Python logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("local_grader")

# Disable cloud telemetry
os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"] = "false"
os.environ["OTEL_TO_CLOUD"] = "false"


def clean_json_text(text: str) -> str:
    """Cleans up markdown code blocks if the model wrapped the JSON response."""
    text = text.strip()
    if text.startswith("```"):
        # Remove first line
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def grade_case(client, case, metric):
    prompt_text = case.get("prompt", {}).get("parts", [{}])[0].get("text", "")
    
    # Extract response text
    responses = case.get("responses", [])
    response_text = ""
    if responses:
        parts = responses[0].get("response", {}).get("parts", [])
        if parts:
            response_text = parts[0].get("text", "")
            
    # Serialize agent data
    agent_data = case.get("agent_data") or {}
    agent_data_str = json.dumps(agent_data, indent=2)
    
    # Format the prompt template
    prompt_template = metric["prompt_template"]
    formatted_prompt = prompt_template.format(
        prompt=prompt_text,
        response=response_text,
        agent_data=agent_data_str
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=formatted_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        cleaned_text = clean_json_text(response.text)
        result = json.loads(cleaned_text)
        return int(result.get("score", 1)), str(result.get("explanation", "Failed to parse explanation."))
    except Exception as e:
        logger.error(f"Error grading case {case.get('eval_id')} for metric {metric['name']}: {e}")
        return 1, f"Grading failed: {e}"


def main():
    traces_path = Path("artifacts/traces/generated_traces.json")
    config_path = Path("tests/eval/eval_config.yaml")
    output_dir = Path("artifacts/grade_results")
    
    logger.info(f"Loading traces from: {traces_path}")
    with open(traces_path, encoding="utf-8") as f:
        traces_dataset = json.load(f)
        
    logger.info(f"Loading evaluation config from: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    metrics = config.get("custom_metrics", [])
    metrics_to_run = config.get("metrics_to_run", [])
    
    # Filter only metrics we want to run
    active_metrics = [m for m in metrics if m["name"] in metrics_to_run]
    
    eval_cases = traces_dataset.get("eval_cases", [])
    logger.info(f"Grading {len(eval_cases)} cases across {len(active_metrics)} metrics.")
    
    client = genai.Client(vertexai=True)
    
    results = {}
    summary = {}
    
    for metric in active_metrics:
        results[metric["name"]] = []
        scores = []
        for case in eval_cases:
            eval_id = case.get("eval_id")
            score, explanation = grade_case(client, case, metric)
            results[metric["name"]].append({
                "eval_id": eval_id,
                "score": score,
                "explanation": explanation
            })
            scores.append(score)
            
        summary[metric["name"]] = {
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "all_scores": scores
        }
        
    # Write local results artifact
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "local_results.json"
    logger.info(f"Saving evaluation results to: {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "results": results
        }, f, indent=2)
        
    # Generate visual summary table
    print("\n" + "="*80)
    print("                      LOCAL EVALUATION SUMMARY REPORT")
    print("="*80)
    print(f"{'Case ID':<30} | {'Routing Correctness':<20} | {'Security Containment':<20}")
    print("-"*80)
    
    case_ids = [case.get("eval_id") for case in eval_cases]
    for case_id in case_ids:
        r_score = next(r["score"] for r in results["routing_correctness"] if r["eval_id"] == case_id)
        s_score = next(r["score"] for r in results["security_containment"] if r["eval_id"] == case_id)
        print(f"{case_id:<30} | {r_score:<20} | {s_score:<20}")
        
    print("-"*80)
    print(f"{'Average Score':<30} | {summary['routing_correctness']['avg_score']:<20.2f} | {summary['security_containment']['avg_score']:<20.2f}")
    print("="*80)
    
    print("\nDETAILED PER-CASE EXPLANATIONS:")
    print("="*80)
    for case_id in case_ids:
        print(f"\n[Case: {case_id}]")
        print(f"  * Routing Correctness Score: {next(r['score'] for r in results['routing_correctness'] if r['eval_id'] == case_id)}/5")
        print(f"    Explanation: {next(r['explanation'] for r in results['routing_correctness'] if r['eval_id'] == case_id)}")
        print(f"  * Security Containment Score: {next(r['score'] for r in results['security_containment'] if r['eval_id'] == case_id)}/5")
        print(f"    Explanation: {next(r['explanation'] for r in results['security_containment'] if r['eval_id'] == case_id)}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
