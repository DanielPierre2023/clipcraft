'use client';

import React, { useState } from 'react';
import { 
  SlidersHorizontal, Play, Pause, Maximize2, Layers, Film, 
  Settings2, ChevronDown, Compass, Aperture, Sun, Move, 
  Volume2, FastForward, Rewind, Plus, ShieldCheck, Sparkles
} from 'lucide-react';

const ASSET_GALLERY = [
  {
    id: 1,
    title: 'Neon Horizon — Shot 01',
    duration: '00:06',
    ratio: '16:9',
    img: 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=1200&auto=format&fit=crop',
    tag: 'Drone Motion'
  },
  {
    id: 2,
    title: 'Misty Alpine Ridge',
    duration: '00:04',
    ratio: '21:9',
    img: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=1200&auto=format&fit=crop',
    tag: 'Pan Left'
  },
  {
    id: 3,
    title: 'Cyberpunk Intersection',
    duration: '00:08',
    ratio: '16:9',
    img: 'https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1200&auto=format&fit=crop',
    tag: 'Zoom Push'
  },
  {
    id: 4,
    title: 'Monolith Fluid Sculpture',
    duration: '00:05',
    ratio: '16:9',
    img: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1200&auto=format&fit=crop',
    tag: 'Macro 85mm'
  }
];

