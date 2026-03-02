"""AI Answer Engine - handles LLM calls with grounding and session memory."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from config import GEMINI_API_KEY, LLM_MODEL, MAX_SESSION_HISTORY
from database.db import get_connection
from engine.citations import extract_citations
from engine.context import assemble_context, get_workflow_steps
from engine.prompts import SYSTEM_PROMPT

client = genai.Client(api_key=GEMINI_API_KEY)


def get_session_history(session_id: str, limit: int = MAX_SESSION_HISTORY) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT user_question, ai_response FROM interaction_log
           WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?""",
        (session_id, limit),
    ).fetchall()
    conn.close()

    history = []
    for row in reversed(rows):
        history.append({"role": "user", "parts": [{"text": row["user_question"]}]})
        history.append({"role": "model", "parts": [{"text": row["ai_response"]}]})
    return history


def log_interaction(
    workflow_id: str,
    session_id: str,
    user_question: str,
    ai_response: str,
    cited_steps: list[int],
    user_id: str = "anonymous",
    video_position: int | None = None,
):
    conn = get_connection()
    conn.execute(
        """INSERT INTO interaction_log
           (id, user_id, workflow_id, session_id, user_question, ai_response, cited_steps, video_position)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(uuid.uuid4()),
            user_id,
            workflow_id,
            session_id,
            user_question,
            ai_response,
            json.dumps(cited_steps),
            video_position,
        ),
    )
    conn.commit()
    conn.close()


def answer_question(
    workflow_id: str,
    question: str,
    session_id: str | None = None,
    user_role: str = "User",
    user_id: str = "anonymous",
    video_position: int | None = None,
) -> dict:
    context = assemble_context(workflow_id)
    workflow_steps = get_workflow_steps(workflow_id)

    conn = get_connection()
    workflow = conn.execute(
        "SELECT title FROM workflows WHERE id = ?", (workflow_id,)
    ).fetchone()
    conn.close()
    workflow_title = workflow["title"] if workflow else "this workflow"

    system_prompt = SYSTEM_PROMPT.replace("{context}", context).replace(
        "{workflow_title}", workflow_title
    )

    contents = []

    if session_id:
        history = get_session_history(session_id)
        contents.extend(history)

    user_message = question
    if user_role and user_role != "User":
        user_message = f"[My role: {user_role}]\n\n{question}"

    contents.append({"role": "user", "parts": [{"text": user_message}]})

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=contents,
        config={
            "system_instruction": system_prompt,
            "temperature": 0.2,
            "max_output_tokens": 2048,
        },
    )

    ai_text = response.text

    result = extract_citations(ai_text, workflow_steps)

    has_not_covered = "isn't covered in the approved workflow content" in ai_text.lower() or \
                      "not covered in the approved" in ai_text.lower()
    result["confidence"] = "not_in_source" if has_not_covered else "answered_from_source"

    if session_id:
        log_interaction(
            workflow_id=workflow_id,
            session_id=session_id,
            user_question=question,
            ai_response=ai_text,
            cited_steps=result["cited_steps"],
            user_id=user_id,
            video_position=video_position,
        )

    return result
