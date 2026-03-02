# GRC AI-Guided Learning System — System Design Architecture

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GRC AI LEARNING SYSTEM                          │
│                                                                         │
│   Video Ingestion → Knowledge Base → AI Answer Engine → Split-Pane UI  │
│                                                                         │
│   Core Problem: Users struggle with complex GRC workflows              │
│   Solution: AI-guided video learning with grounded Q&A + citations     │
└─────────────────────────────────────────────────────────────────────────┘
```

**What the system does:**
- Converts workflow screen recordings into rich, timestamped knowledge documents
- Stores approved content in a structured database
- Provides a grounded AI Q&A engine that answers ONLY from approved content
- Delivers a split-pane UI (video + chat) with clickable timestamp citations
- Tracks user progress and logs all interactions for audit

---

## 2. High-Level Architecture

```
                    ┌──────────────┐
                    │  SME / Admin │
                    └──────┬───────┘
                           │ uploads video
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INGESTION PIPELINE                            │
│                                                                 │
│  MP4 Video ──► FFmpeg ──┬──► Frames (JPG, 1/3s)──┐             │
│                         │                         ├──► Gemini   │
│                         └──► Audio (MP3) ─────────┘   1.5 Pro  │
│                                                         │       │
│                                              Rich Transcript    │
│                                              (timestamped doc)  │
│                                                         │       │
│                                              Human Review &     │
│                                              Approval Gate      │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ approved doc
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE BASE (PostgreSQL)                   │
│                                                                 │
│  ┌────────────┐ ┌────────────────┐ ┌──────────────┐            │
│  │ workflows  │ │ workflow_steps │ │ workflow_faqs│            │
│  │ (metadata) │ │ (timestamped)  │ │ (Q&A pairs)  │            │
│  └────────────┘ └────────────────┘ └──────────────┘            │
│  ┌──────────────────┐ ┌──────────────────────────┐             │
│  │ interaction_log  │ │ user_workflow_progress    │             │
│  │ (audit trail)    │ │ (completion tracking)     │             │
│  └──────────────────┘ └──────────────────────────┘             │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ context assembly
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AI ANSWER ENGINE (FastAPI)                     │
│                                                                 │
│  POST /api/ask { workflow_id, question, user_role, session_id } │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐         │
│  │ System Prompt │  │ Claude       │  │ Citation      │         │
│  │ (6 guardrail │──│ Sonnet 4.5   │──│ Parser        │         │
│  │  rules)       │  │              │  │ [STEP X,MM:SS]│         │
│  └──────────────┘  └──────────────┘  └───────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │ Session      │  │ Safety       │                             │
│  │ Memory       │  │ Testing      │                             │
│  │ (last 5 Q&A) │  │ Suite        │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ JSON response
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTEND (React + Tailwind)                   │
│                                                                 │
│  ┌──────────────────────┐  ◄──SYNC──►  ┌────────────────────┐  │
│  │ VIDEO PANEL           │              │ AI CHAT PANEL      │  │
│  │ - Video.js player     │              │ - Grounded Q&A     │  │
│  │ - seekTo(timestamp)   │              │ - Clickable [STEP] │  │
│  │ - Step progress bar   │              │ - Suggested Qs     │  │
│  │ - Step list tracker   │              │ - Session history  │  │
│  └──────────────────────┘              └────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TRACKING: Completion % │ Steps watched │ Audit log      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details

### 3.1 Ingestion Pipeline

**Purpose:** Convert raw workflow video into a structured, timestamped knowledge document.

```
Input:  MP4 video (3-7 min, 720p+, screen recording + voice narration)

Step 1: Frame Extraction (FFmpeg)
        ffmpeg -i video.mp4 -vf "fps=1/3" -q:v 2 frames/frame_%04d.jpg
        → 1 frame every 3 seconds
        → 5 min video = ~100 frames

Step 2: Audio Extraction (FFmpeg)
        ffmpeg -i video.mp4 -vn -acodec libmp3lame -q:a 2 audio.mp3

Step 3: Multimodal Processing (Gemini 1.5 Pro)
        Input: all frames + audio + system prompt
        Output: 2,000-5,000 word structured document containing:
          - Workflow metadata (title, purpose, roles, prerequisites)
          - Step-by-step guide with timestamps
          - Per-step: navigation path, on-screen description, action, narration, notes
          - 8-10 pre-generated FAQ pairs

Step 4: Human Review & Approval
        SME validates: UI element names, step sequence, timestamps,
        compliance notes, FAQ accuracy
        Status: DRAFT → APPROVED (only approved content enters the system)
```

### 3.2 Knowledge Base (PostgreSQL)

**Purpose:** Store approved workflow documents in a queryable, structured format.

