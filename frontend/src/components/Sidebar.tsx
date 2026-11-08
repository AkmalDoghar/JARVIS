"use client";

import React, { useState } from "react";
import Image from "next/image";
import {
  Home, MessageSquare, Mic, ShieldCheck, Cpu, FolderGit2,
  Globe, Timer, BrainCircuit, Terminal, ChevronLeft,
  ChevronRight, Lock, Activity, Sparkles, Eye,
  HardDrive
} from "lucide-react";
import { CreatorDossierData } from "./CreatorDossierModal";
import { HudModuleTab } from "./HudModuleModal";

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
  autostartEnabled?: boolean;
  onToggleAutostart?: () => void;
  onOpenTimerCreator?: () => void;
  onFocusChatInput?: () => void;
  activeTab?: string;
  onSelectTab?: (tab: string) => void;
  onOpenHudModal?: (tab: HudModuleTab) => void;
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
  autostartEnabled = false,
  onToggleAutostart,
  onOpenTimerCreator,
  onFocusChatInput,
  activeTab = "dashboard",
  onSelectTab,
  onOpenHudModal,
  className,
  collapsible = false,
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [currentTab, setCurrentTab] = useState(activeTab);

  const handleNavClick = (tabId: string, action?: () => void) => {
    setCurrentTab(tabId);
    if (onSelectTab) onSelectTab(tabId);
    if (action) action();

    // Smooth navigation jumps & modal launches
    if (tabId === "dashboard" || tabId === "voice") {
      const el = document.getElementById("jarvis-orb-trigger");
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (tabId === "chat") {
      if (onFocusChatInput) onFocusChatInput();
    } else if (tabId === "timers") {
      if (onOpenHudModal) onOpenHudModal("timers");
      else if (onOpenTimerCreator) onOpenTimerCreator();
      const el = document.getElementById("section-timers");
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (tabId === "system") {
      if (onOpenHudModal) onOpenHudModal("system");
      const el = document.getElementById("section-system-matrix");
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (tabId === "memory") {
      if (onOpenHudModal) onOpenHudModal("memory");
      const el = document.getElementById("section-memory-matrix");
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (tabId === "files") {
      if (onOpenHudModal) onOpenHudModal("files");
    } else if (tabId === "web") {
      if (onOpenHudModal) onOpenHudModal("web");
    } else if (tabId === "vision") {
      if (onOpenHudModal) onOpenHudModal("vision");
    } else if (tabId === "agent") {
      if (onOpenHudModal) onOpenHudModal("agent");
    }
  };

  const navCategories: NavCategoryConfig[] = [
    {
      label: "COMMAND CORE",
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
          label: "Neural Voice Orb",
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
          id: "timers",
          label: "Chrono & Timers",
          icon: <Timer size={16} />,
          badge: activeTimersCount > 0 ? `${activeTimersCount} Running` : "Ready",
          badgeColor: activeTimersCount > 0
            ? "bg-amber-500/30 text-amber-300 border-amber-500/60 animate-pulse font-bold"
            : "bg-slate-800/80 text-slate-400 border-slate-700",
          action: () => handleNavClick("timers"),
        },
        {
          id: "system",
          label: "System Matrix",
          icon: <Cpu size={16} />,
          badge: `${Math.round(systemMetrics.cpu)}% CPU`,
          badgeColor: "bg-blue-500/20 text-blue-300 border-blue-400/40 font-mono",
          action: () => handleNavClick("system"),
        },
        {
          id: "memory",
          label: "Memory Matrix",
          icon: <BrainCircuit size={16} />,
          badge: "Synced",
          badgeColor: "bg-emerald-500/25 text-emerald-300 border-emerald-500/50 font-bold",
          action: () => handleNavClick("memory"),
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
      ],
    },
    {
      label: "AUTONOMOUS EXPANSIONS",
      items: [
        {
          id: "vision",
          label: "Desktop Vision",
          icon: <Eye size={16} className="text-emerald-400" />,
          badge: "Active",
          badgeColor: "bg-emerald-500/25 text-emerald-300 border-emerald-500/50 font-bold",
          locked: false,
          action: () => handleNavClick("vision"),
        },
        {
          id: "agent",
          label: "Autonomous Agent",
          icon: <Terminal size={16} className="text-rose-400" />,
          badge: "Mission Control",
          badgeColor: "bg-rose-500/25 text-rose-300 border-rose-500/50 font-bold",
          locked: false,
          action: () => handleNavClick("agent"),
        },
      ],
    },
  ];

  return (
    <aside
      className={`relative h-full flex flex-col bg-gradient-to-b from-[#050C1B]/98 via-[#07132B]/95 to-[#030612]/98 backdrop-blur-2xl border border-cyan-500/30 text-slate-300 transition-all duration-300 z-40 select-none shadow-[0_8px_35px_rgba(0,0,0,0.8)] rounded-3xl overflow-hidden ${
        className ? className : isCollapsed ? "w-[76px]" : "w-[280px]"
      }`}
    >
      {/* Background Cybernetic Glow & Holographic Scanning Laser */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(6,182,212,0.15),transparent_70%)] pointer-events-none" />
      <div className="absolute top-0 bottom-0 right-0 w-[1px] bg-gradient-to-b from-cyan-400/60 via-blue-500/30 to-transparent pointer-events-none shadow-[0_0_12px_rgba(6,182,212,0.6)]" />

      {/* Floating Seam Collapse / Expand Toggle Button */}
      {collapsible && (
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3.5 top-8 z-50 w-7 h-7 rounded-full bg-[#07132B] hover:bg-cyan-500/30 border border-cyan-400/60 text-cyan-300 hover:text-white flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.6)] transition-all cursor-pointer hover:scale-110 active:scale-95"
          title={isCollapsed ? "Expand Sidebar HUD" : "Collapse Sidebar to Mini Rail"}
        >
          {isCollapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
        </button>
      )}

      {/* 1. TOP HEADER - STARK ARC REACTOR BRANDING */}
      <div
        className={`relative h-20 flex items-center border-b border-cyan-500/20 bg-gradient-to-r from-[#050E22]/90 to-[#081530]/90 px-4 shrink-0 ${
          isCollapsed ? "justify-center px-2" : "justify-between"
        }`}
      >
        <div className={`flex items-center min-w-0 ${isCollapsed ? "justify-center w-full" : "gap-3"}`}>
          {/* 3D Arc Reactor Mini Brand Icon with Rotating Neon Rim */}
          <div
            onClick={() => handleNavClick("dashboard")}
            className="relative w-11 h-11 flex items-center justify-center shrink-0 cursor-pointer group"
            title="JARVIS Mark IX Arc Core - Dashboard"
          >
            <div className="absolute inset-0 rounded-2xl border border-cyan-400/50 bg-gradient-to-br from-cyan-950/80 to-blue-950/70 shadow-[0_0_18px_rgba(6,182,212,0.5)_inset] group-hover:border-cyan-300 transition-colors animate-pulse-glow" />
            <Image
              src="/icon-192.png"
              alt="JARVIS Arc Core"
              width={34}
              height={34}
              priority
              className="relative w-8 h-8 rounded-full object-contain drop-shadow-[0_0_12px_rgba(0,240,255,0.9)] group-hover:scale-115 transition-transform duration-300"
            />
          </div>

          {!isCollapsed && (
            <div className="flex flex-col min-w-0 animate-in fade-in duration-200">
              <div className="flex items-center gap-1.5">
                <span className="font-hud text-transparent bg-clip-text bg-gradient-to-r from-cyan-100 via-white to-blue-200 font-black text-[18px] tracking-[0.22em] drop-shadow-[0_0_10px_rgba(6,182,212,0.7)] leading-none">
                  J.A.R.V.I.S
                </span>
                <span className="text-[9px] font-mono font-black px-1.5 py-0.2 rounded bg-gradient-to-r from-cyan-500/30 to-blue-600/30 text-cyan-200 border border-cyan-400/50 shadow-sm">
                  IX
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-[9px] font-mono text-slate-400 mt-1">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400 shadow-[0_0_6px_#10b981]" />
                </span>
                <span className="text-emerald-400 font-extrabold tracking-wider">ONLINE</span>
                <span className="text-slate-600">•</span>
                <span className="text-cyan-400/90 font-medium">NEURAL AI OS</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2. CREATOR PROFILE DOSSIER CARD */}
      <div className="p-3 border-b border-cyan-500/20 bg-gradient-to-b from-[#071533]/60 to-transparent">
        <button
          onClick={onOpenDossier}
          className={`w-full text-left rounded-2xl border transition-all duration-300 cursor-pointer group flex items-center relative overflow-hidden ${
            isCollapsed
              ? "justify-center p-2 bg-[#09152C]/90 border-cyan-500/40 hover:border-cyan-400 hover:shadow-[0_0_18px_rgba(6,182,212,0.35)]"
              : "p-2.5 bg-gradient-to-r from-[#091733] to-[#0D2146] border-cyan-500/35 hover:border-cyan-400/90 hover:shadow-[0_0_22px_rgba(6,182,212,0.3)]"
          }`}
          title="Master Creator Dossier (Muhammad Akmal) - Open Vault"
        >
          <div className="relative shrink-0">
            <div className="w-10 h-10 rounded-xl p-[1.5px] bg-gradient-to-tr from-cyan-400 via-blue-500 to-indigo-500 shadow-[0_0_15px_rgba(6,182,212,0.5)] overflow-hidden">
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
                className="w-full h-full object-cover rounded-[9px]"
              />
            </div>
            <div
              className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center border-2 border-[#050C1B] ${
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
                <span className="text-[9px] font-mono uppercase tracking-widest font-black text-cyan-400">
                  CREATOR
                </span>
                <span
                  className={`text-[8px] font-mono px-1.5 py-0.2 rounded font-extrabold border ${
                    isVaultUnlocked
                      ? "bg-emerald-500/25 text-emerald-300 border-emerald-500/50 shadow-sm"
                      : "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                  }`}
                >
                  {isVaultUnlocked ? "ROOT ACCESS" : "SYNCED"}
                </span>
              </div>
              <span className="text-white font-extrabold text-xs truncate group-hover:text-cyan-200 transition-colors">
                {dossier?.personal?.preferred_name || dossier?.personal?.name || "Muhammad Akmal"}
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Activity size={10} className="text-emerald-400 animate-pulse" />
                <span className="text-[10px] text-slate-400 font-mono truncate">
                  Biometrics Clearance OK
                </span>
              </div>
            </div>
          )}
        </button>
      </div>

      {/* 2B. WINDOWS DESKTOP OS INTEGRATION CARD */}
      {!isCollapsed && (
        <div className="mx-3 mt-2 mb-1 p-2.5 rounded-2xl bg-gradient-to-b from-[#081530]/90 to-[#040B1A]/90 border border-cyan-500/25 text-xs font-mono shadow-sm">
          <div className="flex items-center justify-between text-[9px] uppercase tracking-wider text-cyan-400 font-bold mb-1.5">
            <span className="flex items-center gap-1">
              <Sparkles size={10} className="text-cyan-400 animate-spin" />
              <span>WINDOWS SYSTEM</span>
            </span>
            <span className="text-[8px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-200 border border-cyan-500/40 font-bold">
              DESKTOP APP
            </span>
          </div>

          <div className="flex items-center justify-between gap-2 py-0.5">
            <span className="text-slate-300 text-[10px]">Start on Windows Boot</span>
            <button
              type="button"
              onClick={onToggleAutostart}
              className={`px-2 py-0.5 rounded text-[9px] font-bold border transition-all cursor-pointer ${
                autostartEnabled
                  ? "bg-emerald-500/25 border-emerald-400 text-emerald-300 shadow-[0_0_10px_rgba(16,185,129,0.35)]"
                  : "bg-slate-800 border-slate-600 text-slate-400 hover:text-white"
              }`}
              title="Toggle Start JARVIS on Windows Boot"
            >
              {autostartEnabled ? "ENABLED" : "DISABLED"}
            </button>
          </div>

          <div className="flex items-center justify-between text-[9px] text-slate-400 pt-1.5 border-t border-cyan-500/15 mt-1.5">
            <span>Global Summon</span>
            <span className="text-cyan-300 font-extrabold px-1.5 py-0.2 rounded bg-cyan-950/60 border border-cyan-500/30">
              Ctrl + Space
            </span>
          </div>
        </div>
      )}

      {/* 2C. LIVE MINI TELEMETRY BARS */}
      {!isCollapsed && (
        <div className="mx-3 mt-1 mb-1 p-2 rounded-xl bg-[#061024]/60 border border-cyan-500/15 flex flex-col gap-1.5 text-[10px] font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1">
              <Cpu size={11} className="text-cyan-400" />
              <span>CPU LOAD</span>
            </span>
            <span className="font-bold text-white">{Math.round(systemMetrics.cpu)}%</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-slate-800/80 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                systemMetrics.cpu > 80 ? "bg-rose-500" : systemMetrics.cpu > 60 ? "bg-amber-400" : "bg-cyan-400"
              }`}
              style={{ width: `${Math.min(100, Math.max(5, systemMetrics.cpu))}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-slate-400 mt-0.5">
            <span className="flex items-center gap-1">
              <HardDrive size={11} className="text-emerald-400" />
              <span>RAM USAGE</span>
            </span>
            <span className="font-bold text-white">{Math.round(systemMetrics.ram)}%</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-slate-800/80 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                systemMetrics.ram > 85 ? "bg-rose-500" : systemMetrics.ram > 70 ? "bg-amber-400" : "bg-emerald-400"
              }`}
              style={{ width: `${Math.min(100, Math.max(5, systemMetrics.ram))}%` }}
            />
          </div>
        </div>
      )}

      {/* 3. NAVIGATION MODULES LIST */}
      <nav className="flex-1 overflow-y-auto px-2.5 py-2 flex flex-col gap-3.5 custom-scrollbar">
        {navCategories.map((cat, cIdx) => (
          <div key={cIdx} className="flex flex-col gap-1">
            {!isCollapsed && (
              <div className="flex items-center justify-between px-2 mb-1">
                <span className="text-[9px] font-mono font-black tracking-[0.22em] text-cyan-400/70 uppercase">
                  {cat.label}
                </span>
                <span className="h-px bg-cyan-500/20 flex-1 ml-2" />
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
                    className={`relative flex items-center justify-between w-full rounded-2xl transition-all duration-200 group ${
                      isCollapsed ? "px-3 py-3 justify-center" : "px-3 py-2.5"
                    } ${
                      isActive
                        ? "bg-gradient-to-r from-cyan-500/30 via-blue-600/35 to-blue-500/25 text-white border border-cyan-400/60 shadow-[0_0_22px_rgba(6,182,212,0.3)]"
                        : item.locked
                        ? "text-slate-600 hover:bg-transparent cursor-not-allowed border border-transparent"
                        : "text-slate-400 hover:text-white hover:bg-[#0E1F42]/70 hover:border-cyan-500/30 border border-transparent"
                    }`}
                    title={`${item.label} ${item.locked ? "(Pending Phase Release)" : ""}`}
                  >
                    {isActive && (
                      <span className="absolute left-0 top-2 bottom-2 w-1.5 rounded-r bg-cyan-400 shadow-[0_0_10px_#22d3ee]" />
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
                      <span className="absolute right-1.5 top-1.5 w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* 4. SLEEK MINIMAL FOOTER */}
      <div className="p-3 border-t border-cyan-500/20 bg-gradient-to-b from-[#050E22]/90 to-[#020510] flex items-center justify-between text-[10px] font-mono text-slate-500 shrink-0">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]" />
          <span className="text-slate-300 font-semibold">STARK OS • MK IX</span>
        </div>
        <span className="text-cyan-400 font-bold">Akmal Edition ✓</span>
      </div>
    </aside>
  );
}
