"""Load approved workflow JSON documents into the SQLite database."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import APPROVED_WORKFLOWS_DIR, VIDEO_DATA_DIR
from database.db import get_connection, init_db


def parse_timestamp(ts: str) -> int:
    """Convert HH:MM:SS or MM:SS to total seconds."""
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return int(parts[0])


def seed_workflow(json_path: Path, conn) -> str:
    with open(json_path) as f:
        data = json.load(f)

    workflow_id = str(uuid.uuid4())

    video_filename = data.get("source_video", "")
    video_url = ""
    if video_filename:
        video_path = VIDEO_DATA_DIR / video_filename
        if video_path.exists():
            video_url = str(video_path)

    roles_json = json.dumps(data.get("roles", []))

    conn.execute(
        """INSERT INTO workflows (id, title, purpose, video_url, video_duration, roles, status, version, approved_by, approved_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'system', datetime('now'))""",
        (
            workflow_id,
            data["title"],
            data.get("purpose", ""),
            video_url,
            data.get("video_duration", 0),
            roles_json,
            "approved",
        ),
    )

    for step in data.get("steps", []):
        step_id = str(uuid.uuid4())
        start_time = parse_timestamp(step.get("start_time", "0"))
        end_time = parse_timestamp(step.get("end_time", "0"))

        conn.execute(
            """INSERT INTO workflow_steps (id, workflow_id, step_number, title, start_time, end_time, navigation, on_screen, action, narration, important_notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                step_id,
                workflow_id,
                step["step_number"],
                step["title"],
                start_time,
                end_time,
                step.get("navigation", ""),
                step.get("on_screen", ""),
                step.get("action", ""),
                step.get("narration", ""),
                step.get("important_notes", ""),
            ),
        )

    for faq in data.get("faqs", []):
        faq_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO workflow_faqs (id, workflow_id, question, answer, related_step)
               VALUES (?, ?, ?, ?, ?)""",
            (
                faq_id,
                workflow_id,
                faq["question"],
                faq["answer"],
                faq.get("related_step"),
            ),
        )

    return workflow_id


def seed_all():
    init_db()
    conn = get_connection()

    conn.execute("DELETE FROM workflow_faqs")
    conn.execute("DELETE FROM workflow_steps")
    conn.execute("DELETE FROM interaction_log")
    conn.execute("DELETE FROM user_workflow_progress")
    conn.execute("DELETE FROM workflows")
    conn.commit()

    json_files = sorted(APPROVED_WORKFLOWS_DIR.glob("*.json"))
    if not json_files:
        print("No approved workflow JSON files found.")
        return

    for json_path in json_files:
        workflow_id = seed_workflow(json_path, conn)
        conn.commit()
        print(f"Seeded: {json_path.name} -> workflow_id={workflow_id}")

    row = conn.execute("SELECT COUNT(*) as c FROM workflows").fetchone()
    print(f"\nTotal workflows: {row['c']}")
    row = conn.execute("SELECT COUNT(*) as c FROM workflow_steps").fetchone()
    print(f"Total steps: {row['c']}")
    row = conn.execute("SELECT COUNT(*) as c FROM workflow_faqs").fetchone()
    print(f"Total FAQs: {row['c']}")

    conn.close()


if __name__ == "__main__":
    seed_all()