export default function StudioCanvas() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeShot, setActiveShot] = useState(ASSET_GALLERY[0]);
  const [selectedLens, setSelectedLens] = useState('35mm Anamorphic');
  const [selectedLighting, setSelectedLighting] = useState('Volumetric Fog & Cyan Glow');
  const [motionIntensity, setMotionIntensity] = useState(65);

  return (
    <div className="flex h-screen w-full bg-[#070709] text-zinc-100 font-sans overflow-hidden antialiased">
      
      {/* LEFT SIDEBAR: Professional Lens & Camera Controls */}
      <aside className="w-80 border-r border-white/5 bg-zinc-950/80 backdrop-blur-2xl flex flex-col justify-between z-20">
        <div className="p-5 space-y-6">
          
          {/* Brand Header */}
          <div className="flex items-center justify-between pb-4 border-b border-white/5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 via-indigo-500 to-fuchsia-500 p-[1px] shadow-lg shadow-violet-500/20">
                <div className="w-full h-full bg-zinc-950 rounded-[7px] flex items-center justify-center">
                  <Film className="w-4 h-4 text-violet-400" />
                </div>
              </div>
              <span className="font-semibold tracking-tight text-sm text-zinc-100">CLIPCRAFT <span className="text-xs text-zinc-500 font-mono">v2.4</span></span>
            </div>
            <span className="px-2 py-0.5 text-[10px] font-mono tracking-wider text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
              4K ENGINE
            </span>
          </div>

          {/* Camera Parameters Block */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-widest text-zinc-500">Camera Rig</span>
              <SlidersHorizontal className="w-3.5 h-3.5 text-zinc-500" />
            </div>

            {/* Lens Selector */}
            <div className="space-y-1.5">
              <label className="text-xs text-zinc-400 flex items-center gap-1.5 font-medium">
                <Aperture className="w-3.5 h-3.5 text-violet-400" /> Focal Optics
              </label>
              <div className="relative">
                <select 
                  value={selectedLens}
                  onChange={(e) => setSelectedLens(e.target.value)}
                  className="w-full bg-zinc-900/90 border border-white/10 rounded-xl px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-violet-500/50 appearance-none cursor-pointer"
                >
                  <option>24mm Ultra-Wide</option>
                  <option>35mm Anamorphic</option>
                  <option>50mm Prime Cinematic</option>
                  <option>85mm Portrait Macro</option>
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-zinc-500 absolute right-3 top-2.5 pointer-events-none" />
              </div>
            </div>

            {/* Lighting Profile */}
            <div className="space-y-1.5">
              <label className="text-xs text-zinc-400 flex items-center gap-1.5 font-medium">
                <Sun className="w-3.5 h-3.5 text-amber-400" /> Atmosphere & Lighting
              </label>
              <div className="relative">
                <select 
                  value={selectedLighting}
                  onChange={(e) => setSelectedLighting(e.target.value)}
                  className="w-full bg-zinc-900/90 border border-white/10 rounded-xl px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-violet-500/50 appearance-none cursor-pointer"
                >
                  <option>Golden Hour Raytracing</option>
                  <option>Volumetric Fog & Cyan Glow</option>
                  <option>Noir High-Contrast Studio</option>
                  <option>Moody Overcast Natural</option>
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-zinc-500 absolute right-3 top-2.5 pointer-events-none" />
              </div>
            </div>

            {/* Motion Dynamics Slider */}
            <div className="space-y-2 pt-2">
              <div className="flex justify-between text-xs">
                <span className="text-zinc-400 flex items-center gap-1.5 font-medium">
                  <Move className="w-3.5 h-3.5 text-indigo-400" /> Camera Velocity
                </span>
                <span className="font-mono text-violet-400 text-[11px]">{motionIntensity}%</span>
              </div>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={motionIntensity}
                onChange={(e) => setMotionIntensity(Number(e.target.value))}
                className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-violet-500"
              />
            </div>
          </div>

          {/* Preset Styles */}
          <div className="space-y-2 pt-2 border-t border-white/5">
            <span className="text-[11px] font-mono uppercase tracking-widest text-zinc-500">Aesthetic Preset</span>
            <div className="grid grid-cols-2 gap-2">
              {['IMAX Film', 'Kodak 35mm', 'Blade Runner', 'Ethereal'].map((style, idx) => (
                <button 
                  key={style}
                  className={`px-3 py-2 rounded-xl text-xs font-medium border text-left transition-all ${
                    idx === 0 
                      ? 'bg-violet-600/15 border-violet-500/40 text-violet-300' 
                      : 'bg-zinc-900/50 border-white/5 text-zinc-400 hover:border-white/10 hover:text-zinc-200'
                  }`}
                >
                  {style}
                </button>
              ))}
            </div>
          </div>

        </div>

        {/* User Account / Credits Pill */}
        <div className="p-4 border-t border-white/5 bg-zinc-950/40 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-zinc-800 border border-white/10 flex items-center justify-center font-mono text-xs text-zinc-300">
              CC
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-zinc-200">Director Tier</span>
              <span className="text-[10px] text-zinc-500 font-mono">1,480 / 2,000 Credits</span>
            </div>
          </div>
          <button className="px-2.5 py-1 bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30 rounded-lg text-xs font-medium transition-all">
            Top Up
          </button>
        </div>
      </aside>

      {/* CENTER: Main Viewport & Timeline */}
      <main className="flex-1 flex flex-col justify-between bg-[#050507] relative overflow-hidden">
        
        {/* Subtle Ambient Backlight Glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-violet-600/10 rounded-full blur-[140px] pointer-events-none" />

        {/* Top Viewport Toolbar */}
        <header className="h-14 border-b border-white/5 px-6 flex items-center justify-between z-10 bg-zinc-950/40 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-zinc-300">{activeShot.title}</span>
            <span className="text-[10px] font-mono px-2 py-0.5 bg-zinc-900 border border-white/10 rounded text-zinc-400">
              {activeShot.ratio}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900 rounded-lg transition-all">
              <Compass className="w-4 h-4" />
            </button>
            <button className="p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900 rounded-lg transition-all">
              <Settings2 className="w-4 h-4" />
            </button>
            <button className="p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900 rounded-lg transition-all">
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Main Cinema Viewport Display */}
        <section className="flex-1 p-6 flex items-center justify-center relative z-10">
          <div className="relative w-full max-w-5xl aspect-video rounded-2xl overflow-hidden border border-white/10 bg-zinc-950 shadow-2xl group">
            
            {/* Display Image with Cinema Look */}
            <img 
              src={activeShot.img} 
              alt="Scene Preview" 
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.01]"
            />

            {/* Vignette Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20 pointer-events-none" />

            {/* On-Canvas Frame Metadata */}
            <div className="absolute top-4 left-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[11px] font-mono text-zinc-300 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-md border border-white/10">
                RAW PREVIEW &middot; 24 FPS
              </span>
            </div>

            {/* Play overlay control */}
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <button 
                onClick={() => setIsPlaying(!isPlaying)}
                className="w-16 h-16 rounded-full bg-zinc-950/80 border border-white/20 text-white flex items-center justify-center backdrop-blur-xl hover:scale-110 hover:border-violet-500/50 transition-all shadow-2xl"
              >
                {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-1" />}
              </button>
            </div>
          </div>
        </section>

        {/* Interactive Scrubbing Timeline Track */}
        <section className="h-44 border-t border-white/5 bg-zinc-950/90 backdrop-blur-2xl p-4 flex flex-col justify-between z-10">
          
          {/* Transport Controls */}
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-4">
              <button className="text-zinc-400 hover:text-zinc-100 transition-all">
                <Rewind className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setIsPlaying(!isPlaying)}
                className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center font-bold hover:bg-zinc-200 transition-all"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
              </button>
              <button className="text-zinc-400 hover:text-zinc-100 transition-all">
                <FastForward className="w-4 h-4" />
              </button>
              <span className="text-xs font-mono text-zinc-400 ml-2">00:02:14 / 00:08:00</span>
            </div>

            <div className="flex items-center gap-3">
              <Volume2 className="w-4 h-4 text-zinc-400" />
              <div className="w-20 h-1 bg-zinc-800 rounded-full overflow-hidden">
                <div className="w-3/4 h-full bg-zinc-400" />
              </div>
            </div>
          </div>

          {/* Timeline Sequence Track */}
          <div className="relative flex-1 mt-3 bg-zinc-900/60 border border-white/5 rounded-xl p-2 flex items-center gap-2 overflow-x-auto">
            {/* Playhead Indicator line */}
            <div className="absolute top-0 bottom-0 left-1/3 w-[2px] bg-violet-500 z-20 shadow-[0_0_10px_rgba(139,92,246,0.8)] pointer-events-none" />

            {ASSET_GALLERY.map((shot) => (
              <div 
                key={shot.id}
                onClick={() => setActiveShot(shot)}
                className={`h-full min-w-[160px] rounded-lg overflow-hidden border relative cursor-pointer group transition-all ${
                  activeShot.id === shot.id 
                    ? 'border-violet-500 ring-2 ring-violet-500/20' 
                    : 'border-white/5 hover:border-white/20 opacity-60 hover:opacity-100'
                }`}
              >
                <img src={shot.img} alt={shot.title} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent p-2 flex flex-col justify-end">
                  <span className="text-[11px] font-medium text-zinc-200 truncate">{shot.title}</span>
                  <span className="text-[9px] font-mono text-zinc-400">{shot.tag} &middot; {shot.duration}</span>
                </div>
              </div>
            ))}

            {/* Add Shot Frame */}
            <button className="h-full min-w-[100px] rounded-lg border border-dashed border-white/10 hover:border-violet-500/40 hover:bg-violet-600/5 flex flex-col items-center justify-center gap-1 text-zinc-500 hover:text-violet-400 transition-all">
              <Plus className="w-5 h-5" />
              <span className="text-[10px] font-medium">Add Shot</span>
            </button>
          </div>
        </section>

      </main>

      {/* RIGHT PANEL: Shot Gallery & Prompt Director */}
      <aside className="w-80 border-l border-white/5 bg-zinc-950/80 backdrop-blur-2xl p-5 flex flex-col justify-between z-20">
        <div className="space-y-5">
          
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <span className="text-xs font-semibold tracking-wider text-zinc-300 uppercase font-mono">Shot Composition</span>
            <Layers className="w-3.5 h-3.5 text-zinc-500" />
          </div>

          {/* Prompt Director Box */}
          <div className="space-y-2">
            <label className="text-xs text-zinc-400 font-medium flex items-center gap-1.5">
              Scene Prompt Direction
            </label>
            <div className="relative">
              <textarea 
                rows={4}
                defaultValue="A ultra-high precision drone sweep across a damp atmospheric mountain peak at twilight, dramatic volumetric lighting, cinematic anamorphic optics, 8K resolution."
                className="w-full bg-zinc-900/80 border border-white/10 rounded-xl p-3 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-violet-500/50 resize-none leading-relaxed"
              />
            </div>
          </div>

          {/* Camera Motion Vector Controls */}
          <div className="space-y-3 pt-2">
            <span className="text-[11px] font-mono uppercase tracking-widest text-zinc-500">Camera Motion Grid</span>
            <div className="grid grid-cols-3 gap-1.5 bg-zinc-900/50 border border-white/5 p-2 rounded-xl">
              {['Pan L', 'Tilt Up', 'Pan R', 'Zoom In', 'Track', 'Zoom Out', 'Roll L', 'Tilt Down', 'Roll R'].map((dir, i) => (
                <button 
                  key={dir}
                  className={`py-2 text-[10px] font-mono rounded-lg border transition-all text-center ${
                    i === 3 
                      ? 'bg-violet-600/20 border-violet-500/40 text-violet-300' 
                      : 'bg-zinc-900 border-white/5 text-zinc-400 hover:border-white/10 hover:text-zinc-200'
                  }`}
                >
                  {dir}
                </button>
              ))}
            </div>
          </div>

        </div>

        {/* Action Render Button */}
        <div className="pt-4 border-t border-white/5">
          <button className="w-full py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-violet-600/25 border border-white/10 transition-all flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4" /> Render Scene Clip
          </button>
        </div>
      </aside>

    </div>
  );
}
