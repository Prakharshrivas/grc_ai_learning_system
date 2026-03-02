import { useCallback, useEffect, useState } from 'react';
import {
  fetchSuggestions,
  fetchWorkflow,
  fetchWorkflows,
  getVideoUrl,
  type WorkflowDetail,
  type WorkflowSummary,
} from '../api/client';
import { useChat } from '../hooks/useChat';
import { useVideoSync } from '../hooks/useVideoSync';
import ChatPanel from './ChatPanel';
import Header from './Header';
import VideoPanel from './VideoPanel';

export default function Layout() {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [selectedRole, setSelectedRole] = useState('User');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorkflows()
      .then((wfs) => {
        setWorkflows(wfs);
        if (wfs.length > 0) {
          setSelectedId(wfs[0].id);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setWorkflow(null);
    fetchWorkflow(selectedId)
      .then((wf) => {
        setWorkflow(wf);
        if (wf.roles.length > 0) setSelectedRole(wf.roles[0]);
      })
      .catch(console.error);
    fetchSuggestions(selectedId).then(setSuggestions).catch(console.error);
  }, [selectedId]);

  const steps = workflow?.steps ?? [];
  const { videoRef, currentTime, currentStep, watchedSteps, completionPct, seekTo } =
    useVideoSync(steps, selectedId);

  const { messages, isLoading: chatLoading, sendMessage, reset } = useChat(selectedId);

  useEffect(() => {
    if (!selectedId || currentStep == null) return;
    fetchSuggestions(selectedId, currentStep).then(setSuggestions).catch(() => {});
  }, [selectedId, currentStep]);

  const handleStepClick = useCallback(
    (step: { start_time: number | null }) => {
      if (step.start_time != null) seekTo(step.start_time);
    },
    [seekTo],
  );

  const handleCitationClick = useCallback(
    (_step: number, startTime: number) => {
      seekTo(startTime);
    },
    [seekTo],
  );

  const handleSend = useCallback(
    (question: string) => {
      sendMessage(question, selectedRole);
    },
    [sendMessage, selectedRole],
  );

  const handleWorkflowChange = useCallback(
    (id: string) => {
      setSelectedId(id);
      reset();
    },
    [reset],
  );

  if (loading) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400 text-sm">Loading workflows...</div>
      </div>
    );
  }

  if (workflows.length === 0) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400 text-sm">No workflows available</p>
          <p className="text-slate-600 text-xs mt-1">
            Seed the database and start the backend
          </p>
        </div>
      </div>
    );
  }

  const videoUrl = workflow?.video_url ? getVideoUrl(workflow.id) : null;
  const roles = workflow?.roles?.length ? workflow.roles : ['User'];

  return (
    <div className="h-screen bg-slate-950 flex flex-col overflow-hidden">
      <Header
        title={workflow?.title ?? 'Loading...'}
        completionPct={completionPct}
        roles={roles}
        selectedRole={selectedRole}
        onRoleChange={setSelectedRole}
      />

      {workflows.length > 1 && (
        <div className="bg-slate-900/50 border-b border-slate-800 px-6 py-2 flex gap-2">
          {workflows.map((wf) => (
            <button
              key={wf.id}
              onClick={() => handleWorkflowChange(wf.id)}
              className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
                wf.id === selectedId
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {wf.title}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 flex min-h-0">
        <div className="w-[55%] border-r border-slate-800 p-4 overflow-y-auto">
          <VideoPanel
            videoRef={videoRef}
            videoUrl={videoUrl}
            steps={steps}
            currentStep={currentStep}
            currentTime={currentTime}
            watchedSteps={watchedSteps}
            completionPct={completionPct}
            onStepClick={handleStepClick}
          />
        </div>

        <div className="w-[45%] flex flex-col bg-slate-900/30">
          <ChatPanel
            messages={messages}
            isLoading={chatLoading}
            suggestions={suggestions}
            onSend={handleSend}
            onCitationClick={handleCitationClick}
            onSuggestionClick={handleSend}
          />
        </div>
      </div>
    </div>
  );
}
