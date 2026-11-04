"use client";

import React, { useState } from "react";
import {
  Home, MessageSquare, Mic, ShieldCheck, Cpu, FolderGit2,
  Globe, Timer, BrainCircuit, Zap, Terminal, ChevronLeft,
  ChevronRight, Lock, Activity
} from "lucide-react";
import { CreatorDossierData } from "./CreatorDossierModal";

export interface SidebarProps {
  dossier: CreatorDossierData | null;
  isVaultUnlocked: boolean;
  onOpenDossier: () => void;
  onPreviewVoice: (lang: "ur" | "en") => void;
  isSpeaking: boolean;
  isListening: boolean;
  isWakeWordEnabled: boolean;
  isContinuousConversation: boolean;
  onToggleWakeWord: () => void;
  onToggleContinuous: () => void;
  systemMetrics: { cpu: number; ram: number; ramUsed: number; ramTotal: number };
  activeTimersCount: number;
  onOpenTimerCreator?: () => void;
  onFocusChatInput?: () => void;
  activeTab?: string;
  onSelectTab?: (tab: string) => void;
  className?: string;
  collapsible?: boolean;
}

interface NavItemConfig {
  id: string;
  label: string;
  icon: React.ReactNode;
  badge?: string;
  badgeColor?: string;
  action?: () => void;
  locked?: boolean;
}

interface NavCategoryConfig {
  label: string;
  items: NavItemConfig[];
}

