"""Pydantic request/response schemas for the API."""

from pydantic import BaseModel


class AskRequest(BaseModel):
    workflow_id: str
    question: str
    user_role: str = "User"
    session_id: str | None = None
    user_id: str = "anonymous"
    video_position: int | None = None


class Citation(BaseModel):
    step: int
    start_time: int
    end_time: int
    title: str
    display_text: str


class SuggestedWatch(BaseModel):
    start_time: int
    end_time: int


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    cited_steps: list[int]
    suggested_watch: SuggestedWatch | None = None
    confidence: str


class WorkflowSummary(BaseModel):
    id: str
    title: str
    purpose: str | None
    video_duration: int | None
    roles: list[str]
    status: str
    step_count: int


class StepDetail(BaseModel):
    id: str
    step_number: int
    title: str
    start_time: int | None
    end_time: int | None
    navigation: str | None
    on_screen: str | None
    action: str | None
    narration: str | None
    important_notes: str | None


class FAQDetail(BaseModel):
    id: str
    question: str
    answer: str
    related_step: int | None


class WorkflowDetail(BaseModel):
    id: str
    title: str
    purpose: str | None
    video_url: str | None
    video_duration: int | None
    roles: list[str]
    status: str
    steps: list[StepDetail]
    faqs: list[FAQDetail]


class FeedbackRequest(BaseModel):
    interaction_id: str
    feedback: str


class ProgressUpdate(BaseModel):
    user_id: str
    workflow_id: str
    step_watched: int | None = None
    step_confirmed: int | None = None
