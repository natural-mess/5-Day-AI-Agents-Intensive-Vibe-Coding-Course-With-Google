New-Item -ItemType Directory -Force -Path .\secure-agent-lab
Set-Location .\secure-agent-lab
git init
git config user.name "Kaggle Student"
git config user.email "student@example.com"
uv venv
. .\.venv\Scripts\Activate.ps1
uvx google-agents-cli setup
agents-cli info
