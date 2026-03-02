"""Generate rich workflow transcript using Gemini 1.5 Pro multimodal API."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL, APPROVED_WORKFLOWS_DIR

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a GRC compliance documentation specialist. You are watching \
a screen recording of a workflow being performed in a compliance \
software platform.

Your task: Produce a DETAILED, TIMESTAMPED workflow guide from this \
video that captures:

1. EVERY navigation action (what menu was clicked, what page loaded)
2. EVERY form field shown (field name, field type, options available)
3. EVERY button clicked and its result
4. EVERY piece of spoken narration and what it explains
5. EVERY validation message, confirmation dialog, or error shown
6. The SEQUENCE of steps required to complete this workflow

Format your output as VALID JSON with the following structure:

{
  "title": "Name of the workflow",
  "purpose": "One paragraph explaining what this workflow achieves and why it matters for compliance",
  "estimated_time": "How long this workflow takes (e.g. '8-12 minutes')",
  "roles": ["Role1", "Role2"],
  "prerequisites": "What must be done before starting this workflow",
  "steps": [
    {
      "step_number": 1,
      "start_time": "HH:MM:SS",
      "end_time": "HH:MM:SS",
      "title": "Short step title",
      "navigation": "Exact click path: Module > Section > Button",
      "on_screen": "Describe exactly what appears on screen",
      "action": "What the user does in this step",
      "narration": "What the speaker says during this step",
      "important_notes": "Any warnings, tips, or compliance notes for this step"
    }
  ],
  "summary": "A 3-5 sentence summary of the complete workflow",
  "faqs": [
    {
      "question": "Anticipated question",
      "answer": "Answer based on what was shown/said in the video",
      "related_step": 1
    }
  ]
}

Be extremely precise about UI elements. Use exact button names, \
exact field labels, exact menu paths as shown on screen. \
Do not generalize or paraphrase UI elements.

Generate 8-10 FAQ pairs that users would likely ask about this workflow.

IMPORTANT: Return ONLY valid JSON, no markdown code fences or other text."""


def get_video_duration_seconds(video_path: Path) -> int:
    """Get video duration using ffprobe."""
    import subprocess

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return int(float(result.stdout.strip()))


def generate_transcript(video_path: str | Path) -> dict:
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    print(f"Uploading video to Gemini: {video_path.name}")
    video_file = client.files.upload(file=str(video_path))

    print("Waiting for video processing...")
    while video_file.state.name == "PROCESSING":
        time.sleep(5)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        raise RuntimeError(f"Gemini video processing failed: {video_file.state}")

    print(f"Video processed. Generating transcript with {GEMINI_MODEL}...")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[video_file, SYSTEM_PROMPT],
        config={
            "temperature": 0.1,
            "max_output_tokens": 65536,
            "response_mime_type": "application/json",
        },
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].strip()

    transcript = json.loads(raw_text)
    transcript["video_duration"] = get_video_duration_seconds(video_path)
    transcript["source_video"] = video_path.name
    transcript["status"] = "draft"

    print(f"Generated transcript: {transcript['title']}")
    print(f"  Steps: {len(transcript['steps'])}")
    print(f"  FAQs: {len(transcript['faqs'])}")

    return transcript


def save_transcript(transcript: dict, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(transcript, f, indent=2)
    print(f"Transcript saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    from config import VIDEO_DATA_DIR

    videos = {
        "part1_introduction": VIDEO_DATA_DIR / "GRC Practical Approach - Part 1 Introduction - Prabh Nair (720p, h264).mp4",
        "part2_governance": VIDEO_DATA_DIR / "GRC Practical Approach - Part 2 Governance - Prabh Nair (720p, h264).mp4",
    }

    for name, video in videos.items():
        if not video.exists():
            print(f"Skipping {name}: {video.name} not found")
            continue

        transcript = generate_transcript(video)
        output_path = APPROVED_WORKFLOWS_DIR / f"{name}.json"
        save_transcript(transcript, output_path)