export function Sidebar({
  dossier,
  isVaultUnlocked,
  onOpenDossier,
  isSpeaking,
  isListening,
  isContinuousConversation,
  systemMetrics,
  activeTimersCount,
  onOpenTimerCreator,
  onFocusChatInput,
  activeTab = "dashboard",
  onSelectTab,
  className,
  collapsible = false,
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [currentTab, setCurrentTab] = useState(activeTab);

  const handleNavClick = (tabId: string, action?: () => void) => {
    setCurrentTab(tabId);
    if (onSelectTab) onSelectTab(tabId);
    if (action) action();

    // Scroll to specific sections if they exist
    if (tabId === "dashboard" || tabId === "voice") {
      const el = document.getElementById("jarvis-orb-trigger");
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (tabId === "chat") {
      if (onFocusChatInput) onFocusChatInput();
    } else if (tabId === "timers") {
      if (onOpenTimerCreator) onOpenTimerCreator();
      const el = document.getElementById("section-timers");
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (tabId === "system") {
      const el = document.getElementById("section-system-matrix");
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (tabId === "memory") {
      const el = document.getElementById("section-memory-matrix");
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  const navCategories: NavCategoryConfig[] = [
    {
      label: "CORE INTELLIGENCE",
      items: [
        {
          id: "dashboard",
          label: "Dashboard HUD",
          icon: <Home size={16} />,
          badge: "Active",
          badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-400/40",
          action: () => handleNavClick("dashboard"),
        },
        {
          id: "voice",
          label: "Voice Comms & Orb",
          icon: <Mic size={16} />,
          badge: isContinuousConversation ? "Open Mic" : isListening ? "Listening" : isSpeaking ? "Speaking" : "Neural",
          badgeColor: isContinuousConversation
            ? "bg-emerald-500/25 text-emerald-300 border-emerald-500/50 animate-pulse"
            : isListening
            ? "bg-purple-500/25 text-purple-300 border-purple-500/50 animate-pulse"
            : "bg-blue-500/20 text-blue-300 border-blue-400/40",
          action: () => handleNavClick("voice"),
        },
        {
          id: "chat",
          label: "Tactical Console",
          icon: <MessageSquare size={16} />,
          badge: "Live",
          badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-400/40",
          action: () => handleNavClick("chat"),
        },
        {
          id: "dossier",
          label: "Creator Dossier",
          icon: <ShieldCheck size={16} className="text-cyan-400" />,
          badge: isVaultUnlocked ? "ROOT" : "PIN Gated",
          badgeColor: isVaultUnlocked
            ? "bg-emerald-500/25 text-emerald-300 border-emerald-500/50 font-bold"
            : "bg-amber-500/25 text-amber-300 border-amber-500/40",
          action: () => {
            setCurrentTab("dossier");
            onOpenDossier();
          },
        },
      ],
    },
    {
      label: "TACTICAL MODULES",
      items: [
        {
          id: "system",
          label: "System Matrix",
          icon: <Cpu size={16} />,
          badge: `${systemMetrics.cpu}% CPU`,
          badgeColor: "bg-blue-500/20 text-blue-300 border-blue-400/40 font-mono",
          action: () => handleNavClick("system"),
        },
        {
          id: "files",
          label: "Files & Code Hub",
          icon: <FolderGit2 size={16} />,
          badge: "Phase 4",
          badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          action: () => handleNavClick("files"),
        },
        {
          id: "web",
          label: "Web & Weather Intel",
          icon: <Globe size={16} />,
          badge: "Phase 5",
          badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-400/40",
          action: () => handleNavClick("web"),
        },
        {
          id: "timers",
          label: "Timers & Reminders",
          icon: <Timer size={16} />,
          badge: activeTimersCount > 0 ? `${activeTimersCount} Active` : "Phase 3C",
          badgeColor: activeTimersCount > 0
            ? "bg-amber-500/30 text-amber-300 border-amber-500/60 animate-pulse font-bold"
            : "bg-slate-800/80 text-slate-400 border-slate-700",
          action: () => handleNavClick("timers"),
        },
      ],
    },
    {
      label: "FUTURE EXPANSIONS",
      items: [
        {
          id: "memory",
          label: "Memory Matrix",
          icon: <BrainCircuit size={16} />,
          badge: "Active",
          badgeColor: "bg-emerald-500/25 text-emerald-300 border-emerald-500/50 font-bold",
          locked: false,
          action: () => handleNavClick("memory"),
        },
        {
          id: "vision",
          label: "Desktop Vision",
          icon: <Zap size={16} />,
          badge: "Phase 7",
          badgeColor: "bg-slate-800/80 text-slate-500 border-slate-700/50",
          locked: true,
        },
        {
          id: "agent",
          label: "Autonomous Agent",
          icon: <Terminal size={16} />,
          badge: "Phase 8",
          badgeColor: "bg-slate-800/80 text-slate-500 border-slate-700/50",
          locked: true,
        },
      ],
    },
  ];

  return (
    <aside
      className={`relative h-full flex flex-col bg-gradient-to-b from-[#050B17]/95 via-[#071126]/95 to-[#040814]/98 backdrop-blur-2xl border border-cyan-500/25 text-slate-300 transition-all duration-300 z-40 select-none shadow-[0_8px_35px_rgba(0,0,0,0.7)] rounded-3xl overflow-hidden ${
        className ? className : isCollapsed ? "w-[76px]" : "w-[280px]"
      }`}
    >
      {/* Background Cyber Glow & Holographic Rim Laser */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(6,182,212,0.12),transparent_70%)] pointer-events-none" />
      <div className="absolute top-0 bottom-0 right-0 w-[1px] bg-gradient-to-b from-cyan-400/60 via-blue-500/30 to-transparent pointer-events-none shadow-[0_0_10px_rgba(6,182,212,0.5)]" />

      {/* Floating Seam Collapse / Expand Toggle Button */}
      {collapsible && (
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3.5 top-8 z-50 w-7 h-7 rounded-full bg-[#071126] hover:bg-cyan-500/30 border border-cyan-400/60 text-cyan-300 hover:text-white flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.5)] transition-all cursor-pointer hover:scale-110 active:scale-95"
          title={isCollapsed ? "Expand Sidebar HUD" : "Collapse Sidebar to Mini Rail"}
        >
          {isCollapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
        </button>
      )}

      {/* 1. TOP HEADER - ARC REACTOR LOGO */}
      <div
        className={`relative h-20 flex items-center border-b border-cyan-500/20 bg-[#050D1E]/80 px-4 shrink-0 ${
          isCollapsed ? "justify-center px-2" : "justify-between"
        }`}
      >
        <div className={`flex items-center min-w-0 ${isCollapsed ? "justify-center w-full" : "gap-3"}`}>
          {/* 3D Arc Reactor Mini Brand Icon */}
          <div
            onClick={() => handleNavClick("dashboard")}
            className="relative w-10 h-10 flex items-center justify-center shrink-0 cursor-pointer group"
            title="JARVIS Mark IX Arc Core - Dashboard"
          >
            <div className="absolute inset-0 rounded-xl border border-cyan-400/40 bg-gradient-to-br from-cyan-950/80 to-blue-950/60 shadow-[0_0_15px_rgba(6,182,212,0.4)_inset] group-hover:border-cyan-300 transition-colors" />
            <div className="absolute inset-1 rounded-lg border border-dashed border-cyan-400/40 animate-[spin_10s_linear_infinite]" />
            <div className="relative w-3.5 h-3.5 rounded-full bg-gradient-to-tr from-cyan-300 to-white shadow-[0_0_12px_#22d3ee] flex items-center justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-900 animate-ping" />
            </div>
          </div>

          {!isCollapsed && (
            <div className="flex flex-col min-w-0 animate-in fade-in duration-200">
              <div className="flex items-center gap-1.5">
                <span className="font-hud text-transparent bg-clip-text bg-gradient-to-r from-cyan-200 via-blue-200 to-indigo-200 font-extrabold text-[17px] tracking-[0.2em] drop-shadow-[0_0_8px_rgba(6,182,212,0.6)] leading-none">
                  J.A.R.V.I.S
                </span>
                <span className="text-[9px] font-mono font-bold px-1 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-400/40">
                  IX
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-[9px] font-mono text-slate-400 mt-1">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-400" />
                </span>
                <span className="text-emerald-400 font-bold tracking-wider">ONLINE</span>
                <span className="text-slate-600">•</span>
                <span className="text-cyan-400/80">NEURAL AI OS</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2. CREATOR PROFILE DOSSIER CARD */}
      <div className="p-3 border-b border-cyan-500/15 bg-gradient-to-b from-[#07132B]/50 to-transparent">
        <button
          onClick={onOpenDossier}
          className={`w-full text-left rounded-xl border transition-all duration-300 cursor-pointer group flex items-center relative overflow-hidden ${
            isCollapsed
              ? "justify-center p-2 bg-[#09152C]/80 border-cyan-500/30 hover:border-cyan-400 hover:shadow-[0_0_15px_rgba(6,182,212,0.3)]"
              : "p-2.5 bg-gradient-to-r from-[#09152C] to-[#0D1E3F] border-cyan-500/30 hover:border-cyan-400/80 hover:shadow-[0_0_20px_rgba(6,182,212,0.25)]"
          }`}
          title="Master Creator Dossier (Muhammad Akmal) - Open Vault"
        >
          <div className="relative shrink-0">
            <div className="w-9 h-9 rounded-xl p-[1.5px] bg-gradient-to-tr from-cyan-400 via-blue-500 to-indigo-500 shadow-[0_0_12px_rgba(6,182,212,0.4)] overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={
                  dossier?.personal?.avatar_url ||
                  (dossier?.social_profiles?.github_username
                    ? `https://github.com/${dossier.social_profiles.github_username}.png`
                    : "https://github.com/AkmalDoghar.png")
                }
                alt="Akmal"
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).src = "https://github.com/AkmalDoghar.png";
                }}
                className="w-full h-full object-cover rounded-[10px]"
              />
            </div>
            <div
              className={`absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full flex items-center justify-center border-2 border-[#050B17] ${
                isVaultUnlocked ? "bg-emerald-400" : "bg-cyan-400"
              }`}
            >
              {isVaultUnlocked ? (
                <ShieldCheck size={9} className="text-slate-950 stroke-[3]" />
              ) : (
                <Lock size={8} className="text-slate-950 stroke-[3]" />
              )}
            </div>
          </div>

          {!isCollapsed && (
            <div className="flex flex-col ml-3 min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-mono uppercase tracking-widest font-extrabold text-cyan-400">
                  CREATOR
                </span>
                <span
                  className={`text-[8px] font-mono px-1.5 py-0.2 rounded font-bold border ${
                    isVaultUnlocked
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                      : "bg-cyan-500/15 text-cyan-300 border-cyan-500/30"
                  }`}
                >
                  {isVaultUnlocked ? "ROOT" : "SYNCED"}
                </span>
              </div>
              <span className="text-white font-bold text-xs truncate group-hover:text-cyan-200 transition-colors">
                {dossier?.personal?.preferred_name || dossier?.personal?.name || "Muhammad Akmal"}
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Activity size={10} className="text-emerald-400" />
                <span className="text-[10px] text-slate-400 font-mono truncate">
                  Biometrics Secured
                </span>
              </div>
            </div>
          )}
        </button>
      </div>

      {/* 3. NAVIGATION MODULES LIST */}
      <nav className="flex-1 overflow-y-auto px-2.5 py-3 flex flex-col gap-4 custom-scrollbar">
        {navCategories.map((cat, cIdx) => (
          <div key={cIdx} className="flex flex-col gap-1">
            {!isCollapsed && (
              <div className="flex items-center justify-between px-2 mb-1">
                <span className="text-[9px] font-mono font-bold tracking-[0.2em] text-cyan-400/60 uppercase">
                  {cat.label}
                </span>
                <span className="h-px bg-cyan-500/15 flex-1 ml-2" />
              </div>
            )}

            <div className="flex flex-col gap-1">
              {cat.items.map((item) => {
                const isActive = currentTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      if (!item.locked && item.action) item.action();
                    }}
                    disabled={item.locked}
                    className={`relative flex items-center justify-between w-full rounded-xl transition-all duration-200 group ${
                      isCollapsed ? "px-3 py-3 justify-center" : "px-3 py-2.5"
                    } ${
                      isActive
                        ? "bg-gradient-to-r from-cyan-500/25 via-blue-600/30 to-blue-500/20 text-white border border-cyan-400/50 shadow-[0_0_20px_rgba(6,182,212,0.25)]"
                        : item.locked
                        ? "text-slate-600 hover:bg-transparent cursor-not-allowed border border-transparent"
                        : "text-slate-400 hover:text-white hover:bg-[#0E1A33]/70 hover:border-cyan-500/25 border border-transparent"
                    }`}
                    title={`${item.label} ${item.locked ? "(Pending Phase Release)" : ""}`}
                  >
                    {isActive && (
                      <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
                    )}

                    <div className="flex items-center gap-3 min-w-0">
                      <span
                        className={`transition-colors shrink-0 ${
                          isActive
                            ? "text-cyan-300"
                            : item.locked
                            ? "text-slate-600"
                            : "text-slate-400 group-hover:text-cyan-400"
                        }`}
                      >
                        {item.icon}
                      </span>
                      {!isCollapsed && (
                        <span
                          className={`text-xs font-medium tracking-wide truncate ${
                            isActive ? "font-bold text-white" : ""
                          }`}
                        >
                          {item.label}
                        </span>
                      )}
                    </div>

                    {!isCollapsed && item.badge && (
                      <span
                        className={`text-[9px] font-mono px-2 py-0.5 rounded-full border shrink-0 ${item.badgeColor}`}
                      >
                        {item.badge}
                      </span>
                    )}

                    {isCollapsed && isActive && (
                      <span className="absolute right-1.5 top-1.5 w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#22d3ee]" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* 4. SLEEK MINIMAL FOOTER */}
      <div className="p-3 border-t border-cyan-500/20 bg-gradient-to-b from-[#050D1E]/70 to-[#030712] flex items-center justify-between text-[10px] font-mono text-slate-500 shrink-0">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-400">MARK IX • REV 9.4</span>
        </div>
        <span className="text-cyan-400/80 font-semibold">Akmal Edition ✓</span>
      </div>
    </aside>
  );
}
