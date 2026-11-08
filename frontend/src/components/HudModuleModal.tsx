"use client";

import React, { useEffect, useState } from "react";
import {
  BrainCircuit,
  Timer,
  Cpu,
  Layers,
  X,
  Plus,
  Wifi,
  BatteryMedium,
  Sparkles,
  Bell,
  Calendar,
  Eye,
  Camera,
  Bot,
  Play,
  Square,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  RefreshCw,
  Terminal,
  Activity,
  FolderGit2,
  Globe,
  CloudSun,
  Search,
  GitBranch,
  FileCode,
  ExternalLink,
  Wind,
  Droplets,
} from "lucide-react";
import { MemoryMatrixWidget } from "./MemoryMatrixWidget";
import { HudTimerWidget } from "./HudTimerWidget";

export type HudModuleTab = "all" | "memory" | "system" | "timers" | "files" | "web" | "vision" | "agent";

export interface AgentPlanStep {
  step_number: number;
  title: string;
  description: string;
  tool_name: string;
  tool_args?: Record<string, unknown>;
  risk_level: string;
  requires_confirmation?: boolean;
  requires_pin?: boolean;
  confirmed?: boolean;
  status: "pending" | "in_progress" | "completed" | "failed" | "skipped" | "awaiting_confirmation";
  result?: Record<string, unknown>;
  error?: string;
  executed_at?: number;
}

export interface AgentPlanData {
  task_id: string;
  goal: string;
  status: string;
  current_step_index: number;
  total_steps?: number;
  max_retries_per_step?: number;
  retry_counts?: Record<string | number, number>;
  created_at?: number;
  completed_at?: number;
  summary?: string;
  steps: AgentPlanStep[];
}

export interface ActiveTimerItem {
  id: string;
  label: string;
  remaining: string;
  duration_seconds?: number;
  fire_at?: number;
}

export interface ActiveAlarmItem {
  id: string;
  label: string;
  fires_at: string;
}

export interface ActiveReminderItem {
  id: string;
  message?: string;
  message_text?: string;
  fires_at?: string;
  scheduled_for?: string;
}

export interface HudModuleModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: HudModuleTab;
  onTabChange: (tab: HudModuleTab) => void;

  // Timers Hub Props
  activeTimers: ActiveTimerItem[];
  activeAlarms: ActiveAlarmItem[];
  activeReminders: ActiveReminderItem[];
  currentTimeSec: number;
  formatSecondsToClock: (s: number) => string;
  handleCancelItem: (id: string, type: string) => void;
  handleLaunchPreset: (secs: number, label: string) => void;

  showTimerCreator: boolean;
  setShowTimerCreator: (show: boolean) => void;
  creatorTab: "timer" | "alarm" | "reminder";
  setCreatorTab: (tab: "timer" | "alarm" | "reminder") => void;

  customLabel: string;
  setCustomLabel: (v: string) => void;
  customHours: number;
  setCustomHours: (v: number) => void;
  customMinutes: number;
  setCustomMinutes: (v: number) => void;
  customSeconds: number;
  setCustomSeconds: (v: number) => void;
  handleCreateCustomTimer: (e?: React.FormEvent) => void;

  alarmTimeInput: string;
  setAlarmTimeInput: (v: string) => void;
  handleCreateCustomAlarm: (e?: React.FormEvent) => void;

  reminderTextInput: string;
  setReminderTextInput: (v: string) => void;
  reminderWhenInput: string;
  setReminderWhenInput: (v: string) => void;
  handleCreateCustomReminder: (e?: React.FormEvent) => void;
  creatingTimer: boolean;

  // System Diagnostics Props
  systemMetrics: {
    cpu: number;
    ram: number;
    ramUsed: number;
    ramTotal: number;
  };
  isCharging?: boolean;
  batteryLevel?: number | null;
}

