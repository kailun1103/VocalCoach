# Speak Practice

Multimodal English conversation practice with a FastAPI backend (Whisper STT + Piper TTS + local LLM proxy) and a Vite/React frontend.

## Project Layout

```
backend/
  app/
    api/
      dependencies.py      # FastAPI dependency singletons (services, paths)
      routes/              # REST + form endpoints grouped by domain
      workflows/           # Shared request/response helpers
    core/
      config.py            # Pydantic settings
      logging.py           # Logging bootstrap
    schemas/               # Pydantic models for API payloads
    services/              # Whisper, Piper, LLM client wrappers
    ui/                    # Lightweight HTML testing forms
    main.py                # FastAPI app factory & frontend mounting
frontend/
  src/
    components/            # Reusable UI blocks (chat message list, composer, etc.)
    hooks/                 # Browser/device hooks (WAV recorder, localStorage)
    modules/
      chat/                # Chat-specific helpers
      i18n/                # Translation resources
      settings/            # App-level settings context
    pages/                 # Page-level React components
  index.html / vite config # Standard Vite tooling
whisper.cpp/               # Whisper runtime binaries (as provided)
data/                      # Persisted audio artifacts (created at runtime)
```

## Backend

- **Runtime**: Python 3.11+, FastAPI, httpx.
- **Entrypoint**: `backend/app/main.py`.
- **Configuration**: environment variables or `.env`, parsed via `backend/app/core/config.py`.
- **Services**:
  - Whisper STT (`backend/app/services/stt.py`)
  - Piper TTS (`backend/app/services/tts.py`)
  - OpenAI-compatible LLM proxy (`backend/app/services/llm.py`)
- **API structure**:
  - JSON endpoints in `backend/app/api/routes/speech.py`, `chat.py`, `translation.py`
  - Form-based test UI in `backend/app/api/routes/forms.py`
  - Shared request/response helpers in `backend/app/api/workflows/speech.py`

### Run the backend

cd "c:\Users\d93xj\OneDrive\Desktop\speak practice\backend" ; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Frontend

- **Runtime**: Node 18+, Vite, React, TypeScript.
- **State**: `frontend/src/modules/settings/SettingsContext.tsx` stores API base, language, streaming preference.
- **Chat UI**:
  - `frontend/src/pages/ChatPage.tsx` orchestrates chat behaviour.
  - `frontend/src/components/chat/ChatMessageList.tsx` renders the transcript + translations.
  - `frontend/src/components/chat/ChatComposer.tsx` handles input, controls, recorder status.
  - Audio recording handled by `frontend/src/hooks/useWavRecorder.ts`.

### Run the frontend

cd "c:\Users\d93xj\OneDrive\Desktop\speak practice\frontend" ; npm run dev

## Development Notes

- Backend audio artifacts land in `data/audio` by default; adjust via `DATA_DIRECTORY` env var.
- Place Whisper/Piper binaries under `backend/app/model` (see `core/config.py` defaults).
- Update `frontend/.env` (copy from `.env.example`) when pointing to a remote backend.
- Run `npm run build` and start the backend to serve the SPA from `/app`.
