"""FastAPI route handlers for the GRC AI Learning System."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.schemas import (
    AskRequest,
    AskResponse,
    FAQDetail,
    FeedbackRequest,
    ProgressUpdate,
    StepDetail,
    WorkflowDetail,
    WorkflowSummary,
)
from config import VIDEO_DATA_DIR
from database.db import get_connection
from engine.answer import answer_question

router = APIRouter(prefix="/api")


@router.get("/workflows", response_model=list[WorkflowSummary])
def list_workflows():
    conn = get_connection()
    workflows = conn.execute(
        "SELECT * FROM workflows WHERE status = 'approved' ORDER BY title"
    ).fetchall()

    results = []
    for w in workflows:
        step_count = conn.execute(
            "SELECT COUNT(*) as c FROM workflow_steps WHERE workflow_id = ?",
            (w["id"],),
        ).fetchone()["c"]

        roles = json.loads(w["roles"]) if w["roles"] else []
        results.append(
            WorkflowSummary(
                id=w["id"],
                title=w["title"],
                purpose=w["purpose"],
                video_duration=w["video_duration"],
                roles=roles,
                status=w["status"],
                step_count=step_count,
            )
        )

    conn.close()
    return results


@router.get("/workflows/{workflow_id}", response_model=WorkflowDetail)
def get_workflow(workflow_id: str):
    conn = get_connection()
    w = conn.execute(
        "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
    ).fetchone()

    if not w:
        conn.close()
        raise HTTPException(status_code=404, detail="Workflow not found")

    steps = conn.execute(
        "SELECT * FROM workflow_steps WHERE workflow_id = ? ORDER BY step_number",
        (workflow_id,),
    ).fetchall()

    faqs = conn.execute(
        "SELECT * FROM workflow_faqs WHERE workflow_id = ?",
        (workflow_id,),
    ).fetchall()

    conn.close()

    roles = json.loads(w["roles"]) if w["roles"] else []

    video_url = None
    if w["video_url"]:
        video_path = Path(w["video_url"])
        if video_path.exists():
            video_url = f"/api/video/{workflow_id}"

    return WorkflowDetail(
        id=w["id"],
        title=w["title"],
        purpose=w["purpose"],
        video_url=video_url,
        video_duration=w["video_duration"],
        roles=roles,
        status=w["status"],
        steps=[
            StepDetail(
                id=s["id"],
                step_number=s["step_number"],
                title=s["title"],
                start_time=s["start_time"],
                end_time=s["end_time"],
                navigation=s["navigation"],
                on_screen=s["on_screen"],
                action=s["action"],
                narration=s["narration"],
                important_notes=s["important_notes"],
            )
            for s in steps
        ],
        faqs=[
            FAQDetail(
                id=f["id"],
                question=f["question"],
                answer=f["answer"],
                related_step=f["related_step"],
            )
            for f in faqs
        ],
    )


@router.get("/workflows/{workflow_id}/suggestions")
def get_suggestions(workflow_id: str, current_step: int | None = None):
    conn = get_connection()
    w = conn.execute(
        "SELECT id FROM workflows WHERE id = ?", (workflow_id,)
    ).fetchone()
    if not w:
        conn.close()
        raise HTTPException(status_code=404, detail="Workflow not found")

    if current_step is not None:
        faqs = conn.execute(
            "SELECT question FROM workflow_faqs WHERE workflow_id = ? AND related_step = ?",
            (workflow_id, current_step),
        ).fetchall()
    else:
        faqs = conn.execute(
            "SELECT question FROM workflow_faqs WHERE workflow_id = ? LIMIT 5",
            (workflow_id,),
        ).fetchall()

    conn.close()

    suggestions = [f["question"] for f in faqs]

    generic = [
        "What should I do in this step?",
        "What if I make a mistake here?",
        "What's the next step?",
    ]

    if current_step is not None:
        suggestions = generic[:2] + suggestions
    else:
        suggestions = suggestions + generic[:1]

    return {"suggestions": suggestions[:6]}


@router.post("/ask", response_model=AskResponse)
def ask_question(req: AskRequest):
    conn = get_connection()
    w = conn.execute(
        "SELECT id FROM workflows WHERE id = ? AND status = 'approved'",
        (req.workflow_id,),
    ).fetchone()
    conn.close()

    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found or not approved")

    session_id = req.session_id or str(uuid.uuid4())

    try:
        result = answer_question(
            workflow_id=req.workflow_id,
            question=req.question,
            session_id=session_id,
            user_role=req.user_role,
            user_id=req.user_id,
            video_position=req.video_position,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI engine error: {str(e)}")

    return AskResponse(
        answer=result["answer"],
        citations=result["citations"],
        cited_steps=result["cited_steps"],
        suggested_watch=result["suggested_watch"],
        confidence=result["confidence"],
    )


@router.get("/video/{workflow_id}")
def serve_video(workflow_id: str):
    conn = get_connection()
    w = conn.execute(
        "SELECT video_url FROM workflows WHERE id = ?", (workflow_id,)
    ).fetchone()
    conn.close()

    if not w or not w["video_url"]:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = Path(w["video_url"])
    if not video_path.exists():
        video_path = VIDEO_DATA_DIR / w["video_url"]
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"},
    )


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    if req.feedback not in ("helpful", "not_helpful"):
        raise HTTPException(status_code=400, detail="Feedback must be 'helpful' or 'not_helpful'")

    conn = get_connection()
    conn.execute(
        "UPDATE interaction_log SET feedback = ? WHERE id = ?",
        (req.feedback, req.interaction_id),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.post("/progress")
def update_progress(req: ProgressUpdate):
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM user_workflow_progress WHERE user_id = ? AND workflow_id = ?",
            (req.user_id, req.workflow_id),
        ).fetchone()

        if not existing:
            conn.execute(
                """INSERT OR IGNORE INTO user_workflow_progress (user_id, workflow_id, status)
                   VALUES (?, ?, 'in_progress')""",
                (req.user_id, req.workflow_id),
            )
            conn.commit()
            existing = conn.execute(
                "SELECT * FROM user_workflow_progress WHERE user_id = ? AND workflow_id = ?",
                (req.user_id, req.workflow_id),
            ).fetchone()

        watched = json.loads(existing["steps_watched"] or "[]")
        confirmed = json.loads(existing["steps_confirmed"] or "[]")

        if req.step_watched and req.step_watched not in watched:
            watched.append(req.step_watched)

        if req.step_confirmed and req.step_confirmed not in confirmed:
            confirmed.append(req.step_confirmed)

        total_steps = conn.execute(
            "SELECT COUNT(*) as c FROM workflow_steps WHERE workflow_id = ?",
            (req.workflow_id,),
        ).fetchone()["c"]

        completion = len(set(watched)) / total_steps if total_steps > 0 else 0.0

        status = "completed" if completion >= 0.8 else "in_progress"

        conn.execute(
            """UPDATE user_workflow_progress
               SET steps_watched = ?, steps_confirmed = ?, completion_pct = ?,
                   status = ?, completed_at = CASE WHEN ? = 'completed' THEN datetime('now') ELSE completed_at END
               WHERE user_id = ? AND workflow_id = ?""",
            (
                json.dumps(sorted(set(watched))),
                json.dumps(sorted(set(confirmed))),
                round(completion, 2),
                status,
                status,
                req.user_id,
                req.workflow_id,
            ),
        )
        conn.commit()

        return {
            "steps_watched": sorted(set(watched)),
            "steps_confirmed": sorted(set(confirmed)),
            "completion_pct": round(completion, 2),
            "status": status,
        }
    finally:
        conn.close()


@router.get("/progress/{user_id}/{workflow_id}")
def get_progress(user_id: str, workflow_id: str):
    conn = get_connection()
    progress = conn.execute(
        "SELECT * FROM user_workflow_progress WHERE user_id = ? AND workflow_id = ?",
        (user_id, workflow_id),
    ).fetchone()
    conn.close()

    if not progress:
        return {
            "steps_watched": [],
            "steps_confirmed": [],
            "completion_pct": 0.0,
            "status": "not_started",
            "questions_asked": 0,
        }

    return {
        "steps_watched": json.loads(progress["steps_watched"] or "[]"),
        "steps_confirmed": json.loads(progress["steps_confirmed"] or "[]"),
        "completion_pct": progress["completion_pct"],
        "status": progress["status"],
        "questions_asked": progress["questions_asked"],
    }