```
TABLE: workflows
  id              UUID PK
  title           TEXT
  purpose         TEXT
  video_url       TEXT
  video_duration  INTEGER (seconds)
  roles           TEXT[]
  status          ENUM (draft, approved, archived)
  version         INTEGER
  approved_by     TEXT
  approved_at     TIMESTAMP

TABLE: workflow_steps
  id              UUID PK
  workflow_id     UUID FK → workflows
  step_number     INTEGER
  title           TEXT
  start_time      INTEGER (seconds)
  end_time        INTEGER (seconds)
  navigation      TEXT (click path)
  on_screen       TEXT (visual description)
  action          TEXT
  narration       TEXT
  important_notes TEXT

TABLE: workflow_faqs
  id              UUID PK
  workflow_id     UUID FK → workflows
  question        TEXT
  answer          TEXT
  related_step    INTEGER

TABLE: interaction_log
  id              UUID PK
  user_id         TEXT
  workflow_id     UUID FK
  session_id      UUID
  user_question   TEXT
  ai_response     TEXT
  cited_steps     INTEGER[]
  timestamp       TIMESTAMP
  feedback        ENUM (helpful, not_helpful, null)

TABLE: user_workflow_progress
  user_id         TEXT
  workflow_id     UUID FK
  steps_watched   INTEGER[]
  steps_confirmed INTEGER[]
  questions_asked INTEGER
  completion_pct  DECIMAL (0.0 to 1.0)
  started_at      TIMESTAMP
  completed_at    TIMESTAMP
  status          ENUM (not_started, in_progress, completed)
```

**Context Assembly Function:**

```
assemble_context(workflow_id):
  → SELECT workflow metadata, all steps (ordered), all FAQs
  → Format into a single text block (~2K-4K tokens per workflow)
  → Inject into LLM system prompt at query time

Note: No vector DB needed at MVP. 50 workflows still fit in a
modern LLM context window. Add retrieval only when content > ~100K tokens.
```

### 3.3 AI Answer Engine (FastAPI)

**Purpose:** Grounded Q&A that answers ONLY from approved content, with timestamp citations.

```
API Endpoint: POST /api/ask

Request:
  { workflow_id, question, user_role, session_id }

Processing Flow:
  1. Validate input
  2. Load workflow context from DB (assemble_context)
  3. Load session history (last 5 Q&A exchanges)
  4. Assemble full prompt: system prompt + context + history + question
  5. Call LLM (Claude Sonnet 4.5)
  6. Parse response for [STEP X, MM:SS] citations
  7. Log interaction to interaction_log
  8. Return structured response

Response:
  {
    answer: "To create a new risk assessment, navigate to...",
    citations: [
      { step: 1, start_time: 0, end_time: 28, title: "Navigate to Module" },
      { step: 2, start_time: 28, end_time: 65, title: "Create Assessment" }
    ],
    suggested_watch: { start_time: 0, end_time: 65 },
    confidence: "answered_from_source" | "not_in_source"
  }
```

**System Prompt — 6 Guardrail Rules:**

| Rule | Description |
|------|-------------|
| 1. Source-Only | Answer ONLY from approved content. No general knowledge. |
| 2. Mandatory Citations | Every claim must include `[STEP X, MM:SS]` reference. |
| 3. Honest Unknowns | If not covered → "This question isn't covered in the approved workflow content..." |
| 4. No Compliance Advice | Explain HOW to use the platform, not WHETHER an approach meets regulations. |
| 5. Role Awareness | If action requires a different role, inform which role is needed. |
| 6. Step-by-Step | Always provide exact navigation path using exact UI element names. |

**Safety Testing Categories:**
- Out-of-scope questions → triggers Rule 3
- Hallucination attempts → only answer if documented
- Citation accuracy → timestamps match video moments
- Role-based responses → informs role requirements
- Conversation continuity → follow-ups work correctly

### 3.4 Frontend (React + Tailwind)

**Purpose:** Split-pane UI with synchronized video playback and AI chat.

```
┌─────────────────────────────────────────────────────┐
│ Header: [Workflow Title]              [User Role]    │
├────────────────────────┬────────────────────────────┤
│ VIDEO PANEL            │ AI CHAT PANEL              │
│                        │                            │
│ ┌────────────────┐     │ AI: Welcome! Ask me about  │
│ │  Video.js      │     │ this workflow.              │
│ │  Player        │     │                            │
│ │  [01:42/05:30] │     │ You: How do I set the risk │
│ └────────────────┘     │ category?                  │
│                        │                            │
│ Progress: ■■■□□ 3/12   │ AI: Click the "Category"   │
│                        │ dropdown...                │
│ ✅ 1. Navigate         │ ▶ Watch [STEP 3, 1:05]     │
│ ✅ 2. Create new       │                            │
│ ▶  3. Fill form        │ [Type your question...]    │
│ ○  4. Attach evidence  │ [Ask] [Suggest ?s]         │
├────────────────────────┴────────────────────────────┤
│ Footer: Progress 25% │ Est. 8 min remaining         │
└─────────────────────────────────────────────────────┘
```

