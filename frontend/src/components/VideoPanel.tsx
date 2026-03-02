import type { RefObject } from 'react';
import type { StepDetail } from '../api/client';
import StepList from './StepList';

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

interface VideoPanelProps {
  videoRef: RefObject<HTMLVideoElement | null>;
  videoUrl: string | null;
  steps: StepDetail[];
  currentStep: number | null;
  currentTime: number;
  watchedSteps: Set<number>;
  completionPct: number;
  onStepClick: (step: StepDetail) => void;
}

export default function VideoPanel({
  videoRef,
  videoUrl,
  steps,
  currentStep,
  currentTime,
  watchedSteps,
  completionPct,
  onStepClick,
}: VideoPanelProps) {
  const totalSteps = steps.length;
  const duration = videoRef.current?.duration || 0;

  return (
    <div className="flex flex-col h-full">
      <div className="bg-black rounded-xl overflow-hidden shadow-2xl">
        {videoUrl ? (
          <video
            ref={videoRef}
            src={videoUrl}
            controls
            className="w-full aspect-video"
            preload="metadata"
          />
        ) : (
          <div className="w-full aspect-video bg-slate-800 flex items-center justify-center">
            <p className="text-slate-500 text-sm">No video available</p>
          </div>
        )}
      </div>

      <div className="mt-3 px-1">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
          <span>{formatTime(currentTime)}</span>
          <span>
            Step {currentStep || '-'} / {totalSteps}
          </span>
          <span>{duration ? formatTime(duration) : '--:--'}</span>
        </div>
        <div className="w-full h-1 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all"
            style={{ width: `${completionPct}%` }}
          />
        </div>
      </div>

      <div className="mt-4 flex-1 min-h-0 overflow-y-auto pr-1">
        <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2 px-1">
          Steps
        </h3>
        <StepList
          steps={steps}
          currentStep={currentStep}
          watchedSteps={watchedSteps}
          onStepClick={onStepClick}
        />
      </div>
    </div>
  );
}
