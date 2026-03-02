"""Assemble workflow context for LLM prompt injection."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.db import get_connection


def format_time(seconds: int) -> str:
    """Convert seconds to MM:SS format."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def assemble_context(workflow_id: str) -> str:
    conn = get_connection()

    workflow = conn.execute(
        "SELECT * FROM workflows WHERE id = ? AND status = 'approved'",
        (workflow_id,),
    ).fetchone()

    if not workflow:
        conn.close()
        raise ValueError(f"No approved workflow found with id: {workflow_id}")

    steps = conn.execute(
        "SELECT * FROM workflow_steps WHERE workflow_id = ? ORDER BY step_number",
        (workflow_id,),
    ).fetchall()

    faqs = conn.execute(
        "SELECT * FROM workflow_faqs WHERE workflow_id = ?",
        (workflow_id,),
    ).fetchall()

    conn.close()

    roles = json.loads(workflow["roles"]) if workflow["roles"] else []
    roles_str = ", ".join(roles) if roles else "All users"

    lines = [
        "=== APPROVED WORKFLOW KNOWLEDGE BASE ===",
        "",
        f"WORKFLOW: {workflow['title']}",
        f"PURPOSE: {workflow['purpose']}",
        f"ROLES: {roles_str}",
        f"VIDEO DURATION: {workflow['video_duration']} seconds ({format_time(workflow['video_duration'])})",
        "",
        "STEP-BY-STEP GUIDE:",
        "",
    ]

    for step in steps:
        start = format_time(step["start_time"]) if step["start_time"] else "00:00"
        end = format_time(step["end_time"]) if step["end_time"] else "00:00"

        lines.extend([
            f"[STEP {step['step_number']}] [{start} - {end}]",
            f"TITLE: {step['title']}",
        ])
        if step["navigation"]:
            lines.append(f"NAVIGATION: {step['navigation']}")
        if step["on_screen"]:
            lines.append(f"ON SCREEN: {step['on_screen']}")
        if step["action"]:
            lines.append(f"ACTION: {step['action']}")
        if step["narration"]:
            lines.append(f"NARRATION: {step['narration']}")
        if step["important_notes"]:
            lines.append(f"IMPORTANT: {step['important_notes']}")
        lines.append("")

    lines.extend([
        "FREQUENTLY ASKED QUESTIONS:",
        "",
    ])

    for i, faq in enumerate(faqs, 1):
        lines.extend([
            f"Q{i}: {faq['question']}",
            f"A{i}: {faq['answer']}",
            "",
        ])

    lines.append("=== END OF APPROVED CONTENT ===")

    return "\n".join(lines)


def get_workflow_steps(workflow_id: str) -> list[dict]:
    conn = get_connection()
    steps = conn.execute(
        "SELECT * FROM workflow_steps WHERE workflow_id = ? ORDER BY step_number",
        (workflow_id,),
    ).fetchall()
    conn.close()
    return [dict(s) for s in steps]