**Synchronization Flows:**

```
Flow 1: Citation click → video seeks
  chat.onCitationClick(step, timestamp) → videoPlayer.seekTo(timestamp)

Flow 2: Step click → video seeks
  stepList.onStepClick(step) → videoPlayer.seekTo(step.start_time)

Flow 3: Video time update → step list updates
  videoPlayer.onTimeUpdate(time) → stepTracker.markWatched(step)

Flow 4: Question asked → AI responds → citations rendered
  chat.onAsk(question) → api.post("/api/ask") → chat.render(response)
```

**Suggested Questions:** Change based on current video position. Pull from workflow_faqs filtered by the step the user is currently watching.

### 3.5 Audit Trail & Completion Tracking

**Interaction Logging** — every Q&A exchange logs:
- User ID, role, timestamp
- Workflow being viewed
- Question asked + AI response
- Cited steps + video position at time of question
- Helpful/not helpful feedback

**Completion Rules (configurable):**
- ≥80% of video duration watched
- All steps viewed (not skipped)
- Optional: ≥1 question asked
- Optional: "I understand" clicked on key steps

**Admin Reporting Dashboard:**
- User × workflow completion matrix
- Average completion time per workflow
- Most frequently asked questions (struggle signals)
- Questions that triggered "not in source" (content gaps)
- Feedback scores (which answers marked not helpful)

---

## 4. Technology Stack

```
INGESTION:
  FFmpeg .................. Frame + audio extraction
  Gemini 1.5 Pro ......... Multimodal video understanding

STORAGE:
  PostgreSQL .............. Knowledge base + interaction logs
  (SQLite for quick MVP)

AI ENGINE:
  Claude Sonnet 4.5 ...... Primary answer LLM
  (GPT-4o as alternative)
  FastAPI ................ API server
  Python 3.11+ ........... Backend

FRONTEND:
  React .................. UI framework
  Tailwind CSS ........... Styling
  Video.js ............... Video player (or HTML5 <video>)

DEPLOYMENT (MVP):
  Railway / Render ....... Backend hosting
  Vercel ................. Frontend hosting
  Neon / Supabase ........ Managed PostgreSQL
```

---

## 5. Scaling Path

```
MVP (1 workflow)          10+ workflows            50+ workflows           Enterprise
─────────────────    ──────────────────────    ─────────────────────    ──────────────
Full context in      Workflow selector UI       Add RAG layer            Role-based
LLM prompt           or auto-routing            Vector DB + embeddings   content access
                     classifier                 Top-K chunk retrieval    (RBAC)
SQLite / Postgres    Still fits in context      >100K tokens of content  Per-role
~4K tokens           ~40K tokens                                        workflow libs

                     Option A: User picks       User Question
                     workflow (safer)              │
                                                   ▼
                     Option B: Classifier        Embedding Model
                     auto-routes (more              │
                     convenient, adds               ▼
                     failure point)              Vector Search
                                                   │
                                                   ▼
                                                Top 5-10 chunks → LLM → Grounded answer
```

**Recommendation:** Start with MVP (1 workflow, full context). Add workflow selector at 10+. Add RAG only when content exceeds context window (~50+ workflows). Add RBAC when multiple user roles need different content libraries.

---

## 6. Data Flow Summary

```
1. Admin uploads MP4 video
2. FFmpeg extracts frames + audio
3. Gemini 1.5 Pro generates rich timestamped transcript
4. SME reviews and approves document
5. Approved content loaded into PostgreSQL
6. User opens learning page for a workflow
7. Video plays in left panel
8. User asks question in right panel
9. FastAPI loads workflow context from DB
10. Context + system prompt + question sent to Claude
11. Claude returns grounded answer with [STEP X, MM:SS] citations
12. Citation parser extracts structured citation objects
13. UI renders answer with clickable timestamp links
14. User clicks citation → video seeks to that moment
15. Interaction logged for audit trail
16. Progress tracked toward completion
```

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| No vector DB at MVP | Full context in prompt | Single workflow is ~4K tokens. Avoids premature complexity. |
| Human approval gate | Mandatory before content enters system | AI never answers from unapproved/draft content. Critical for compliance. |
| Gemini for ingestion, Claude for Q&A | Best tool for each job | Gemini excels at multimodal video understanding. Claude excels at instruction-following and grounded Q&A. |
| Citation format `[STEP X, MM:SS]` | Structured, parseable | Easy to regex-extract and convert to seekable video timestamps. |
| Session memory (last 5 exchanges) | Enables follow-up questions | "What about the next step?" works without re-explaining context. |
| Completion = 80% watched + all steps viewed | Configurable per workflow | Balance between thorough learning and practical completion. |
