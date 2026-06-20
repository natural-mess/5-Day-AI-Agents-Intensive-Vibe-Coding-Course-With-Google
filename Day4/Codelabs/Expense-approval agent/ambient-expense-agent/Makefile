# Makefile for managing the ADK 2.0 Expense-Approval Agent

.PHONY: install playground generate-traces grade

install:
	uvx google-agents-cli install

playground:
	uv run uvicorn expense_agent.fast_api_app:app --host 127.0.0.1 --port 8080

generate-traces:
	uv run python tests/eval/generate_traces.py

grade:
	uvx google-agents-cli eval grade --traces artifacts/traces/generated_traces.json --config tests/eval/eval_config.yaml
