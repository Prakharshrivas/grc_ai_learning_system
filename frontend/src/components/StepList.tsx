import type { StepDetail } from '../api/client';

function formatTime(seconds: number | null): string {
  if (seconds == null) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

interface StepListProps {
  steps: StepDetail[];
  currentStep: number | null;
  watchedSteps: Set<number>;
  onStepClick: (step: StepDetail) => void;
}

export default function StepList({
  steps,
  currentStep,
  watchedSteps,
  onStepClick,
}: StepListProps) {
  return (
    <div className="space-y-1">
      {steps.map((step) => {
        const isActive = currentStep === step.step_number;
        const isWatched = watchedSteps.has(step.step_number);

        return (
          <button
            key={step.id}
            onClick={() => onStepClick(step)}
            className={`w-full text-left px-3 py-2 rounded-lg transition-all text-sm flex items-start gap-2 group
              ${isActive ? 'bg-blue-600/20 border border-blue-500/30' : 'hover:bg-slate-700/50 border border-transparent'}
            `}
          >
            <span className="mt-0.5 shrink-0">
              {isWatched ? (
                <svg className="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : isActive ? (
                <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-slate-600 group-hover:border-slate-400" />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <div className={`font-medium truncate ${isActive ? 'text-blue-300' : 'text-slate-300'}`}>
                {step.step_number}. {step.title}
              </div>
              <div className="text-slate-500 text-xs">
                {formatTime(step.start_time)} - {formatTime(step.end_time)}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
