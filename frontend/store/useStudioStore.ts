// frontend/store/useStudioStore.ts
import { create } from 'zustand';

export interface CameraMotion {
  pan: number;   // -1.0 to 1.0
  tilt: number;  // -1.0 to 1.0
  zoom: number;  // -1.0 to 1.0
}

interface StudioState {
  prompt: string;
  enhancedPrompt: string;
  provider: 'runway' | 'replicate_wan' | 'kling';
  duration: number;
  resolution: string;
  style: string;
  camera: CameraMotion;
  
  // Generation State
  isGenerating: boolean;
  jobId: string | null;
  progress: number;
  stage: string;
  videoUrl: string | null;
  creditsBalance: number;

  // Actions
  setPrompt: (p: string) => void;
  setProvider: (prov: 'runway' | 'replicate_wan' | 'kling') => void;
  setCameraMotion: (motion: Partial<CameraMotion>) => void;
  startGeneration: () => Promise<void>;
  updateProgress: (pct: number, stage: str, url?: string) => void;
}

export const useStudioStore = create<StudioState>((set, get) => ({
  prompt: '',
  enhancedPrompt: '',
  provider: 'runway',
  duration: 5,
  resolution: '1280x720',
  style: 'cinematic',
  camera: { pan: 0, tilt: 0, zoom: 0 },

  isGenerating: false,
  jobId: null,
  progress: 0,
  stage: 'idle',
  videoUrl: null,
  creditsBalance: 450,

  setPrompt: (prompt) => set({ prompt }),
  setProvider: (provider) => set({ provider }),
  setCameraMotion: (motion) =>
    set((state) => ({ camera: { ...state.camera, ...motion } })),

  startGeneration: async () => {
    const { prompt, provider, duration, resolution, style, camera } = get();
    if (!prompt.trim()) return;

    set({ isGenerating: true, progress: 0, stage: 'queuing', videoUrl: null });

    try {
      const res = await fetch('/api/v1/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          provider,
          duration,
          resolution,
          style,
          camera_pan: camera.pan,
          camera_tilt: camera.tilt,
          camera_zoom: camera.zoom,
        }),
      });

      const data = await res.json();
      set({ jobId: data.job_id });

      // Subscribe to Server-Sent Events
      const eventSource = new EventSource(`/api/v1/jobs/${data.job_id}/stream`);
      
      eventSource.addEventListener('update', (e: MessageEvent) => {
        const payload = JSON.parse(e.data);
        get().updateProgress(payload.progress, payload.stage, payload.result_url);

        if (payload.progress === 100 || payload.stage === 'failed') {
          eventSource.close();
        }
      });

    } catch (err) {
      set({ isGenerating: false, stage: 'failed' });
    }
  },

  updateProgress: (progress, stage, videoUrl) => {
    set((state) => ({
      progress,
      stage,
      videoUrl: videoUrl || state.videoUrl,
      isGenerating: progress < 100 && stage !== 'failed',
    }));
  },
}));