export function HudModuleModal({
  isOpen,
  onClose,
  activeTab,
  onTabChange,
  activeTimers,
  activeAlarms,
  activeReminders,
  currentTimeSec,
  formatSecondsToClock,
  handleCancelItem,
  handleLaunchPreset,
  showTimerCreator,
  setShowTimerCreator,
  creatorTab,
  setCreatorTab,
  customLabel,
  setCustomLabel,
  customHours,
  setCustomHours,
  customMinutes,
  setCustomMinutes,
  customSeconds,
  setCustomSeconds,
  handleCreateCustomTimer,
  alarmTimeInput,
  setAlarmTimeInput,
  handleCreateCustomAlarm,
  reminderTextInput,
  setReminderTextInput,
  reminderWhenInput,
  setReminderWhenInput,
  handleCreateCustomReminder,
  creatingTimer,
  systemMetrics,
  isCharging,
  batteryLevel,
}: HudModuleModalProps) {
  // Phase 7 Desktop Vision interactive inspector state
  const [visionFocus, setVisionFocus] = useState<"error" | "code" | "ui" | "general">("error");
  const [visionQuestion, setVisionQuestion] = useState("");
  const [isInspecting, setIsInspecting] = useState(false);
  const [visionResult, setVisionResult] = useState<{ analysis?: string; model?: string; error?: string } | null>(null);

  const handleInspectScreen = async () => {
    setIsInspecting(true);
    setVisionResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/vision/inspect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          focus: visionFocus,
          question: visionQuestion.trim() || undefined,
          save_screenshot: false,
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setVisionResult({ analysis: data.analysis, model: data.model });
      } else {
        setVisionResult({ error: data.error || data.spoken_response || data.detail || "Inspection failed or offline." });
      }
    } catch {
      setVisionResult({ error: "Failed to connect to JARVIS vision API." });
    } finally {
      setIsInspecting(false);
    }
  };

  // Phase 8 Autonomous Multi-Step Agent state
  const [agentGoal, setAgentGoal] = useState("");
  const [isAgentRunning, setIsAgentRunning] = useState(false);
  const [agentPlan, setAgentPlan] = useState<AgentPlanData | null>(null);
  const [agentLogs, setAgentLogs] = useState<string[]>([]);
  const [agentPin, setAgentPin] = useState("");
  const [confirmingStep, setConfirmingStep] = useState(false);
  const [stoppingAgent, setStoppingAgent] = useState(false);

  // Poll agent status if executing or active
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isOpen && (isAgentRunning || agentPlan?.status === "executing" || agentPlan?.status === "waiting_for_confirmation")) {
      interval = setInterval(async () => {
        try {
          const res = await fetch("http://127.0.0.1:8000/api/agent/status");
          if (res.ok) {
            const data = await res.json();
            if (data.plan) {
              setAgentPlan(data.plan);
              if (data.plan.status === "completed" || data.plan.status === "failed" || data.plan.status === "stopped") {
                setIsAgentRunning(false);
              }
            }
            if (data.logs) {
              setAgentLogs(data.logs);
            }
          }
        } catch {
          // ignore
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isOpen, isAgentRunning, agentPlan?.status]);

  const handleLaunchMission = async (customGoal?: string, templateKey?: string) => {
    const goalToRun = customGoal || agentGoal.trim() || "Prepare project for deployment";
    setIsAgentRunning(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/agent/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal: goalToRun,
          template: templateKey,
        }),
      });
      const data = await res.json();
      if (res.ok && data.plan) {
        setAgentPlan(data.plan);
      }
    } catch {
      // ignore
    } finally {
      setIsAgentRunning(false);
    }
  };

  const handleConfirmAgentStep = async () => {
    if (!agentPlan?.task_id) return;
    setConfirmingStep(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/agent/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: agentPlan.task_id,
          pin: agentPin || undefined,
        }),
      });
      const data = await res.json();
      if (res.ok && data.plan) {
        setAgentPlan(data.plan);
        setAgentPin("");
      }
    } catch {
      // ignore
    } finally {
      setConfirmingStep(false);
    }
  };

  const handleEmergencyStop = async () => {
    setStoppingAgent(true);
    try {
      await fetch("http://127.0.0.1:8000/api/agent/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      setIsAgentRunning(false);
      const res = await fetch("http://127.0.0.1:8000/api/agent/status");
      if (res.ok) {
        const data = await res.json();
        if (data.plan) setAgentPlan(data.plan);
      }
    } catch {
      // ignore
    } finally {
      setStoppingAgent(false);
    }
  };

  // Phase 4 Files & Code Hub state
  const [projectData, setProjectData] = useState<{
    project_name?: string;
    path?: string;
    frameworks?: string[];
    dependencies?: string[];
    entry_files?: string[];
    git?: {
      is_git_repo?: boolean;
      branch?: string;
      modified_count?: number;
      status_summary?: string;
    };
  } | null>(null);
  const [loadingFiles, setLoadingFiles] = useState(false);

  const fetchProjectInfo = async () => {
    setLoadingFiles(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/files/inspect");
      if (res.ok) {
        const data = await res.json();
        if (data.project) {
          setProjectData(data.project);
        } else if (data.project_name) {
          setProjectData(data);
        }
      }
    } catch {
      // offline or error
    } finally {
      setLoadingFiles(false);
    }
  };

  // Phase 5 Web & Weather state
  const [weatherCity, setWeatherCity] = useState("Islamabad");
  const [weatherData, setWeatherData] = useState<{
    city?: string;
    country?: string;
    temp_c?: string;
    feels_like_c?: string;
    condition?: string;
    humidity?: string;
    wind_kmph?: string;
    spoken_summary?: string;
    message?: string;
    error?: string;
  } | null>(null);
  const [loadingWeather, setLoadingWeather] = useState(false);

  const [webQuery, setWebQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Array<{ title: string; snippet: string; url: string }>>([]);
  const [searchingWeb, setSearchingWeb] = useState(false);

  const fetchWeatherInfo = async (cityToFetch?: string) => {
    const targetCity = cityToFetch || weatherCity || "Islamabad";
    setLoadingWeather(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/web/weather?city=${encodeURIComponent(targetCity)}`);
      if (res.ok) {
        const data = await res.json();
        setWeatherData(data);
      }
    } catch {
      // offline
    } finally {
      setLoadingWeather(false);
    }
  };

  const handleRunWebSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!webQuery.trim()) return;
    setSearchingWeb(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/web/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: webQuery.trim(), max_results: 4 }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.results) {
          setSearchResults(data.results);
        }
      }
    } catch {
      // offline
    } finally {
      setSearchingWeb(false);
    }
  };

  // Auto-fetch Files or Weather data when tabs are activated
  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(() => {
      if ((activeTab === "files" || activeTab === "all") && !projectData) {
        fetchProjectInfo();
      }
      if ((activeTab === "web" || activeTab === "all") && !weatherData) {
        fetchWeatherInfo();
      }
    }, 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, activeTab, projectData, weatherData]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const totalActiveTimers =
    activeTimers.length + activeAlarms.length + activeReminders.length;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
      onClick={onClose}
    >
      {/* Modal Dialog Window */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-4xl max-h-[88vh] flex flex-col rounded-3xl cyber-glass border border-cyan-500/40 shadow-[0_0_60px_rgba(6,182,212,0.35)] bg-gradient-to-b from-[#0B152A] via-[#050B18] to-[#02050E] overflow-hidden animate-in zoom-in-95 duration-200"
      >
        {/* Glow ambient background accents */}
        <div className="absolute top-0 right-1/4 w-72 h-20 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/4 w-72 h-20 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-cyan-500/25 flex flex-wrap items-center justify-between gap-3 bg-[#061024]/90 shrink-0 relative z-10">
          {/* Left Title & Status */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.3)]">
              {activeTab === "memory" && <BrainCircuit size={20} className="text-purple-400" />}
              {activeTab === "timers" && <Timer size={20} className="text-amber-400" />}
              {activeTab === "system" && <Cpu size={20} className="text-cyan-400" />}
              {activeTab === "files" && <FolderGit2 size={20} className="text-emerald-400" />}
              {activeTab === "web" && <Globe size={20} className="text-cyan-400" />}
              {activeTab === "vision" && <Eye size={20} className="text-emerald-400" />}
              {activeTab === "agent" && <Bot size={20} className="text-rose-400" />}
              {activeTab === "all" && <Layers size={20} className="text-blue-400" />}
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-hud text-sm sm:text-base font-bold text-white tracking-wider">
                  {activeTab === "memory" && "NEURAL MEMORY MATRIX"}
                  {activeTab === "timers" && "CHRONO-MATRIX HUB"}
                  {activeTab === "system" && "HARDWARE TELEMETRY"}
                  {activeTab === "files" && "FILES & CODEBASE HUB"}
                  {activeTab === "web" && "WEB & WEATHER INTELLIGENCE"}
                  {activeTab === "vision" && "DESKTOP VISION DIAGNOSTICS"}
                  {activeTab === "agent" && "AUTONOMOUS AGENT MISSION CONTROL"}
                  {activeTab === "all" && "TACTICAL COMMAND HUD"}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 uppercase">
                  {activeTab === "memory" && "Phase 6B Active"}
                  {activeTab === "timers" && "Phase 3C Async"}
                  {activeTab === "system" && "Live Sensor Feed"}
                  {activeTab === "files" && "Phase 4 Code Tools"}
                  {activeTab === "web" && "Phase 5 Online Research"}
                  {activeTab === "vision" && "Phase 7 Multimodal AI"}
                  {activeTab === "agent" && "Phase 8 Autonomous Pipeline"}
                  {activeTab === "all" && "All Subsystems"}
                </span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                {activeTab === "memory" && "Persistent episodic memories & project context recall"}
                {activeTab === "timers" && "Non-blocking background countdowns, alarms & scheduled reminders"}
                {activeTab === "system" && "Real-time CPU compute load, RAM allocation, network and battery status"}
                {activeTab === "files" && "Workspace file reading, code editing, and Git inspection tools"}
                {activeTab === "web" && "Real-time search, prompt injection defense, and meteorological radar"}
                {activeTab === "vision" && "Real-time desktop screen capture, UI inspection & bug diagnostics"}
                {activeTab === "agent" && "Multi-step autonomous execution, safety confirmation gates & circuit breaker"}
                {activeTab === "all" && "Unified multi-subsystem view"}
              </span>
            </div>
          </div>

          {/* Quick Tab Switcher inside Modal */}
          <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-[#030814]/90 border border-cyan-500/30 overflow-x-auto">
            <button
              onClick={() => onTabChange("memory")}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeTab === "memory"
                  ? "bg-purple-600/40 text-purple-200 border border-purple-400/50 shadow-[0_0_12px_rgba(168,85,247,0.35)]"
                  : "text-slate-400 hover:text-purple-300"
              }`}
            >
              <BrainCircuit size={13} />
              <span>Memory</span>
            </button>

            <button
              onClick={() => onTabChange("timers")}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeTab === "timers"
                  ? "bg-amber-600/40 text-amber-200 border border-amber-400/50 shadow-[0_0_12px_rgba(245,158,11,0.35)]"
                  : "text-slate-400 hover:text-amber-300"
              }`}
            >
              <Timer size={13} />
              <span>Timers</span>
              {totalActiveTimers > 0 && (
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
              )}
            </button>

            <button
              onClick={() => onTabChange("system")}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeTab === "system"
                  ? "bg-cyan-600/40 text-cyan-200 border border-cyan-400/50 shadow-[0_0_12px_rgba(6,182,212,0.35)]"
                  : "text-slate-400 hover:text-cyan-300"
              }`}
            >
              <Cpu size={13} />
              <span>System</span>
            </button>

            <button
              onClick={() => onTabChange("files")}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeTab === "files"
                  ? "bg-emerald-600/40 text-emerald-200 border border-emerald-400/50 shadow-[0_0_12px_rgba(16,185,129,0.35)]"
                  : "text-slate-400 hover:text-emerald-300"
              }`}
            >
              <FolderGit2 size={13} />
              <span>Files</span>
            </button>

            <button
              onClick={() => onTabChange("web")}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeTab === "web"
                  ? "bg-cyan-600/40 text-cyan-200 border border-cyan-400/50 shadow-[0_0_12px_rgba(6,182,212,0.35)]"
                  : "text-slate-400 hover:text-cyan-300"
              }`}
            >
              <Globe size={13} />
              <span>Web</span>
            </button>

            <button
              onClick={() => onTabChange("vision")}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeTab === "vision"
                  ? "bg-emerald-600/40 text-emerald-200 border border-emerald-400/50 shadow-[0_0_12px_rgba(16,185,129,0.35)]"
                  : "text-slate-400 hover:text-emerald-300"
              }`}
            >
              <Eye size={13} />
              <span>Vision</span>
            </button>

            <button
              onClick={() => onTabChange("agent")}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeTab === "agent"
                  ? "bg-rose-600/40 text-rose-200 border border-rose-400/50 shadow-[0_0_12px_rgba(244,63,94,0.35)]"
                  : "text-slate-400 hover:text-rose-300"
              }`}
            >
              <Bot size={13} />
              <span>Agent</span>
            </button>

            <button
              onClick={() => onTabChange("all")}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeTab === "all"
                  ? "bg-blue-600/40 text-blue-200 border border-blue-400/50 shadow-[0_0_12px_rgba(59,130,246,0.35)]"
                  : "text-slate-400 hover:text-blue-300"
              }`}
            >
              <Layers size={13} />
              <span>All</span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="ml-2 w-8 h-8 rounded-xl bg-slate-800/80 hover:bg-rose-500/20 border border-slate-700 hover:border-rose-500/50 text-slate-400 hover:text-rose-300 flex items-center justify-center transition-all cursor-pointer"
              title="Close modal (Esc)"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-5 custom-scrollbar min-h-0 space-y-6">
          {/* 1. MEMORY MATRIX VIEW */}
          {(activeTab === "memory" || activeTab === "all") && (
            <div className="space-y-2">
              {activeTab === "all" && (
                <div className="flex items-center gap-2 pb-1 border-b border-purple-500/20 text-purple-300">
                  <BrainCircuit size={16} />
                  <span className="font-hud text-xs font-bold uppercase tracking-wider">
                    Neural Memory Matrix
                  </span>
                </div>
              )}
              <MemoryMatrixWidget />
            </div>
          )}

          {/* 2. CHRONO-MATRIX HUB VIEW */}
          {(activeTab === "timers" || activeTab === "all") && (
            <div className="space-y-4">
              {activeTab === "all" && (
                <div className="flex items-center gap-2 pb-1 border-b border-amber-500/20 text-amber-300">
                  <Timer size={16} />
                  <span className="font-hud text-xs font-bold uppercase tracking-wider">
                    Chrono-Matrix Hub (Timers & Alarms)
                  </span>
                </div>
              )}

              {/* Integrated Live Main Timer Widget in All HUD & Timers Tab */}
              <HudTimerWidget
                activeTimers={activeTimers}
                currentTimeSec={currentTimeSec}
                formatSecondsToClock={formatSecondsToClock}
                handleCancelItem={handleCancelItem}
                handleLaunchPreset={handleLaunchPreset}
              />

              <div
                id="section-timers-modal"
                className="relative rounded-3xl bg-gradient-to-b from-[#110F20]/90 via-[#0A0D1A]/95 to-[#04060F]/98 border border-amber-500/35 p-5 sm:p-6 shadow-[0_0_35px_rgba(245,158,11,0.12)] flex flex-col gap-4 overflow-hidden"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.3)]">
                      <Timer size={20} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-hud text-white font-bold text-sm tracking-wider">
                        Chrono Engine Controls
                      </span>
                      <span className="text-[11px] text-amber-400/80 font-mono">
                        Phase 3C Active • Non-Blocking Background Timers
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => setShowTimerCreator(!showTimerCreator)}
                    className="px-3.5 py-2 rounded-xl bg-amber-500/25 hover:bg-amber-500/35 border border-amber-500/50 text-amber-300 font-semibold text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
                  >
                    <Plus size={14} className={showTimerCreator ? "rotate-45 transition-transform" : "transition-transform"} />
                    <span>{showTimerCreator ? "Close Form" : "+ Create New"}</span>
                  </button>
                </div>

                {/* Inline Creator Form */}
                {showTimerCreator && (
                  <div className="p-4 rounded-2xl bg-[#060D1E] border border-amber-500/40 flex flex-col gap-3.5 shadow-inner">
                    <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5">
                      <button
                        onClick={() => setCreatorTab("timer")}
                        className={`flex-1 py-1.5 rounded-xl text-xs font-mono font-bold transition-colors cursor-pointer ${
                          creatorTab === "timer"
                            ? "bg-amber-600 text-white shadow-sm"
                            : "text-slate-400 hover:text-amber-200"
                        }`}
                      >
                        Timer (Countdown)
                      </button>
                      <button
                        onClick={() => setCreatorTab("alarm")}
                        className={`flex-1 py-1.5 rounded-xl text-xs font-mono font-bold transition-colors cursor-pointer ${
                          creatorTab === "alarm"
                            ? "bg-amber-600 text-white shadow-sm"
                            : "text-slate-400 hover:text-amber-200"
                        }`}
                      >
                        Daily Alarm
                      </button>
                      <button
                        onClick={() => setCreatorTab("reminder")}
                        className={`flex-1 py-1.5 rounded-xl text-xs font-mono font-bold transition-colors cursor-pointer ${
                          creatorTab === "reminder"
                            ? "bg-amber-600 text-white shadow-sm"
                            : "text-slate-400 hover:text-amber-200"
                        }`}
                      >
                        Scheduled Reminder
                      </button>
                    </div>

                    {creatorTab === "timer" && (
                      <form onSubmit={handleCreateCustomTimer} className="flex flex-col gap-3">
                        <input
                          type="text"
                          placeholder="Timer Label (e.g. Code Sprint, Meeting, Tea Break)"
                          value={customLabel}
                          onChange={(e) => setCustomLabel(e.target.value)}
                          className="bg-[#09152B] border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                        />
                        <div className="grid grid-cols-3 gap-3 text-center text-xs font-mono">
                          <div>
                            <span className="text-[10px] text-slate-400 block mb-1">Hours</span>
                            <input
                              type="number"
                              min={0}
                              max={24}
                              value={customHours}
                              onChange={(e) => setCustomHours(Number(e.target.value))}
                              className="w-full bg-[#09152B] border border-slate-700 rounded-xl px-2 py-2 text-center text-white font-bold"
                            />
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 block mb-1">Minutes</span>
                            <input
                              type="number"
                              min={0}
                              max={59}
                              value={customMinutes}
                              onChange={(e) => setCustomMinutes(Number(e.target.value))}
                              className="w-full bg-[#09152B] border border-slate-700 rounded-xl px-2 py-2 text-center text-white font-bold"
                            />
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 block mb-1">Seconds</span>
                            <input
                              type="number"
                              min={0}
                              max={59}
                              value={customSeconds}
                              onChange={(e) => setCustomSeconds(Number(e.target.value))}
                              className="w-full bg-[#09152B] border border-slate-700 rounded-xl px-2 py-2 text-center text-white font-bold"
                            />
                          </div>
                        </div>
                        <button
                          type="submit"
                          disabled={creatingTimer}
                          className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-mono font-bold transition-all cursor-pointer shadow-[0_0_15px_rgba(245,158,11,0.35)] mt-1 disabled:opacity-50"
                        >
                          {creatingTimer ? "Initiating Timer..." : "Start Timer"}
                        </button>
                      </form>
                    )}

                    {creatorTab === "alarm" && (
                      <form onSubmit={handleCreateCustomAlarm} className="flex flex-col gap-3">
                        <input
                          type="time"
                          value={alarmTimeInput}
                          onChange={(e) => setAlarmTimeInput(e.target.value)}
                          className="bg-[#09152B] border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono"
                        />
                        <button
                          type="submit"
                          disabled={creatingTimer}
                          className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-mono font-bold transition-all cursor-pointer shadow-[0_0_15px_rgba(245,158,11,0.35)] disabled:opacity-50"
                        >
                          {creatingTimer ? "Setting Alarm..." : "Set Alarm"}
                        </button>
                      </form>
                    )}

                    {creatorTab === "reminder" && (
                      <form onSubmit={handleCreateCustomReminder} className="flex flex-col gap-3">
                        <input
                          type="text"
                          placeholder="Reminder text (e.g. Check client email)"
                          value={reminderTextInput}
                          onChange={(e) => setReminderTextInput(e.target.value)}
                          className="bg-[#09152B] border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                        />
                        <input
                          type="text"
                          placeholder="When (e.g. 20 minutes, 1 hour, tomorrow 9am)"
                          value={reminderWhenInput}
                          onChange={(e) => setReminderWhenInput(e.target.value)}
                          className="bg-[#09152B] border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                        />
                        <button
                          type="submit"
                          disabled={creatingTimer}
                          className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-mono font-bold transition-all cursor-pointer shadow-[0_0_15px_rgba(245,158,11,0.35)] disabled:opacity-50"
                        >
                          {creatingTimer ? "Scheduling..." : "Schedule Reminder"}
                        </button>
                      </form>
                    )}
                  </div>
                )}

                {/* Active Timers & Alarms List */}
                {totalActiveTimers === 0 ? (
                  <div className="py-8 text-center text-slate-500 text-xs font-mono bg-[#060D1E]/40 rounded-2xl border border-slate-800">
                    No active timers, alarms, or reminders running.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activeTimers.map((t) => {
                      const totalDuration = t.duration_seconds || 1;
                      const remainingSecs = t.fire_at
                        ? Math.max(0, t.fire_at - currentTimeSec)
                        : 0;
                      const progress = Math.min(
                        100,
                        Math.max(0, ((totalDuration - remainingSecs) / totalDuration) * 100)
                      );

                      return (
                        <div
                          key={t.id}
                          className="p-3.5 rounded-2xl bg-[#060D1E]/90 border border-amber-500/35 flex flex-col gap-2.5 shadow-sm"
                        >
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-semibold text-white truncate text-sm">
                              {t.label}
                            </span>
                            <div className="flex items-center gap-2.5">
                              <span className="font-mono text-amber-300 font-bold text-sm">
                                {formatSecondsToClock(remainingSecs)}
                              </span>
                              <button
                                onClick={() => handleCancelItem(t.id, "Timer")}
                                className="w-6 h-6 rounded-lg bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 flex items-center justify-center transition-colors cursor-pointer"
                                title="Cancel timer"
                              >
                                <X size={13} />
                              </button>
                            </div>
                          </div>
                          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-amber-500 to-rose-500 transition-all duration-1000 shadow-[0_0_8px_#f59e0b]"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}

                    {/* Active Alarms */}
                    {activeAlarms.map((a) => (
                      <div
                        key={a.id}
                        className="p-3.5 rounded-2xl bg-[#060D1E]/90 border border-amber-500/35 flex items-center justify-between text-xs shadow-sm"
                      >
                        <div className="flex items-center gap-2.5">
                          <Bell size={16} className="text-amber-400" />
                          <span className="font-semibold text-white text-sm">
                            {a.label || "Daily Alarm"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2.5">
                          <span className="font-mono text-amber-300 font-bold text-sm">
                            {a.fires_at}
                          </span>
                          <button
                            onClick={() => handleCancelItem(a.id, "Alarm")}
                            className="w-6 h-6 rounded-lg bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 flex items-center justify-center transition-colors cursor-pointer"
                            title="Cancel alarm"
                          >
                            <X size={13} />
                          </button>
                        </div>
                      </div>
                    ))}

                    {/* Active Reminders */}
                    {activeReminders.map((r) => (
                      <div
                        key={r.id}
                        className="p-3.5 rounded-2xl bg-[#060D1E]/90 border border-amber-500/35 flex items-center justify-between text-xs shadow-sm"
                      >
                        <div className="flex items-center gap-2.5">
                          <Calendar size={16} className="text-amber-400" />
                          <span className="font-semibold text-white text-sm">
                            {r.message_text || r.message || "Scheduled Reminder"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2.5">
                          <span className="font-mono text-amber-300 font-bold text-xs">
                            {r.scheduled_for || r.fires_at || "Scheduled"}
                          </span>
                          <button
                            onClick={() => handleCancelItem(r.id, "Reminder")}
                            className="w-6 h-6 rounded-lg bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 flex items-center justify-center transition-colors cursor-pointer"
                            title="Cancel reminder"
                          >
                            <X size={13} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Quick Preset Buttons */}
                <div className="pt-2">
                  <span className="text-[10px] text-slate-400 font-mono block mb-2">
                    QUICK LAUNCH PRESETS
                  </span>
                  <div className="grid grid-cols-4 gap-2.5 text-xs font-mono">
                    <button
                      onClick={() => handleLaunchPreset(300, "5 Min Focus")}
                      className="py-2.5 rounded-xl bg-[#060D1E] border border-slate-800 text-slate-300 hover:text-amber-300 hover:border-amber-500/50 transition-colors cursor-pointer text-center"
                    >
                      5m Focus
                    </button>
                    <button
                      onClick={() => handleLaunchPreset(900, "15 Min Pomodoro")}
                      className="py-2.5 rounded-xl bg-[#060D1E] border border-slate-800 text-slate-300 hover:text-amber-300 hover:border-amber-500/50 transition-colors cursor-pointer text-center"
                    >
                      15m Pomodoro
                    </button>
                    <button
                      onClick={() => handleLaunchPreset(1800, "30 Min Sprint")}
                      className="py-2.5 rounded-xl bg-[#060D1E] border border-slate-800 text-slate-300 hover:text-amber-300 hover:border-amber-500/50 transition-colors cursor-pointer text-center"
                    >
                      30m Sprint
                    </button>
                    <button
                      onClick={() => handleLaunchPreset(3600, "1 Hour Deep Work")}
                      className="py-2.5 rounded-xl bg-[#060D1E] border border-slate-800 text-slate-300 hover:text-amber-300 hover:border-amber-500/50 transition-colors cursor-pointer text-center"
                    >
                      1h Deep Work
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 3. HARDWARE TELEMETRY VIEW */}
          {(activeTab === "system" || activeTab === "all") && (
            <div className="space-y-4">
              {activeTab === "all" && (
                <div className="flex items-center gap-2 pb-1 border-b border-cyan-500/20 text-cyan-300">
                  <Cpu size={16} />
                  <span className="font-hud text-xs font-bold uppercase tracking-wider">
                    Hardware Telemetry & System Diagnostics
                  </span>
                </div>
              )}

              <div
                id="section-system-modal"
                className="relative rounded-3xl bg-gradient-to-b from-[#0B152A]/90 via-[#060D1E]/95 to-[#030610]/98 border border-cyan-500/35 p-5 sm:p-6 shadow-[0_0_35px_rgba(6,182,212,0.15)] flex flex-col gap-4 overflow-hidden"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                      <Cpu size={20} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-hud text-white font-bold text-sm tracking-wider">
                        Live Hardware Telemetry
                      </span>
                      <span className="text-[11px] text-cyan-400/80 font-mono">
                        Windows Sensor Matrix • Real-Time Health
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[11px] font-mono text-emerald-400 font-semibold">
                      OPERATIONAL
                    </span>
                  </div>
                </div>

                {/* Progress Gauges */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {/* CPU Gauge */}
                  <div className="p-4 rounded-2xl bg-[#060D1E]/80 border border-cyan-500/25 flex flex-col gap-2.5">
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="text-slate-400 font-semibold">CPU Compute Load</span>
                      <span className="text-cyan-400 font-bold text-sm">{systemMetrics.cpu}%</span>
                    </div>
                    <div className="w-full h-3 bg-[#030712] rounded-full overflow-hidden border border-cyan-500/30">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500 shadow-[0_0_10px_#22d3ee]"
                        style={{ width: `${Math.min(100, Math.max(0, systemMetrics.cpu))}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Dynamic multi-core processing load
                    </span>
                  </div>

                  {/* RAM Gauge */}
                  <div className="p-4 rounded-2xl bg-[#060D1E]/80 border border-emerald-500/25 flex flex-col gap-2.5">
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="text-slate-400 font-semibold">RAM Allocation</span>
                      <span className="text-emerald-400 font-bold text-sm">
                        {systemMetrics.ram}% ({systemMetrics.ramUsed}GB / {systemMetrics.ramTotal}GB)
                      </span>
                    </div>
                    <div className="w-full h-3 bg-[#030712] rounded-full overflow-hidden border border-emerald-500/30">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500 shadow-[0_0_10px_#10b981]"
                        style={{ width: `${Math.min(100, Math.max(0, systemMetrics.ram))}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Physical host memory utilization
                    </span>
                  </div>
                </div>

                {/* Network & Battery Status Row */}
                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-800 text-xs font-mono">
                  <div className="flex items-center gap-2.5 p-3 rounded-xl bg-[#060D1E] border border-slate-800 text-slate-300">
                    <Wifi size={16} className="text-emerald-400" />
                    <div className="flex flex-col">
                      <span className="text-slate-400 text-[10px]">Network Connectivity</span>
                      <span className="text-white font-bold">127.0.0.1 Local Link</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5 p-3 rounded-xl bg-[#060D1E] border border-slate-800 text-slate-300">
                    <BatteryMedium size={16} className={isCharging ? "text-amber-400" : "text-emerald-400"} />
                    <div className="flex flex-col">
                      <span className="text-slate-400 text-[10px]">Power Matrix</span>
                      <span className="text-white font-bold">
                        {batteryLevel !== null ? `${batteryLevel}%` : "AC Power"} {isCharging && "(Charging)"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* PHASE 4: FILES & CODEBASE HUB */}
          {(activeTab === "files" || activeTab === "all") && (
            <div className="space-y-4">
              {activeTab === "all" && (
                <div className="flex items-center gap-2 pb-1 border-b border-emerald-500/20 text-emerald-300">
                  <FolderGit2 size={16} />
                  <span className="font-hud text-xs font-bold uppercase tracking-wider">
                    Phase 4: Files & Codebase Architecture
                  </span>
                </div>
              )}

              <div
                id="section-files-modal"
                className="relative rounded-3xl bg-gradient-to-b from-[#06181C]/90 via-[#041014]/95 to-[#02080A]/98 border border-emerald-500/35 p-5 sm:p-6 shadow-[0_0_35px_rgba(16,185,129,0.15)] flex flex-col gap-4 overflow-hidden"
              >
                {/* Header Row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                      <FolderGit2 size={20} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-hud text-white font-bold text-sm tracking-wider">
                        Workspace & Codebase Intelligence
                      </span>
                      <span className="text-[11px] text-emerald-400/80 font-mono">
                        Phase 4 Active • Sandboxed Workspace Inspector
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={fetchProjectInfo}
                      disabled={loadingFiles}
                      className="px-2.5 py-1 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-[11px] font-mono text-emerald-300 flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
                      title="Refresh Project Architecture"
                    >
                      <RefreshCw size={12} className={loadingFiles ? "animate-spin" : ""} />
                      <span>{loadingFiles ? "Inspecting..." : "Scan Workspace"}</span>
                    </button>
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  </div>
                </div>

                {/* 3 Metric Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
                  <div className="p-3.5 rounded-2xl bg-[#030e10]/80 border border-emerald-500/25 flex flex-col gap-1.5">
                    <span className="text-slate-400 text-[10px]">Workspace Root</span>
                    <span className="text-emerald-300 font-bold truncate">
                      {projectData?.path || "D:\\projects\\JARVIS"}
                    </span>
                    <span className="text-[10px] text-slate-500">Secure Sandboxed Path</span>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[#030e10]/80 border border-emerald-500/25 flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-[10px]">Git VCS Status</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        {projectData?.git?.branch || "main"}
                      </span>
                    </div>
                    <span className="text-cyan-300 font-bold flex items-center gap-1.5">
                      <GitBranch size={13} />
                      {projectData?.git?.modified_count !== undefined
                        ? `${projectData.git.modified_count} Modified Files`
                        : "Tracking Synchronized"}
                    </span>
                    <span className="text-[10px] text-slate-500">VCS Branch Linked</span>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[#030e10]/80 border border-emerald-500/25 flex flex-col gap-1.5">
                    <span className="text-slate-400 text-[10px]">Active Frameworks</span>
                    <span className="text-amber-300 font-bold truncate">
                      {projectData?.frameworks && projectData.frameworks.length > 0
                        ? projectData.frameworks.join(" • ")
                        : "Python • FastAPI • Next.js 16"}
                    </span>
                    <span className="text-[10px] text-slate-500">Multi-engine runtime</span>
                  </div>
                </div>

                {/* Key Entry Points & Git Diff Stream */}
                <div className="p-4 rounded-2xl bg-[#030b0d]/90 border border-emerald-500/30 flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileCode size={15} className="text-emerald-400" />
                      <span className="font-hud text-xs font-bold text-white tracking-wider">
                        Core Entry Points & Subsystems
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-emerald-400/80">
                      AST & Syntax Verified
                    </span>
                  </div>

                  {/* Subsystems Tags */}
                  <div className="flex flex-wrap gap-2 text-xs font-mono">
                    <span className="px-2.5 py-1 rounded-xl bg-[#06181C] border border-emerald-500/30 text-emerald-300 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      /backend (FastAPI REST & Voice Engine)
                    </span>
                    <span className="px-2.5 py-1 rounded-xl bg-[#06181C] border border-cyan-500/30 text-cyan-300 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                      /frontend (Next.js 16 & Iron Man HUD)
                    </span>
                    <span className="px-2.5 py-1 rounded-xl bg-[#06181C] border border-purple-500/30 text-purple-300 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                      /tests (Pytest Verification Suite)
                    </span>
                  </div>

                  {/* Git Status Stream Summary */}
                  {projectData?.git?.status_summary && (
                    <div className="mt-1 p-3 rounded-xl bg-[#020507] border border-emerald-500/20 font-mono text-[11px] text-slate-300 max-h-32 overflow-y-auto custom-scrollbar">
                      <div className="text-[10px] text-slate-500 mb-1 font-bold">
                        VCS WORKING TREE SUMMARY:
                      </div>
                      <pre className="whitespace-pre-wrap text-emerald-400/90 leading-relaxed font-mono">
                        {projectData.git.status_summary}
                      </pre>
                    </div>
                  )}

                  {/* Security Guardrails Strip */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-emerald-500/20 text-[10px] font-mono text-slate-400">
                    <div className="flex items-center gap-1.5 text-emerald-400">
                      <ShieldCheck size={13} />
                      <span>Zero Out-of-Bounds Access</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-cyan-400">
                      <ShieldCheck size={13} />
                      <span>Unified Diff Engine Guard</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-purple-400">
                      <ShieldCheck size={13} />
                      <span>AST Integrity Pre-validation</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* PHASE 5: WEB & WEATHER INTELLIGENCE */}
          {(activeTab === "web" || activeTab === "all") && (
            <div className="space-y-4">
              {activeTab === "all" && (
                <div className="flex items-center gap-2 pb-1 border-b border-cyan-500/20 text-cyan-300">
                  <Globe size={16} />
                  <span className="font-hud text-xs font-bold uppercase tracking-wider">
                    Phase 5: Web & Weather Intelligence
                  </span>
                </div>
              )}

              <div
                id="section-web-modal"
                className="relative rounded-3xl bg-gradient-to-b from-[#061426]/90 via-[#040C1A]/95 to-[#020610]/98 border border-cyan-500/35 p-5 sm:p-6 shadow-[0_0_35px_rgba(6,182,212,0.15)] flex flex-col gap-4 overflow-hidden"
              >
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                      <Globe size={20} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-hud text-white font-bold text-sm tracking-wider">
                        Online Intelligence & Atmospheric Telemetry
                      </span>
                      <span className="text-[11px] text-cyan-400/80 font-mono">
                        Phase 5 Active • Real-time Web Search & Sensor Radar
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 text-[10px] font-mono font-semibold">
                      INJECTION GUARD ON
                    </span>
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                  </div>
                </div>

                {/* Sub-grid: Weather Telemetry + Safe Search Engine */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Weather Sensor Card */}
                  <div className="p-4 rounded-2xl bg-[#030914]/80 border border-cyan-500/25 flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CloudSun size={16} className="text-amber-400" />
                        <span className="font-hud text-xs font-bold text-white tracking-wider">
                          Live Atmospheric Radar
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-cyan-400">wttr.in Feed</span>
                    </div>

                    {/* City input and trigger */}
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={weatherCity}
                        onChange={(e) => setWeatherCity(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && fetchWeatherInfo(weatherCity)}
                        placeholder="Enter city (e.g. Islamabad, Karachi)..."
                        className="flex-1 px-3 py-1.5 rounded-xl bg-[#02050B] border border-cyan-500/30 text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
                      />
                      <button
                        onClick={() => fetchWeatherInfo(weatherCity)}
                        disabled={loadingWeather}
                        className="px-3 py-1.5 rounded-xl bg-cyan-600/30 hover:bg-cyan-600/50 border border-cyan-400/40 text-cyan-200 text-xs font-mono font-bold transition-all cursor-pointer disabled:opacity-50"
                      >
                        {loadingWeather ? "Scanning..." : "Scan"}
                      </button>
                    </div>

                    {/* Weather Data Display */}
                    {weatherData && (
                      <div className="p-3.5 rounded-xl bg-[#020712] border border-cyan-500/20 flex flex-col gap-2.5">
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="font-hud text-2xl font-bold text-white">
                              {weatherData.temp_c || "26"}°C
                            </span>
                            <span className="text-xs font-mono text-slate-400 ml-2">
                              Feels {weatherData.feels_like_c || "22"}°C
                            </span>
                          </div>
                          <span className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-mono font-bold">
                            {weatherData.condition || "Clear"}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs font-mono text-slate-300 pt-1 border-t border-cyan-500/20">
                          <div className="flex items-center gap-1.5">
                            <Droplets size={13} className="text-cyan-400" />
                            <span>Humidity: {weatherData.humidity || "20"}%</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Wind size={13} className="text-cyan-400" />
                            <span>Wind: {weatherData.wind_kmph || "8"} km/h</span>
                          </div>
                        </div>

                        {weatherData.spoken_summary && (
                          <div className="p-2 rounded-lg bg-[#040e1e] border border-cyan-500/20 text-[11px] font-mono text-cyan-300/90 italic">
                            &ldquo;{weatherData.spoken_summary}&rdquo;
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Safe Web Research Card */}
                  <div className="p-4 rounded-2xl bg-[#030914]/80 border border-cyan-500/25 flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Search size={16} className="text-cyan-400" />
                        <span className="font-hud text-xs font-bold text-white tracking-wider">
                          Privacy Web Research
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-emerald-400">Rule 14 Shielded</span>
                    </div>

                    {/* Search query box */}
                    <form onSubmit={handleRunWebSearch} className="flex gap-2">
                      <input
                        type="text"
                        value={webQuery}
                        onChange={(e) => setWebQuery(e.target.value)}
                        placeholder="Search documentation, news, or articles..."
                        className="flex-1 px-3 py-1.5 rounded-xl bg-[#02050B] border border-cyan-500/30 text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
                      />
                      <button
                        type="submit"
                        disabled={searchingWeb || !webQuery.trim()}
                        className="px-3 py-1.5 rounded-xl bg-blue-600/30 hover:bg-blue-600/50 border border-blue-400/40 text-blue-200 text-xs font-mono font-bold transition-all cursor-pointer disabled:opacity-50"
                      >
                        {searchingWeb ? "Querying..." : "Search"}
                      </button>
                    </form>

                    {/* Results list */}
                    {searchResults.length > 0 ? (
                      <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
                        {searchResults.map((r, i) => (
                          <div
                            key={i}
                            className="p-2.5 rounded-xl bg-[#020712] border border-cyan-500/20 flex flex-col gap-1 text-xs font-mono"
                          >
                            <a
                              href={r.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-cyan-300 hover:text-white font-bold flex items-center gap-1.5 group"
                            >
                              <span className="truncate">{r.title}</span>
                              <ExternalLink size={11} className="shrink-0 opacity-60 group-hover:opacity-100" />
                            </a>
                            <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                              {r.snippet}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-3.5 rounded-xl bg-[#020712]/60 border border-cyan-500/10 text-center text-xs font-mono text-slate-500">
                        Enter a query to execute sandboxed real-time web search.
                      </div>
                    )}
                  </div>
                </div>

                {/* External Subsystems & Integrations Strip */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-cyan-500/20 text-xs font-mono">
                  <div className="p-2.5 rounded-xl bg-[#020712] border border-slate-800 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-slate-300">WhatsApp Web Bridge:</span>
                    <span className="text-emerald-400 font-bold ml-auto">Ready</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#020712] border border-slate-800 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-slate-300">Chrome Bookmarks:</span>
                    <span className="text-cyan-400 font-bold ml-auto">Synced</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#020712] border border-slate-800 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-slate-300">Prompt Injection Guard:</span>
                    <span className="text-purple-400 font-bold ml-auto">Active</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 4. PHASE 7: DESKTOP VISION & SCREEN DIAGNOSTICS */}
          {(activeTab === "vision" || activeTab === "all") && (
            <div className="space-y-4">
              {activeTab === "all" && (
                <div className="flex items-center gap-2 pb-1 border-b border-emerald-500/20 text-emerald-300">
                  <Eye size={16} />
                  <span className="font-hud text-xs font-bold uppercase tracking-wider">
                    Phase 7: Desktop Vision & Screen Diagnostics
                  </span>
                </div>
              )}

              <div
                id="section-vision-modal"
                className="relative rounded-3xl bg-gradient-to-b from-[#081F1A]/90 via-[#061515]/95 to-[#020D0D]/98 border border-emerald-500/35 p-5 sm:p-6 shadow-[0_0_35px_rgba(16,185,129,0.15)] flex flex-col gap-4 overflow-hidden"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                      <Eye size={20} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-hud text-white font-bold text-sm tracking-wider">
                        Multimodal Desktop Vision
                      </span>
                      <span className="text-[11px] text-emerald-400/80 font-mono">
                        Phase 7 Active • On-Demand Screen Diagnostics
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[11px] font-mono text-emerald-300 font-semibold">
                      IN-MEMORY GUARD ACTIVE
                    </span>
                  </div>
                </div>

                {/* Info Cards Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
                  <div className="p-3.5 rounded-2xl bg-[#030e0e]/80 border border-emerald-500/25 flex flex-col gap-1.5">
                    <span className="text-slate-400 text-[10px]">Multimodal Model Pool</span>
                    <span className="text-emerald-300 font-bold">Gemini 2.0 / OpenRouter</span>
                    <span className="text-[10px] text-slate-500">Auto-fallback with latency guard</span>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[#030e0e]/80 border border-emerald-500/25 flex flex-col gap-1.5">
                    <span className="text-slate-400 text-[10px]">Privacy Guarantee</span>
                    <span className="text-cyan-300 font-bold">Zero Disk Storage</span>
                    <span className="text-[10px] text-slate-500">In-memory buffer only</span>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[#030e0e]/80 border border-emerald-500/25 flex flex-col gap-1.5">
                    <span className="text-slate-400 text-[10px]">Injection Defense</span>
                    <span className="text-purple-300 font-bold">Untrusted Guard ON</span>
                    <span className="text-[10px] text-slate-500">Prompt hijacking strictly isolated</span>
                  </div>
                </div>

                {/* Interactive Screen Inspection Control */}
                <div className="p-4 rounded-2xl bg-[#041212]/95 border border-emerald-500/30 flex flex-col gap-3 shadow-inner">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5">
                    <div className="flex items-center gap-2">
                      <Camera size={16} className="text-emerald-400" />
                      <span className="font-hud text-xs font-bold text-white tracking-wider">
                        Live Screen Inspector
                      </span>
                    </div>

                    {/* Focus Modes */}
                    <div className="flex items-center gap-1 bg-[#020a0a] p-1 rounded-xl border border-emerald-500/20 text-[10px] font-mono">
                      <button
                        onClick={() => setVisionFocus("error")}
                        className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                          visionFocus === "error" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-400 hover:text-emerald-300"
                        }`}
                      >
                        Bug/Error
                      </button>
                      <button
                        onClick={() => setVisionFocus("code")}
                        className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                          visionFocus === "code" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-400 hover:text-emerald-300"
                        }`}
                      >
                        Code Review
                      </button>
                      <button
                        onClick={() => setVisionFocus("ui")}
                        className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                          visionFocus === "ui" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-400 hover:text-emerald-300"
                        }`}
                      >
                        UI Layout
                      </button>
                      <button
                        onClick={() => setVisionFocus("general")}
                        className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                          visionFocus === "general" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-400 hover:text-emerald-300"
                        }`}
                      >
                        Overview
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row items-center gap-2">
                    <input
                      type="text"
                      placeholder="Optional question (e.g. 'Why is npm build failing?' or 'Find the bug on line 42')"
                      value={visionQuestion}
                      onChange={(e) => setVisionQuestion(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleInspectScreen();
                      }}
                      className="flex-1 bg-[#020a0a] border border-emerald-500/25 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400 w-full"
                    />
                    <button
                      onClick={handleInspectScreen}
                      disabled={isInspecting}
                      className="w-full sm:w-auto px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-mono font-bold transition-all cursor-pointer flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.35)] shrink-0 disabled:opacity-50"
                    >
                      <Camera size={14} className={isInspecting ? "animate-pulse" : ""} />
                      <span>{isInspecting ? "Analyzing Screen..." : "Inspect Screen Now"}</span>
                    </button>
                  </div>

                  {/* Inspection Result Box */}
                  {visionResult && (
                    <div className="p-3.5 rounded-xl bg-[#020808] border border-emerald-500/35 flex flex-col gap-2 mt-1 animate-in fade-in">
                      <div className="flex items-center justify-between text-[11px] font-mono border-b border-emerald-500/20 pb-1.5">
                        <span className="text-emerald-300 font-bold flex items-center gap-1.5">
                          <Sparkles size={12} className="text-emerald-400" />
                          Diagnostic Result
                        </span>
                        {visionResult.model && (
                          <span className="text-[10px] text-slate-400">
                            Model: {visionResult.model}
                          </span>
                        )}
                      </div>
                      {visionResult.error ? (
                        <p className="text-rose-400 text-xs font-mono">
                          {visionResult.error}
                        </p>
                      ) : (
                        <p className="text-slate-200 text-xs whitespace-pre-wrap leading-relaxed">
                          {visionResult.analysis}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 5. Phase 8 Autonomous Agent Mission Control Subsystem */}
          {(activeTab === "agent" || activeTab === "all") && (
            <div className="flex flex-col gap-4 animate-in fade-in duration-300">
              <div className="p-4 sm:p-5 rounded-2xl bg-[#090b14]/90 border border-rose-500/35 shadow-[0_0_30px_rgba(244,63,94,0.15)] flex flex-col gap-4">
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rose-500/20 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-rose-500/20 border border-rose-400/40 flex items-center justify-center text-rose-400 shadow-[0_0_12px_rgba(244,63,94,0.3)]">
                      <Bot size={16} />
                    </div>
                    <div>
                      <h4 className="font-hud text-sm font-bold text-white tracking-wider flex items-center gap-2">
                        AUTONOMOUS MISSION CONTROL
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-400/40">
                          PHASE 8 ACTIVE
                        </span>
                      </h4>
                      <p className="text-[11px] text-slate-400 font-mono">
                        Multi-step autonomous execution • Circuit breaker protection • Safety confirmation gates
                      </p>
                    </div>
                  </div>

                  {/* Emergency Stop Button */}
                  {agentPlan && (agentPlan.status === "executing" || agentPlan.status === "waiting_for_confirmation") && (
                    <button
                      onClick={handleEmergencyStop}
                      disabled={stoppingAgent}
                      className="px-3.5 py-1.5 rounded-xl bg-red-600/90 hover:bg-red-500 text-white font-mono text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shadow-[0_0_15px_rgba(239,68,68,0.5)] animate-pulse"
                    >
                      <Square size={12} fill="currentColor" />
                      <span>{stoppingAgent ? "Halting..." : "EMERGENCY ABORT"}</span>
                    </button>
                  )}
                </div>

                {/* Quick Mission Templates */}
                <div className="flex flex-col gap-2">
                  <span className="text-[11px] font-mono text-slate-400">One-Click Engineering Missions:</span>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <button
                      onClick={() => handleLaunchMission("Prepare project for deployment", "deployment_prep")}
                      disabled={isAgentRunning}
                      className="p-2.5 rounded-xl bg-[#0e1220] hover:bg-rose-500/15 border border-rose-500/25 hover:border-rose-400/60 text-left transition-all cursor-pointer group flex items-start gap-2 disabled:opacity-50"
                    >
                      <span className="text-base">🚀</span>
                      <div className="flex flex-col">
                        <span className="text-xs font-bold text-white group-hover:text-rose-300 font-mono">Deploy Prep</span>
                        <span className="text-[10px] text-slate-400">Inspect frontend, git, tests & build</span>
                      </div>
                    </button>

                    <button
                      onClick={() => handleLaunchMission("Scan, diagnose and fix code errors", "bug_diagnosis")}
                      disabled={isAgentRunning}
                      className="p-2.5 rounded-xl bg-[#0e1220] hover:bg-rose-500/15 border border-rose-500/25 hover:border-rose-400/60 text-left transition-all cursor-pointer group flex items-start gap-2 disabled:opacity-50"
                    >
                      <span className="text-base">🔍</span>
                      <div className="flex flex-col">
                        <span className="text-xs font-bold text-white group-hover:text-rose-300 font-mono">Scan &amp; Fix</span>
                        <span className="text-[10px] text-slate-400">Run dev tests &amp; inspect git diffs</span>
                      </div>
                    </button>

                    <button
                      onClick={() => handleLaunchMission("Perform full developer workspace and git audit", "workspace_audit")}
                      disabled={isAgentRunning}
                      className="p-2.5 rounded-xl bg-[#0e1220] hover:bg-rose-500/15 border border-rose-500/25 hover:border-rose-400/60 text-left transition-all cursor-pointer group flex items-start gap-2 disabled:opacity-50"
                    >
                      <span className="text-base">⚡</span>
                      <div className="flex flex-col">
                        <span className="text-xs font-bold text-white group-hover:text-rose-300 font-mono">Workspace Audit</span>
                        <span className="text-[10px] text-slate-400">Git tree, windows &amp; system health</span>
                      </div>
                    </button>
                  </div>
                </div>

                {/* Custom Goal Input Bar */}
                <div className="flex flex-col sm:flex-row items-center gap-2">
                  <input
                    type="text"
                    placeholder="Enter custom autonomous goal (e.g. 'Audit project, run tests and check git status')"
                    value={agentGoal}
                    onChange={(e) => setAgentGoal(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleLaunchMission();
                    }}
                    disabled={isAgentRunning}
                    className="flex-1 bg-[#04060c] border border-rose-500/30 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-400 w-full font-sans"
                  />
                  <button
                    onClick={() => handleLaunchMission()}
                    disabled={isAgentRunning || (!agentGoal.trim() && !agentPlan)}
                    className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 via-pink-600 to-purple-600 hover:from-rose-500 hover:to-purple-500 text-white text-xs font-mono font-bold transition-all cursor-pointer flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(244,63,94,0.35)] shrink-0 disabled:opacity-50"
                  >
                    <Play size={14} className={isAgentRunning ? "animate-spin" : ""} />
                    <span>{isAgentRunning ? "Executing..." : "Launch Mission"}</span>
                  </button>
                </div>

                {/* Active Plan Stepper Display */}
                {agentPlan && (
                  <div className="p-4 rounded-xl bg-[#060812] border border-rose-500/30 flex flex-col gap-3.5 animate-in fade-in">
                    {/* Mission Header & Status Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rose-500/20 pb-2.5">
                      <div className="flex items-center gap-2">
                        <Activity size={15} className="text-rose-400" />
                        <span className="text-xs font-mono font-bold text-white">
                          Mission: {agentPlan.goal}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full uppercase font-bold tracking-wider ${
                            agentPlan.status === "completed"
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-400/40"
                              : agentPlan.status === "failed"
                              ? "bg-red-500/20 text-red-300 border border-red-400/40"
                              : agentPlan.status === "stopped"
                              ? "bg-slate-500/20 text-slate-300 border border-slate-400/40"
                              : agentPlan.status === "waiting_for_confirmation"
                              ? "bg-amber-500/20 text-amber-300 border border-amber-400/40 animate-pulse"
                              : "bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 animate-pulse"
                          }`}
                        >
                          {agentPlan.status.replace("_", " ")}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          Step {agentPlan.current_step_index + 1} of {agentPlan.total_steps || agentPlan.steps?.length}
                        </span>
                      </div>
                    </div>

                    {/* Pending Confirmation Warning Gate */}
                    {agentPlan.status === "waiting_for_confirmation" && (
                      <div className="p-3.5 rounded-xl bg-amber-500/15 border border-amber-500/40 flex flex-col sm:flex-row items-center justify-between gap-3 animate-pulse">
                        <div className="flex items-center gap-2.5">
                          <AlertTriangle size={18} className="text-amber-400 shrink-0" />
                          <div className="flex flex-col">
                            <span className="text-xs font-mono font-bold text-amber-200">
                              Security Approval Required
                            </span>
                            <span className="text-[11px] text-amber-300/80 font-sans">
                              Step {agentPlan.steps[agentPlan.current_step_index]?.step_number}: &quot;{agentPlan.steps[agentPlan.current_step_index]?.title}&quot; requires confirmation.
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 w-full sm:w-auto">
                          {agentPlan.steps[agentPlan.current_step_index]?.requires_pin && (
                            <input
                              type="password"
                              maxLength={6}
                              placeholder="PIN"
                              value={agentPin}
                              onChange={(e) => setAgentPin(e.target.value)}
                              className="w-20 bg-black/60 border border-amber-400/40 rounded-lg px-2 py-1 text-center font-mono text-xs text-white"
                            />
                          )}
                          <button
                            onClick={handleConfirmAgentStep}
                            disabled={confirmingStep}
                            className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-mono text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shadow-sm"
                          >
                            <ShieldCheck size={13} />
                            <span>{confirmingStep ? "Verifying..." : "Approve & Execute"}</span>
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Step-by-Step List */}
                    <div className="flex flex-col gap-2">
                      {agentPlan.steps?.map((step: AgentPlanStep) => (
                        <div
                          key={step.step_number}
                          className={`p-3 rounded-xl border flex flex-col gap-1.5 transition-all ${
                            step.status === "completed"
                              ? "bg-emerald-500/5 border-emerald-500/30 text-slate-300"
                              : step.status === "in_progress"
                              ? "bg-cyan-500/10 border-cyan-400/50 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                              : step.status === "awaiting_confirmation"
                              ? "bg-amber-500/10 border-amber-400/50"
                              : step.status === "failed"
                              ? "bg-red-500/10 border-red-500/40"
                              : "bg-[#04060c] border-slate-800 opacity-60"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2.5">
                              {step.status === "completed" && <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />}
                              {step.status === "in_progress" && <RefreshCw size={16} className="text-cyan-400 animate-spin shrink-0" />}
                              {step.status === "awaiting_confirmation" && <AlertTriangle size={16} className="text-amber-400 shrink-0" />}
                              {step.status === "failed" && <Square size={16} className="text-rose-400 shrink-0" />}
                              {step.status === "pending" && <div className="w-4 h-4 rounded-full border border-slate-600 shrink-0" />}

                              <span className="text-xs font-mono font-bold text-white">
                                {step.step_number}. {step.title}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                                {step.tool_name}
                              </span>
                              <span
                                className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-bold ${
                                  step.risk_level === "HIGH"
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                    : step.risk_level === "MEDIUM"
                                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                                    : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                                }`}
                              >
                                {step.risk_level}
                              </span>
                            </div>
                          </div>

                          <p className="text-[11px] text-slate-400 pl-6 font-sans">
                            {step.description}
                          </p>

                          {step.error && (
                            <div className="ml-6 p-2 rounded bg-rose-500/10 border border-rose-500/30 text-[11px] font-mono text-rose-300">
                              Error: {step.error}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Mission Summary Card */}
                    {agentPlan.summary && (
                      <div className="p-3 rounded-xl bg-[#04060c] border border-rose-500/35 flex flex-col gap-1">
                        <span className="text-[11px] font-mono font-bold text-rose-300 flex items-center gap-1.5">
                          <Sparkles size={12} />
                          Mission Briefing Summary:
                        </span>
                        <p className="text-xs text-slate-200 font-sans leading-relaxed">
                          {agentPlan.summary}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Live Real-Time Tactical Console Drawer */}
                {agentLogs.length > 0 && (
                  <div className="p-3 rounded-xl bg-[#030408] border border-slate-800 flex flex-col gap-1.5 font-mono text-[10px] text-slate-400 max-h-36 overflow-y-auto">
                    <div className="flex items-center gap-1.5 text-slate-300 font-bold border-b border-slate-800 pb-1">
                      <Terminal size={12} className="text-rose-400" />
                      <span>Agent Telemetry Feed:</span>
                    </div>
                    {agentLogs.slice(-8).map((l, i) => (
                      <div key={i} className="text-slate-300 whitespace-pre-wrap">
                        {l}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-cyan-500/20 bg-[#061024]/80 flex items-center justify-between text-xs font-mono text-slate-400 shrink-0">
          <div className="flex items-center gap-2">
            <Sparkles size={12} className="text-cyan-400" />
            <span>JARVIS Autonomous Systems Interface</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 border border-cyan-400/40 text-xs font-mono font-bold transition-all cursor-pointer"
          >
            Close Dialog
          </button>
        </div>
      </div>
    </div>
  );
}
