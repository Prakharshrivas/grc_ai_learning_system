# GRC AI-Guided Learning System

AI-powered video learning platform for GRC (Governance, Risk, and Compliance) workflows. Features a split-pane UI with synchronized video playback and a grounded AI Q&A chatbot that answers exclusively from approved content with clickable timestamp citations.

## Quick Start

### Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- [Node.js](https://nodejs.org/) 18+
- A [Google Gemini API key](https://aistudio.google.com/apikey)

### 1. Clone and Create the Environment

```bash
git clone <repo-url>
cd grc-ai-learning-system
conda env create -f environment.yml
conda activate grc_ai
```

This installs Python 3.11, FFmpeg, and all backend dependencies in one step.

### 2. Configure API Keys

Copy the example and add your key:

```bash
cp .env.example .env
```

Edit `.env`:

```
GEMINI_API_KEY=your_actual_gemini_key
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Seed the Database

```bash
cd backend
python database/seed.py
```

### 5. Start the App (two terminals)

**Terminal 1 -- Backend:**

```bash
conda activate grc_ai
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 -- Frontend:**

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

## Architecture

```
Video Ingestion (FFmpeg + Gemini) → Knowledge Base (SQLite) → AI Engine (Claude + FastAPI) → UI (React + Tailwind)
```

### Backend (`/backend`)

| Component | Description |
|-----------|-------------|
| `ingestion/` | FFmpeg frame/audio extraction + Gemini transcript generation |
| `database/` | SQLite schema, seed script, models |
| `engine/` | System prompt, context assembly, citation parser, LLM answer engine |
| `api/` | FastAPI routes for Q&A, workflows, video serving, progress tracking |

### Frontend (`/frontend`)

| Component | Description |
|-----------|-------------|
| `VideoPanel` | HTML5 video player with step progress tracking |
| `ChatPanel` | AI chat with clickable `[STEP X, MM:SS]` citations |
| `StepList` | Step-by-step progress sidebar |
| Hooks | `useVideoSync` (video-step sync), `useChat` (session-based chat) |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/workflows` | List all approved workflows |
| GET | `/api/workflows/{id}` | Get workflow with steps and FAQs |
| GET | `/api/workflows/{id}/suggestions` | Context-aware question suggestions |
| POST | `/api/ask` | Ask a question (grounded Q&A) |
| GET | `/api/video/{id}` | Serve workflow video file |
| POST | `/api/progress` | Update user progress |
| POST | `/api/feedback` | Submit helpful/not_helpful feedback |

## Docker

### Prerequisites

- Docker and Docker Compose

### Run with Docker

```bash
# Add your API key to .env first, then:
docker compose up --build
```

- Frontend: **http://localhost:3000**
- Backend API: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**

The database auto-seeds on first startup from `approved_workflows/*.json`. Video files are mounted read-only from `video_data/`.

### Stop

```bash
docker compose down
```

## Managing Videos

The source of truth is the JSON files in `approved_workflows/`. The database is rebuilt from those files every time you run the seed script.

### Adding a New Video

1. Place the MP4 in `video_data/`.

2. Generate the transcript (requires `GEMINI_API_KEY` in `.env`):

```bash
conda activate grc_ai
cd backend
python -c "
from ingestion.generate_transcript import generate_transcript, save_transcript
from config import VIDEO_DATA_DIR, APPROVED_WORKFLOWS_DIR

video = VIDEO_DATA_DIR / 'your_new_video.mp4'
transcript = generate_transcript(video)
save_transcript(transcript, APPROVED_WORKFLOWS_DIR / 'your_new_workflow.json')
"
```

3. Review and edit the generated JSON in `approved_workflows/your_new_workflow.json` for accuracy.

4. Re-seed the database:

```bash
python database/seed.py
```

The new workflow appears in the UI immediately.

### Removing a Video

1. Delete the JSON file from `approved_workflows/`.
2. Optionally delete the MP4 from `video_data/`.
3. Re-seed the database:

```bash
cd backend
python database/seed.py
```

### Bulk Processing All Videos

To generate transcripts for every MP4 in `video_data/` at once:

```bash
cd backend
python ingestion/generate_transcript.py
python database/seed.py
```
