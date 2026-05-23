python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install
Write-Host "Setup complete. Ensure Ollama is running and qwen2.5 is available, then run npm run dev."
