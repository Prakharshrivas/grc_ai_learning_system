"""Pydantic models for database records."""

from pydantic import BaseModel


class Workflow(BaseModel):
    id: str
    title: str
    purpose: str | None = None
    video_url: str | None = None
    video_duration: int | None = None
    roles: list[str] = []
    status: str = "draft"
    version: int = 1
    approved_by: str | None = None
    approved_at: str | None = None
    created_at: str | None = None


class WorkflowStep(BaseModel):
    id: str
    workflow_id: str
    step_number: int
    title: str
    start_time: int | None = None
    end_time: int | None = None
    navigation: str | None = None
    on_screen: str | None = None
    action: str | None = None
    narration: str | None = None
    important_notes: str | None = None


class WorkflowFAQ(BaseModel):
    id: str
    workflow_id: str
    question: str
    answer: str
    related_step: int | None = None


class InteractionLog(BaseModel):
    id: str
    user_id: str = "anonymous"
    workflow_id: str
    session_id: str | None = None
    user_question: str
    ai_response: str
    cited_steps: list[int] = []
    video_position: int | None = None
    timestamp: str | None = None
    feedback: str | None = None


class UserWorkflowProgress(BaseModel):
    user_id: str
    workflow_id: str
    steps_watched: list[int] = []
    steps_confirmed: list[int] = []
    questions_asked: int = 0
    completion_pct: float = 0.0
    started_at: str | None = None
    completed_at: str | None = None
    status: str = "not_started"
