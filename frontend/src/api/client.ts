const BASE = '/api';

export interface WorkflowSummary {
  id: string;
  title: string;
  purpose: string | null;
  video_duration: number | null;
  roles: string[];
  status: string;
  step_count: number;
}

export interface StepDetail {
  id: string;
  step_number: number;
  title: string;
  start_time: number | null;
  end_time: number | null;
  navigation: string | null;
  on_screen: string | null;
  action: string | null;
  narration: string | null;
  important_notes: string | null;
}

export interface FAQDetail {
  id: string;
  question: string;
  answer: string;
  related_step: number | null;
}

export interface WorkflowDetail {
  id: string;
  title: string;
  purpose: string | null;
  video_url: string | null;
  video_duration: number | null;
  roles: string[];
  status: string;
  steps: StepDetail[];
  faqs: FAQDetail[];
}

export interface Citation {
  step: number;
  start_time: number;
  end_time: number;
  title: string;
  display_text: string;
}

export interface AskResponse {
  answer: string;
  citations: Citation[];
  cited_steps: number[];
  suggested_watch: { start_time: number; end_time: number } | null;
  confidence: string;
}

export async function fetchWorkflows(): Promise<WorkflowSummary[]> {
  const res = await fetch(`${BASE}/workflows`);
  if (!res.ok) throw new Error('Failed to fetch workflows');
  return res.json();
}

export async function fetchWorkflow(id: string): Promise<WorkflowDetail> {
  const res = await fetch(`${BASE}/workflows/${id}`);
  if (!res.ok) throw new Error('Failed to fetch workflow');
  return res.json();
}

export async function askQuestion(
  workflowId: string,
  question: string,
  sessionId?: string,
  userRole?: string,
): Promise<AskResponse> {
  const res = await fetch(`${BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workflow_id: workflowId,
      question,
      session_id: sessionId,
      user_role: userRole || 'User',
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || 'Failed to get answer');
  }
  return res.json();
}

export async function fetchSuggestions(
  workflowId: string,
  currentStep?: number,
): Promise<string[]> {
  const params = currentStep != null ? `?current_step=${currentStep}` : '';
  const res = await fetch(`${BASE}/workflows/${workflowId}/suggestions${params}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.suggestions || [];
}

export async function updateProgress(
  userId: string,
  workflowId: string,
  stepWatched?: number,
) {
  await fetch(`${BASE}/progress`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      workflow_id: workflowId,
      step_watched: stepWatched,
    }),
  });
}

export function getVideoUrl(workflowId: string): string {
  return `${BASE}/video/${workflowId}`;
}
