import { useCallback, useEffect, useRef, useState } from 'react';
import type { StepDetail } from '../api/client';
import { updateProgress } from '../api/client';

export function useVideoSync(steps: StepDetail[], workflowId: string | null) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentStep, setCurrentStep] = useState<number | null>(null);
  const [watchedSteps, setWatchedSteps] = useState<Set<number>>(new Set());
  const [isPlaying, setIsPlaying] = useState(false);

  const seekTo = useCallback((seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play().catch(() => {});
    }
  }, []);

  const onTimeUpdate = useCallback(() => {
    if (!videoRef.current) return;
    const time = videoRef.current.currentTime;
    setCurrentTime(time);

    const active = steps.find(
      (s) =>
        s.start_time != null &&
        s.end_time != null &&
        time >= s.start_time &&
        time <= s.end_time,
    );

    if (active) {
      setCurrentStep(active.step_number);
    }

    const completed = steps.filter(
      (s) => s.end_time != null && time >= s.end_time,
    );
    const newWatched = new Set(completed.map((s) => s.step_number));
    setWatchedSteps((prev) => {
      const merged = new Set([...prev, ...newWatched]);
      if (merged.size !== prev.size && workflowId) {
        const newest = [...newWatched].filter((n) => !prev.has(n));
        newest.forEach((stepNum) => {
          updateProgress('anonymous', workflowId, stepNum).catch(() => {});
        });
      }
      return merged;
    });
  }, [steps, workflowId]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener('timeupdate', onTimeUpdate);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('timeupdate', onTimeUpdate);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, [onTimeUpdate]);

  const totalSteps = steps.length;
  const completionPct = totalSteps > 0 ? (watchedSteps.size / totalSteps) * 100 : 0;

  return {
    videoRef,
    currentTime,
    currentStep,
    watchedSteps,
    isPlaying,
    completionPct,
    seekTo,
  };
}
