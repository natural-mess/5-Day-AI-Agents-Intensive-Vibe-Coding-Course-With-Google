import vertexai
import json
from vertexai.preview.reasoning_engines import ReasoningEngine

def test_deployment():
    vertexai.init(project="antigravity-project-499816", location="us-east1")
    re = ReasoningEngine("projects/162241375902/locations/us-east1/reasoningEngines/8225719166275944448")
    
    print("\n--- Test 1: $50 Meal Expense ---")
    run_config = {"node_input": {"expense_amount": 50.0}}
    try:
        # Since stream_query yields events, let's just collect them
        events = list(re.stream_query(message="", user_id="test_user_1", run_config=run_config))
        print("Events:", [e for e in events])
    except Exception as e:
        print(f"Error querying 50.0: {e}")

    print("\n--- Test 2: $150 Client Dinner Expense ---")
    run_config2 = {"node_input": {"expense_amount": 150.0}}
    try:
        events2 = list(re.stream_query(message="", user_id="test_user_2", run_config=run_config2))
        print("Events:", [e for e in events2])
    except Exception as e:
        print(f"Error querying 150.0: {e}")

if __name__ == "__main__":
    test_deployment()
