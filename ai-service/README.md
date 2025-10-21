# AI Service (FastAPI)

A lightweight FastAPI service for InterviewAI handling transcription (stub), TTS (stub), interview turn logic (stub), and question generation (basic heuristic for now).

## Quick start

1. Create a virtual environment and install deps

```
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2. Configure environment

Copy `.env.example` to `.env` and fill in values as needed.

3. Run the server

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Try it

- Health: GET http://localhost:8000/health
- Transcribe (stub): POST /transcribe with multipart/form-data field `audio`
- TTS (stub): POST /synthesize with `{ "text": "Hello" }`
- Interview turn (stub): POST /interview/turn
- Generate questions: POST /questions/generate

## Notes

- Real STT/LLM/TTS providers will be wired later via `services/` and `models/` interfaces.
- Keep endpoints stable; replace internals as providers are added.
