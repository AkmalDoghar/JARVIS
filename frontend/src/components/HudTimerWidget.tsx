"use client";

import React, { useState, useEffect } from "react";
import { 
  Timer, Play, Pause, RotateCcw, Plus, 
  X, Flame,
  Clock, Coffee, Zap, Target
} from "lucide-react";

export interface HudTimerWidgetProps {
  activeTimers: {
    id: string;
    label: string;
    remaining: string;
    duration_seconds?: number;
    fire_at?: number;
  }[];
  currentTimeSec: number;
  formatSecondsToClock: (sec: number) => string;
  handleCancelItem: (type: "timer" | "alarm" | "reminder", id: string) => void;
  handleLaunchPreset: (seconds: number, name: string) => void;
  onOpenFullModal?: () => void;
  className?: string;
}

export function HudTimerWidget({
  activeTimers,
  currentTimeSec,
  formatSecondsToClock,
  handleCancelItem,
  handleLaunchPreset,
  onOpenFullModal,
  className = "",
}: HudTimerWidgetProps) {
  // Local Stopwatch / Quick Timer state
  const [stopwatchRunning, setStopwatchRunning] = useState(false);
  const [stopwatchSeconds, setStopwatchSeconds] = useState(0);
  const [activeTab, setActiveTab] = useState<"presets" | "stopwatch" | "custom">("presets");
  const [customInputMins, setCustomInputMins] = useState("");
  const [customLabel, setCustomLabel] = useState("");
  const [isStarting, setIsStarting] = useState(false);

  // Stopwatch interval
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (stopwatchRunning) {
      interval = setInterval(() => {
        setStopwatchSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [stopwatchRunning]);

  const handleStartCustom = async () => {
    const mins = parseInt(customInputMins, 10);
    if (isNaN(mins) || mins <= 0) return;
    setIsStarting(true);
    try {
      await handleLaunchPreset(mins * 60, customLabel.trim() || `Tactical ${mins}m`);
      setCustomInputMins("");
      setCustomLabel("");
      setActiveTab("presets");
    } finally {
      setIsStarting(false);
    }
  };

  // Format Stopwatch time: HH:MM:SS
  const formatStopwatch = (totalSec: number) => {
    const hrs = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    return `${hrs > 0 ? `${hrs.toString().padStart(2, "0")}:` : ""}${mins
      .toString()
      .padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const presets = [
    { label: "1m Quick", secs: 60, icon: <Zap size={12} className="text-amber-400" /> },
    { label: "5m Rapid", secs: 300, icon: <Coffee size={12} className="text-emerald-400" /> },
    { label: "15m Break", secs: 900, icon: <Clock size={12} className="text-blue-400" /> },
    { label: "25m Focus", secs: 1500, icon: <Target size={12} className="text-cyan-400" /> },
    { label: "45m Deep", secs: 2700, icon: <Flame size={12} className="text-rose-400" /> },
  ];

  return (
    <div
      className={`relative rounded-3xl cyber-glass border border-cyan-500/30 p-3.5 bg-gradient-to-b from-[#08152E]/90 via-[#040A18]/95 to-[#020510]/98 shadow-[0_8px_35px_rgba(0,0,0,0.6)] backdrop-blur-xl flex flex-col gap-3 transition-all duration-300 hover:border-cyan-400/50 ${className}`}
    >
      {/* Holographic Top Horizon Corner Tech Brackets */}
      <div className="absolute top-2 left-2 text-[9px] font-mono text-cyan-400/40 select-none">┌ CHRONO</div>
      <div className="absolute top-2 right-2 text-[9px] font-mono text-cyan-400/40 select-none">HUD_T1 ┐</div>

      {/* Widget Header */}
      <div className="flex items-center justify-between pt-2 px-1">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_12px_rgba(6,182,212,0.3)]">
            <Timer size={14} className="text-cyan-300 animate-pulse" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-hud font-extrabold text-xs tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-200 via-blue-200 to-indigo-200">
                CHRONO MATRIX
              </span>
              <span className="text-[8px] font-mono font-bold px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-400/40">
                LIVE
              </span>
            </div>
            <span className="text-[9px] font-mono text-slate-400">
              Tactical Mission Timers &amp; Precision Stopwatch
            </span>
          </div>
        </div>

        {/* Tab switchers: Presets | Stopwatch | Custom */}
        <div className="flex items-center gap-1 bg-[#061024]/90 p-1 rounded-xl border border-cyan-500/20 text-[10px] font-mono">
          <button
            onClick={() => setActiveTab("presets")}
            className={`px-2 py-0.5 rounded-lg transition-all cursor-pointer ${
              activeTab === "presets"
                ? "bg-cyan-500/25 text-cyan-200 font-bold border border-cyan-400/40 shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Presets
          </button>
          <button
            onClick={() => setActiveTab("stopwatch")}
            className={`px-2 py-0.5 rounded-lg transition-all cursor-pointer ${
              activeTab === "stopwatch"
                ? "bg-cyan-500/25 text-cyan-200 font-bold border border-cyan-400/40 shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Stopwatch
          </button>
          <button
            onClick={() => setActiveTab("custom")}
            className={`px-2 py-0.5 rounded-lg transition-all cursor-pointer ${
              activeTab === "custom"
                ? "bg-cyan-500/25 text-cyan-200 font-bold border border-cyan-400/40 shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Custom
          </button>
        </div>
      </div>

      {/* Main Display Body depending on activeTab */}
      {activeTab === "presets" && (
        <div className="flex flex-col gap-2.5">
          {/* Quick preset pills */}
          <div className="grid grid-cols-5 gap-1.5">
            {presets.map((p) => (
              <button
                key={p.secs}
                onClick={() => handleLaunchPreset(p.secs, p.label)}
                className="py-2 px-1 rounded-xl bg-gradient-to-b from-[#09152B]/90 to-[#050D1C]/90 hover:from-cyan-950/60 hover:to-blue-900/40 border border-cyan-500/25 hover:border-cyan-400/70 text-slate-300 hover:text-white flex flex-col items-center justify-center gap-1 transition-all cursor-pointer group shadow-sm hover:scale-[1.03] active:scale-95"
                title={`Launch ${p.label} timer`}
              >
                <div className="p-1 rounded-lg bg-cyan-950/40 group-hover:bg-cyan-500/20 transition-colors">
                  {p.icon}
                </div>
                <span className="text-[10px] font-mono font-bold">{p.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {activeTab === "stopwatch" && (
        <div className="flex items-center justify-between p-3 rounded-2xl bg-[#061024]/80 border border-cyan-500/25 shadow-inner">
          <div className="flex flex-col">
            <span className="text-[9px] font-mono text-cyan-400/80 uppercase tracking-widest font-bold">
              MISSION ELAPSED TIME
            </span>
            <span className="font-hud text-2xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-100 to-cyan-300 drop-shadow-[0_0_12px_rgba(6,182,212,0.6)]">
              {formatStopwatch(stopwatchSeconds)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setStopwatchRunning(!stopwatchRunning)}
              className={`p-2.5 rounded-xl border font-mono text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shadow-md ${
                stopwatchRunning
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/50 hover:bg-amber-500/30"
                  : "bg-emerald-500/20 text-emerald-300 border-emerald-500/50 hover:bg-emerald-500/30"
              }`}
            >
              {stopwatchRunning ? <Pause size={14} /> : <Play size={14} />}
              <span>{stopwatchRunning ? "PAUSE" : "START"}</span>
            </button>

            <button
              onClick={() => {
                setStopwatchRunning(false);
                setStopwatchSeconds(0);
              }}
              className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all cursor-pointer"
              title="Reset Stopwatch"
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>
      )}

      {activeTab === "custom" && (
        <div className="flex items-center gap-2 p-2 rounded-2xl bg-[#061024]/80 border border-cyan-500/25">
          <input
            type="number"
            min="1"
            max="300"
            placeholder="Mins (e.g. 20)"
            value={customInputMins}
            onChange={(e) => setCustomInputMins(e.target.value)}
            className="w-28 bg-[#09152C] border border-cyan-500/30 rounded-xl px-3 py-1.5 text-xs text-white font-mono placeholder-slate-500 focus:outline-none focus:border-cyan-400"
          />
          <input
            type="text"
            placeholder="Label (optional)"
            value={customLabel}
            onChange={(e) => setCustomLabel(e.target.value)}
            className="flex-1 bg-[#09152C] border border-cyan-500/30 rounded-xl px-3 py-1.5 text-xs text-white font-sans placeholder-slate-500 focus:outline-none focus:border-cyan-400"
          />
          <button
            onClick={handleStartCustom}
            disabled={!customInputMins || isStarting}
            className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-40 text-white font-mono text-xs font-bold transition-all cursor-pointer flex items-center gap-1 shadow-sm"
          >
            <Plus size={13} />
            <span>Set</span>
          </button>
        </div>
      )}

      {/* Active Backend Timers Section (Live Countdown Displays) */}
      <div className="flex flex-col gap-1.5 border-t border-cyan-500/20 pt-2.5">
        <div className="flex items-center justify-between text-[10px] font-mono px-1">
          <div className="flex items-center gap-1.5 text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            <span className="font-semibold uppercase tracking-wider">
              ACTIVE MISSIONS ({activeTimers.length})
            </span>
          </div>

          {onOpenFullModal && (
            <button
              onClick={onOpenFullModal}
              className="text-cyan-400 hover:text-cyan-300 hover:underline cursor-pointer flex items-center gap-1"
            >
              <span>Full Manager</span>
              <span>→</span>
            </button>
          )}
        </div>

        {activeTimers.length === 0 ? (
          <div className="p-2.5 rounded-xl bg-[#061024]/50 border border-cyan-500/10 text-center text-slate-500 text-[11px] font-mono flex items-center justify-center gap-2">
            <Clock size={12} className="text-slate-600" />
            <span>No mission timers running. Select a preset above to arm HUD timer.</span>
          </div>
        ) : (
          <div className="flex flex-col gap-1.5 max-h-36 overflow-y-auto custom-scrollbar pr-0.5">
            {activeTimers.map((timer) => {
              // Calculate remaining seconds if fire_at exists
              let displayRemaining = timer.remaining;
              let percent = 50;

              if (timer.fire_at && timer.duration_seconds && timer.duration_seconds > 0) {
                const diff = Math.max(0, Math.floor(timer.fire_at - currentTimeSec));
                displayRemaining = formatSecondsToClock(diff);
                percent = Math.max(0, Math.min(100, (diff / timer.duration_seconds) * 100));
              }

              return (
                <div
                  key={timer.id}
                  className="flex items-center justify-between p-2 rounded-xl bg-gradient-to-r from-[#09152B] to-[#0D1E3F] border border-cyan-500/30 shadow-sm relative overflow-hidden group"
                >
                  {/* Progress bar background glow */}
                  <div
                    className="absolute inset-y-0 left-0 bg-cyan-500/10 transition-all duration-1000 pointer-events-none"
                    style={{ width: `${percent}%` }}
                  />

                  <div className="flex items-center gap-2.5 min-w-0 z-10">
                    <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shadow-[0_0_8px_#f59e0b] shrink-0" />
                    <div className="flex flex-col min-w-0">
                      <span className="text-white text-xs font-bold truncate">
                        {timer.label || "Tactical Timer"}
                      </span>
                      <span className="text-[9px] font-mono text-cyan-300/80">
                        {timer.duration_seconds ? `${Math.round(timer.duration_seconds / 60)}m Total` : "Running"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 z-10">
                    <span className="font-hud text-sm font-bold text-cyan-200 tracking-wider font-mono">
                      {displayRemaining}
                    </span>
                    <button
                      onClick={() => handleCancelItem("timer", timer.id)}
                      className="p-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/15 transition-all cursor-pointer"
                      title="Abort this timer"
                    >
                      <X size={13} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom Corner Tech Brackets */}
      <div className="absolute bottom-2 left-2 text-[9px] font-mono text-cyan-400/40 select-none">└ SENSORS</div>
      <div className="absolute bottom-2 right-2 text-[9px] font-mono text-cyan-400/40 select-none">00:00:00 ┘</div>
    </div>
  );
}

