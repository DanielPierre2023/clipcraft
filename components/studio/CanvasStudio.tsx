// frontend/components/studio/CanvasStudio.tsx
'use client';

import React from 'react';
import { useStudioStore } from '@/store/useStudioStore';
import { Play, Sparkles, Video, Sliders, Layers, Zap } from 'lucide-react';

export default function CanvasStudio() {
  const store = useStudioStore();

  return (
    <div className="flex h-screen bg="#09090b" text-slate-100 font-sans overflow-hidden">
      
      {/* LEFT: Controls & Controls Sidebar */}
      <div className="w-[420px] border-r border-zinc-800 p-6 flex flex-col gap-6 bg-zinc-950 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Video className="w-6 h-6 text-purple-500" />
            <h1 className="font-bold text-xl tracking-tight bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
              ClipCraft Studio
            </h1>
          </div>
          <div className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-full text-xs font-semibold text-purple-400">
            <Zap className="w-3.5 h-3.5 fill-purple-400" />
            {store.creditsBalance} Credits
          </div>
        </div>

        {/* Prompt Input & Expander */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Prompt</label>
          <div className="relative">
            <textarea
              value={store.prompt}
              onChange={(e) => store.setPrompt(e.target.value)}
              placeholder="A cinematic drone shot through a neon-lit cyberpunk alley..."
              className="w-full h-32 bg-zinc-900 border border-zinc-800 rounded-xl p-3.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
            />
          </div>
        </div>

        {/* Provider Selector */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">AI Generation Engine</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'runway', name: 'Runway Gen-3' },
              { id: 'replicate_wan', name: 'Wan 2.1 AI' },
              { id: 'kling', name: 'Kling 3.0' },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => store.setProvider(p.id as any)}
                className={`py-2.5 px-3 rounded-lg text-xs font-medium border transition-all ${
                  store.provider === p.id
                    ? 'bg-purple-600/10 border-purple-500 text-purple-300'
                    : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        {/* Camera Vectors Control */}
        <div className="flex flex-col gap-3 bg-zinc-900/50 border border-zinc-800/80 p-4 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-purple-400" /> 3D Camera Motion
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-[11px] text-zinc-400 mb-1">
                <span>Horizontal Pan</span>
                <span>{store.camera.pan}</span>
              </div>
              <input
                type="range" min="-1" max="1" step="0.1"
                value={store.camera.pan}
                onChange={(e) => store.setCameraMotion({ pan: parseFloat(e.target.value) })}
                className="w-full accent-purple-500 bg-zinc-800 h-1 rounded-lg cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-zinc-400 mb-1">
                <span>Vertical Tilt</span>
                <span>{store.camera.tilt}</span>
              </div>
              <input
                type="range" min="-1" max="1" step="0.1"
                value={store.camera.tilt}
                onChange={(e) => store.setCameraMotion({ tilt: parseFloat(e.target.value) })}
                className="w-full accent-purple-500 bg-zinc-800 h-1 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Submit Generation */}
        <button
          onClick={store.startGeneration}
          disabled={store.isGenerating || !store.prompt.trim()}
          className="w-full py-3.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-all shadow-lg shadow-purple-600/20 flex items-center justify-center gap-2"
        >
          {store.isGenerating ? (
            <span className="animate-pulse">Generating Scene...</span>
          ) : (
            <>
              <Sparkles className="w-4 h-4" /> Render Video Scene
            </>
          )}
        </button>
      </div>

      {/* RIGHT: Studio Canvas Display */}
      <div className="flex-1 bg-zinc-950 flex flex-col">
        {/* Main Preview Screen */}
        <div className="flex-1 p-8 flex items-center justify-center relative">
          <div className="w-full max-w-4xl aspect-video bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden relative shadow-2xl flex items-center justify-center">
            {store.videoUrl ? (
              <video
                src={store.videoUrl}
                controls
                autoPlay
                loop
                className="w-full h-full object-contain"
              />
            ) : store.isGenerating ? (
              <div className="flex flex-col items-center gap-4 p-8 text-center max-w-md">
                <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-zinc-200 capitalize">{store.stage.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-zinc-500">{store.progress}% complete</p>
                </div>
                <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden mt-2">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-full transition-all duration-300"
                    style={{ width: `${store.progress}%` }}
                  />
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-zinc-600">
                <Play className="w-12 h-12 stroke-[1.5]" />
                <p className="text-sm font-medium">Ready to render. Enter prompt to start.</p>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Timeline Preview Bar */}
        <div className="h-32 border-t border-zinc-800 bg-zinc-900/40 p-4 flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span className="flex items-center gap-1 font-mono"><Layers className="w-3.5 h-3.5" /> Timeline Track</span>
            <span>00:00:05</span>
          </div>
          <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg p-2 flex items-center gap-2">
            <div className="h-full w-32 bg-purple-900/30 border border-purple-500/30 rounded flex items-center justify-center text-xs text-purple-300 font-medium">
              Scene 1
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
