import asyncio
from app.agent import expense_workflow

async def run_test():
    # Test case 1: Auto approve (< 100)
    print("--- Testing Auto Approve ---")
    response1 = await expense_workflow.run(input={"expense_amount": 50.0})
    print(f"Output: {response1}")

    # Test case 2: Human review (>= 100)
    print("\n--- Testing Review Agent ---")
    response2 = await expense_workflow.run(input={"expense_amount": 150.0})
    
    if hasattr(response2, 'interrupt_ids') and response2.interrupt_ids:
        print(f"Interrupts: {response2.interrupt_ids}")
        print("Simulating human approval...")
        # Assume response2 has a run_id or session, but let's just pass resume_inputs to a new run call
        response3 = await expense_workflow.run(
            input={"expense_amount": 150.0},
            resume_inputs={"review_agent": {"human_review_input": "approved"}} # Or similar depending on ADK
        )
        print(f"Output after resume: {response3}")
    else:
        print(f"Output: {response2}")

if __name__ == "__main__":
    asyncio.run(run_test())
