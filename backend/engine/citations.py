"""Parse and extract [STEP X, MM:SS] citations from LLM responses."""

import re


def parse_citation_timestamp(ts: str) -> int:
    """Convert MM:SS to total seconds."""
    parts = ts.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def extract_citations(llm_response: str, workflow_steps: list[dict]) -> dict:
    """
    Extract [STEP X, MM:SS] citations from LLM response and map them
    to workflow step objects with start/end times.

    Returns dict with:
      - answer: cleaned response text
      - citations: list of citation objects
      - cited_steps: list of step numbers cited
    """
    pattern = r'\[STEP\s+(\d+),?\s*([\d:]+)(?:\s*-\s*([\d:]+))?\]'
    matches = list(re.finditer(pattern, llm_response, re.IGNORECASE))

    steps_by_number = {s["step_number"]: s for s in workflow_steps}

    citations = []
    cited_steps = set()

    for match in matches:
        step_num = int(match.group(1))
        cited_steps.add(step_num)

        step_data = steps_by_number.get(step_num)
        if step_data:
            citation = {
                "step": step_num,
                "start_time": step_data.get("start_time", 0),
                "end_time": step_data.get("end_time", 0),
                "title": step_data.get("title", f"Step {step_num}"),
                "display_text": match.group(0),
            }
        else:
            timestamp_sec = parse_citation_timestamp(match.group(2))
            citation = {
                "step": step_num,
                "start_time": timestamp_sec,
                "end_time": timestamp_sec + 30,
                "title": f"Step {step_num}",
                "display_text": match.group(0),
            }

        citations.append(citation)

    suggested_watch = None
    if citations:
        suggested_watch = {
            "start_time": min(c["start_time"] for c in citations),
            "end_time": max(c["end_time"] for c in citations),
        }

    unique_citations = []
    seen = set()
    for c in citations:
        if c["step"] not in seen:
            seen.add(c["step"])
            unique_citations.append(c)

    return {
        "answer": llm_response,
        "citations": unique_citations,
        "cited_steps": sorted(cited_steps),
        "suggested_watch": suggested_watch,
    }
