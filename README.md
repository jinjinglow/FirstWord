# FirstWord

Offline-first desktop/web hybrid application for Singapore child safety case intake documentation and recommendation support.

The application records discussion audio, transcribes it locally with Faster-Whisper, summarises it locally through Ollama/Qwen2.5, compares the summary against a bundled MSF Break The Silence guidance snapshot, and stores only summaries and recommendations in SQLite.

## Safety Boundaries

- The app does not diagnose child abuse.
- It does not confirm abuse, generate criminal accusations, or override professional judgment.
- Raw audio is temporary and deleted after processing.
- Raw transcripts are held in memory only and are not stored.
- Recommendations are advisory and always display: "This is a recommendation support tool and does not replace professional judgment."

## Prerequisites

- Windows 10/11
- Node.js 18+
- Python 3.10+
- Ollama installed locally
- Qwen2.5 model pulled locally, for example `ollama pull qwen2.5:7b-instruct`
- Faster-Whisper model available locally or downloadable during setup

Runtime operation is offline-first. Do dependency/model installation before use in an online setup environment if needed.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install
npm run dev
```

The Electron window opens after the React frontend and FastAPI backend are healthy.

## Configuration

Environment variables can be placed in `.env`:

```text
APP_DB_PATH=local-data/app.db
WHISPER_MODEL_SIZE=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_PREDICT=1200
OLLAMA_TIMEOUT_SECONDS=300
```

Use `WHISPER_DEVICE=cuda` and a compatible compute type only on machines with CUDA configured. If transcription fails with `CUDA driver version is insufficient for CUDA runtime version`, either update the NVIDIA driver or set:

```text
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

FirstWord will also fall back to CPU `int8` automatically when CUDA fails with a driver/runtime mismatch.

### Ollama GPU Startup

Ollama runs as a separate local process. Project `.env` values configure this app's connection to Ollama, but they do not change an already-running Ollama process.

To start Ollama with a specific NVIDIA GPU from this project:

```powershell
.\scripts\start-ollama-gpu.ps1 -GpuId 0
```

Then load Qwen:

```powershell
ollama run qwen2.5:7b-instruct
```

Check placement:

```powershell
ollama ps
nvidia-smi
```

In `ollama ps`, the `PROCESSOR` column should show `100% GPU` or a CPU/GPU split. If it shows `100% CPU`, update the NVIDIA driver and restart Ollama.

## Data Storage

SQLite tables:

- `cases`
- `case_updates`
- `recommendations`

Stored fields include case IDs, timestamps, structured summaries, recommendation labels, rationales, contributing indicators, uncertainty notes, and user mode. Raw recordings and transcripts are never persisted.

## Approved Guidance Snapshot

The recommendation engine uses a bundled local snapshot derived from Singapore MSF Break The Silence pages for:

- SSSG and CARG roles
- Tier 1 and Tier 2 protection principles
- child protection system concepts
- signs of physical, sexual, emotional/psychological abuse and neglect

Refresh this snapshot only through a reviewed update process.
