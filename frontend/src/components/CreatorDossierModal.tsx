"use client";

import React, { useState, useEffect } from "react";
import {
  User, ShieldCheck, RefreshCw, Code, X, ExternalLink,
  Globe, Share2, Mic, Terminal, Cpu, Radio,
  Fingerprint, Activity, CheckCircle2, Zap,
  Check, Copy, Shield, Database, Compass, Trash2,
  Lock, KeyRound, Eye, EyeOff, Camera
} from "lucide-react";

function InstagramIcon({ size = 18, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
    </svg>
  );
}

export interface SyncedRepo {
  name: string;
  description: string;
  language: string;
  stars: number;
  html_url?: string;
}

export interface CreatorDossierData {
  personal?: {
    name?: string;
    preferred_name?: string;
    title?: string;
    bio?: string;
    location?: string;
    email?: string;
    avatar_url?: string;
  };
  social_profiles?: {
    github?: string;
    github_username?: string;
    linkedin?: string;
    portfolio?: string;
    twitter?: string;
    instagram?: string;
  };
  tech_stack?: string[];
  coding_preferences?: string;
  projects?: {
    name: string;
    role: string;
    description: string;
  }[];
  online_synced_data?: {
    last_synced?: string;
    public_repos_count?: number;
    followers?: number;
    recent_repos?: SyncedRepo[];
    online_summary?: string;
  };
  ai_interaction_rules?: {
    honorific?: string;
    tone?: string;
  };
}

interface CreatorDossierModalProps {
  isOpen: boolean;
  onClose: () => void;
  dossier: CreatorDossierData | null;
  onSync: (githubUser?: string) => Promise<void>;
  isSyncing: boolean;
  onSave: (updates: Partial<CreatorDossierData>) => Promise<void>;
  showNotice: (msg: string) => void;
}

export function CreatorDossierModal({
  isOpen,
  onClose,
  dossier,
  onSync,
  isSyncing,
  onSave,
  showNotice
}: CreatorDossierModalProps) {
  // Security Lock & Authentication State
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [pinInput, setPinInput] = useState("");
  const [unlockError, setUnlockError] = useState<string | null>(null);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Active Tab in Unlocked Mode
  const [activeTab, setActiveTab] = useState<'overview' | 'repos' | 'edit'>('overview');
  
  // Edit Form States
  const [editName, setEditName] = useState(() => dossier?.personal?.name || "Muhammad Akmal");
  const [editTitle, setEditTitle] = useState(() => dossier?.personal?.title || "Full Stack Developer & AI Engineer");
  const [editLocation, setEditLocation] = useState(() => dossier?.personal?.location || "Lahore, Pakistan");
  const [editBio, setEditBio] = useState(() => dossier?.personal?.bio || "Creator and Master Architect of JARVIS AI System.");
  const [editGithub, setEditGithub] = useState(() => dossier?.social_profiles?.github_username || dossier?.social_profiles?.github || "");
  const [editLinkedin, setEditLinkedin] = useState(() => dossier?.social_profiles?.linkedin || "");
  const [editPortfolio, setEditPortfolio] = useState(() => dossier?.social_profiles?.portfolio || "");
  const [editInstagram, setEditInstagram] = useState(() => dossier?.social_profiles?.instagram || dossier?.social_profiles?.twitter || "");
  const [editAvatarUrl, setEditAvatarUrl] = useState(() => 
    dossier?.personal?.avatar_url || 
    (dossier?.social_profiles?.github_username ? `https://github.com/${dossier.social_profiles.github_username}.png` : "")
  );
  const [imageLoadFailed, setImageLoadFailed] = useState(false);
  const [editTechStack, setEditTechStack] = useState(() => Array.isArray(dossier?.tech_stack) ? dossier.tech_stack.join(", ") : "");
  const [isSaving, setIsSaving] = useState(false);
  const [copiedLink, setCopiedLink] = useState<string | null>(null);

  // Voice Biometrics State
  const [voiceStatus, setVoiceStatus] = useState<{ enrolled: boolean; samples_count: number } | null>(null);
  const [isEnrollingVoice, setIsEnrollingVoice] = useState(false);
  const [isResettingVoice, setIsResettingVoice] = useState(false);

  // Auto-lock whenever modal is closed or unmounted
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
  if (prevIsOpen !== isOpen) {
    setPrevIsOpen(isOpen);
    if (!isOpen) {
      setIsUnlocked(false);
      setPinInput("");
      setUnlockError(null);
      setIsAuthorizing(false);
    }
  }

  // Fetch voice status when opened & unlocked
  useEffect(() => {
    let ignore = false;
    if (isOpen && isUnlocked) {
      fetch("http://127.0.0.1:8000/api/voice/biometrics/status")
        .then((res) => res.json())
        .then((data) => {
          if (!ignore && data?.biometrics) {
            setVoiceStatus(data.biometrics);
          }
        })
        .catch(() => {});
    }
    return () => {
      ignore = true;
    };
  }, [isOpen, isUnlocked]);

  // Auto-lock and close modal
  const handleClose = () => {
    setIsUnlocked(false);
    setPinInput("");
    setUnlockError(null);
    onClose();
  };

  // Authenticate PIN / Password
  const handleUnlockDossier = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!pinInput.trim()) {
      setUnlockError("Please enter your security PIN or password.");
      return;
    }
    setUnlockError(null);
    setIsAuthorizing(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/vault/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin: pinInput.trim() })
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        setIsUnlocked(true);
        setUnlockError(null);
        showNotice("Identity verified! Welcome, Akmal bhai.");
      } else {
        setUnlockError(data.detail || "Access Denied: Incorrect Security PIN.");
      }
    } catch {
      setUnlockError("Connection error with JARVIS Security Subsystem.");
    } finally {
      setIsAuthorizing(false);
    }
  };

  const populateEditFields = () => {
    setEditName(dossier?.personal?.name || "Muhammad Akmal");
    setEditTitle(dossier?.personal?.title || "Full Stack Developer & AI Engineer");
    setEditLocation(dossier?.personal?.location || "Lahore, Pakistan");
    setEditBio(dossier?.personal?.bio || "Creator and Master Architect of JARVIS AI System.");
    setEditGithub(dossier?.social_profiles?.github_username || dossier?.social_profiles?.github || "");
    setEditLinkedin(dossier?.social_profiles?.linkedin || "");
    setEditPortfolio(dossier?.social_profiles?.portfolio || "");
    setEditInstagram(dossier?.social_profiles?.instagram || dossier?.social_profiles?.twitter || "");
    setEditAvatarUrl(dossier?.personal?.avatar_url || (dossier?.social_profiles?.github_username ? `https://github.com/${dossier.social_profiles.github_username}.png` : ""));
    setImageLoadFailed(false);
    setEditTechStack(Array.isArray(dossier?.tech_stack) ? dossier.tech_stack.join(", ") : "");
  };

  const handleTabSwitch = (tab: 'overview' | 'repos' | 'edit') => {
    if (tab === 'edit') {
      populateEditFields();
    }
    setActiveTab(tab);
  };

  const handleCopy = (text: string, label: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedLink(label);
    showNotice(`${label} copied to clipboard!`);
    setTimeout(() => setCopiedLink(null), 2500);
  };

  const handleEnrollVoice = async () => {
    setIsEnrollingVoice(true);
    showNotice("Listening... Please speak clearly into your mic for 4-5 seconds!");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/voice/biometrics/enroll", {
        method: "POST"
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showNotice(`Voiceprint enrolled successfully! (Sample #${data.samples_count})`);
        const statusRes = await fetch("http://127.0.0.1:8000/api/voice/biometrics/status");
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setVoiceStatus(statusData.biometrics);
        }
      } else {
        showNotice(data.detail || data.error || "Enrollment failed. Please speak louder into mic.");
      }
    } catch {
      showNotice("Network error during voice enrollment.");
    } finally {
      setIsEnrollingVoice(false);
    }
  };

  const handleResetVoice = async () => {
    if (!window.confirm("Akmal bhai, kya aap waqai enrolled voiceprint delete karna chahte hain? Iske baad JARVIS voice command kisi b shakhs se accept karega jab tak aap dubara voice enroll na karein.")) {
      return;
    }
    setIsResettingVoice(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/voice/biometrics/reset", {
        method: "POST"
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        showNotice("Voiceprint successfully deleted! Biometric lock reset.");
        setVoiceStatus({ enrolled: false, samples_count: 0 });
      } else {
        showNotice("Failed to delete voiceprint.");
      }
    } catch {
      showNotice("Network error deleting voiceprint.");
    } finally {
      setIsResettingVoice(false);
    }
  };

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsSaving(true);
    try {
      const techList = editTechStack.split(",").map((s) => s.trim()).filter(Boolean);
      const cleanGh = editGithub.trim().replace("https://github.com/", "").replace("/", "");
      await onSave({
        personal: {
          name: editName.trim(),
          preferred_name: "Akmal bhai",
          title: editTitle.trim(),
          bio: editBio.trim(),
          location: editLocation.trim(),
          avatar_url: editAvatarUrl.trim(),
        },
        social_profiles: {
          github: cleanGh ? (cleanGh.startsWith("http") ? cleanGh : `https://github.com/${cleanGh}`) : "",
          github_username: cleanGh,
          linkedin: editLinkedin.trim(),
          portfolio: editPortfolio.trim(),
          instagram: editInstagram.trim(),
          twitter: editInstagram.trim(),
        },
        tech_stack: techList,
      });
      setActiveTab('overview');
    } catch {
      showNotice("Failed to save dossier.");
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const currentRepos = dossier?.online_synced_data?.recent_repos || [];
  const publicReposCount = dossier?.online_synced_data?.public_repos_count ?? currentRepos.length;
  const followersCount = dossier?.online_synced_data?.followers ?? 0;
  const techStackList = dossier?.tech_stack && dossier.tech_stack.length > 0
    ? dossier.tech_stack
    : ["Python", "FastAPI", "Next.js", "React", "TypeScript", "Tailwind CSS", "PyTorch", "AI/LLMs", "Node.js", "Git"];

  const activeAvatar = dossier?.personal?.avatar_url || editAvatarUrl || (dossier?.social_profiles?.github_username ? `https://github.com/${dossier.social_profiles.github_username}.png` : "");

  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-2xl flex items-center justify-center p-3 sm:p-5 overflow-hidden animate-in fade-in duration-200">
      
      {/* Sci-Fi HUD Container */}
      <div className="relative w-full max-w-5xl bg-[#040814] border border-cyan-500/40 rounded-2xl shadow-[0_0_80px_rgba(6,182,212,0.25)] flex flex-col max-h-[92vh] overflow-hidden text-slate-300">
        
        {/* Holographic Top Laser Line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_#38bdf8]" />
        
        {/* Ambient Glow Orbs */}
        <div className="absolute -top-32 -left-32 w-80 h-80 bg-cyan-500/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />

        {/* HUD Top Bar */}
        <div className="px-5 pt-4 pb-3 border-b border-[#132238] bg-gradient-to-b from-[#081122]/90 to-transparent flex flex-wrap items-center justify-between gap-3 relative z-10 shrink-0">
          
          {/* Left Title */}
          <div className="flex items-center gap-3.5">
            <div className={`relative w-11 h-11 rounded-xl flex items-center justify-center shrink-0 border transition-colors shadow-lg ${
              isUnlocked 
                ? 'bg-gradient-to-br from-cyan-950/80 to-[#0A1528] border-cyan-400/50 text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.3)]'
                : 'bg-gradient-to-br from-amber-950/80 to-[#120D04] border-amber-500/50 text-amber-300 shadow-[0_0_20px_rgba(245,158,11,0.25)]'
            }`}>
              {isUnlocked ? <Fingerprint size={22} /> : <Lock size={22} />}
              <div className={`absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2 border-[#040814] ${
                isUnlocked ? 'bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]' : 'bg-amber-400 animate-ping'
              }`} />
            </div>

            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-cyan-400/80 font-bold flex items-center gap-1.5">
                  <Cpu size={12} /> JARVIS AI CORE // DOSSIER PROTOCOL v4.5
                </span>
                <span className={`text-[9px] border px-2 py-0.2 rounded-full font-mono flex items-center gap-1 font-bold ${
                  isUnlocked 
                    ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40' 
                    : 'bg-amber-950/80 text-amber-300 border-amber-500/40'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${isUnlocked ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                  {isUnlocked ? 'AUTHENTICATED ROOT ACCESS' : 'ENCRYPTED LOCK GATE ACTIVE'}
                </span>
              </div>
              <h2 className="text-white font-extrabold text-lg sm:text-xl tracking-wider font-sans flex items-center gap-2 drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]">
                CREATOR DIGITAL DOSSIER
              </h2>
            </div>
          </div>

          {/* Right Action Suite */}
          <div className="flex items-center gap-2 ml-auto">
            {isUnlocked && (
              <>
                <button
                  onClick={() => onSync(dossier?.social_profiles?.github_username || editGithub)}
                  disabled={isSyncing}
                  className="text-xs bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-400/50 text-cyan-200 px-3.5 py-1.5 rounded-xl transition-all font-semibold flex items-center gap-1.5 cursor-pointer shadow-md shadow-cyan-500/10 hover:shadow-cyan-500/25 disabled:opacity-50"
                  title="Scans public GitHub repos, followers, and bio live"
                >
                  <RefreshCw size={13} className={isSyncing ? "animate-spin text-cyan-300" : ""} />
                  <span>{isSyncing ? "Syncing..." : "⚡ Sync Footprint"}</span>
                </button>

                <button
                  onClick={() => {
                    setIsUnlocked(false);
                    setPinInput("");
                    showNotice("Creator Dossier locked.");
                  }}
                  className="text-xs bg-amber-950/40 hover:bg-amber-900/60 border border-amber-500/40 hover:border-amber-400 text-amber-300 px-3 py-1.5 rounded-xl transition-all font-semibold flex items-center gap-1.5 cursor-pointer"
                  title="Lock the dossier immediately"
                >
                  <Lock size={13} />
                  <span>Lock</span>
                </button>
              </>
            )}

            <button
              onClick={handleClose}
              className="w-8 h-8 rounded-xl bg-[#0C1527] hover:bg-red-950/60 border border-[#1A2D48] hover:border-red-500/50 text-slate-400 hover:text-red-300 flex items-center justify-center transition-colors cursor-pointer"
              title="Close Dossier (Auto-locks immediately)"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* SCREEN 1: LOCKED SECURITY PIN / PASSWORD GATE */}
        {!isUnlocked ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 py-14 gap-6 relative z-10 text-center animate-in fade-in zoom-in-95 duration-200">
            
            {/* Glowing Lock Icon Emblem */}
            <div className="relative">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-900/40 via-cyan-900/30 to-[#030712] border border-cyan-400/50 flex items-center justify-center text-cyan-300 shadow-[0_0_50px_rgba(6,182,212,0.35)]">
                <Lock size={36} className="drop-shadow-[0_0_12px_#38bdf8]" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-amber-500 border-2 border-[#040814] flex items-center justify-center text-slate-950 shadow-md">
                <KeyRound size={12} strokeWidth={3} />
              </div>
            </div>

            {/* Security Notice */}
            <div className="max-w-md flex flex-col gap-1.5">
              <span className="text-[11px] font-mono uppercase tracking-[0.3em] text-cyan-400 font-bold">
                HIGH SECURITY CLEARANCE REQUIRED
              </span>
              <h3 className="text-white font-extrabold text-xl tracking-wide">
                Restricted to Muhammad Akmal
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed mt-1">
                This dossier contains proprietary system architecture, personal online footprint, and AI consciousness binding. Enter your Security PIN to decrypt access.
              </p>
            </div>

            {/* PIN Entry Form */}
            <form onSubmit={handleUnlockDossier} className="w-full max-w-sm flex flex-col items-center gap-3.5">
              <div className="relative w-full">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••"
                  value={pinInput}
                  onChange={(e) => {
                    setPinInput(e.target.value);
                    setUnlockError(null);
                  }}
                  autoFocus
                  maxLength={16}
                  className="w-full bg-[#030712] border border-cyan-500/50 focus:border-cyan-400 rounded-xl px-4 py-3 text-white font-mono text-center tracking-[0.45em] text-xl outline-none shadow-[0_0_20px_rgba(6,182,212,0.15)_inset] focus:shadow-[0_0_30px_rgba(6,182,212,0.3)_inset] transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-cyan-400 transition-colors p-1 cursor-pointer"
                  title={showPassword ? "Hide PIN" : "Show PIN"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {unlockError && (
                <div className="w-full text-xs text-red-400 font-mono bg-red-950/60 border border-red-500/40 px-3 py-2 rounded-xl text-center shadow-lg shadow-red-950/30">
                  ⚠️ {unlockError}
                </div>
              )}

              <button
                type="submit"
                disabled={isAuthorizing || !pinInput.trim()}
                className="w-full py-3 rounded-xl font-bold text-xs bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/25 cursor-pointer disabled:opacity-50"
              >
                <KeyRound size={15} />
                <span>{isAuthorizing ? "Authenticating Matrix..." : "Authorize & Decrypt Dossier"}</span>
              </button>

              <div className="flex items-center justify-between w-full text-[10px] text-slate-500 font-mono px-1">
                <span>Default Security PIN: <strong className="text-slate-400">****</strong></span>
                <span className="text-emerald-400 font-bold">Auto-locks on close</span>
              </div>
            </form>

          </div>
        ) : (
          /* SCREEN 2: UNLOCKED FUTURISTIC COMMAND CENTER */
          <>
            {/* Futuristic HUD Navigation Tabs */}
            <div className="px-5 pt-2 pb-2 bg-[#060D1A]/70 border-b border-[#121F33] flex items-center justify-between gap-2 shrink-0 overflow-x-auto custom-scrollbar">
              <div className="flex items-center gap-1.5 sm:gap-2">
                {[
                  { id: 'overview' as const, label: 'Neural Identity & Voiceprint', icon: <ShieldCheck size={14} /> },
                  { id: 'repos' as const, label: `Repositories & Cyber Footprint (${publicReposCount})`, icon: <Code size={14} /> },
                  { id: 'edit' as const, label: 'Override & Edit Parameters', icon: <Terminal size={14} /> },
                ].map((tab) => {
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => handleTabSwitch(tab.id)}
                      className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
                        isActive
                          ? "bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-400/50 text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,0.2)] font-bold"
                          : "text-slate-400 hover:text-slate-200 hover:bg-[#0B1527] border border-transparent"
                      }`}
                    >
                      <span className={isActive ? "text-cyan-400" : "text-slate-500"}>{tab.icon}</span>
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>

              <div className="hidden md:flex items-center gap-2 font-mono text-[10px] text-slate-500 shrink-0">
                <Radio size={12} className="text-emerald-400 animate-pulse" />
                <span>NEURAL LINK: <span className="text-emerald-400 font-bold">100% SYNCHRONIZED</span></span>
              </div>
            </div>

            {/* Modal Scrollable Canvas */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-5 relative z-10 flex flex-col gap-5">
              
              {/* TAB 1: OVERVIEW & BIOMETRICS */}
              {activeTab === 'overview' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 animate-in fade-in duration-200">
                  
                  {/* LEFT COLUMN: Holographic ID & Biometric Radar (5 Cols) */}
                  <div className="lg:col-span-5 flex flex-col gap-4">
                    
                    {/* Holographic Master Identity Card */}
                    <div className="bg-gradient-to-b from-[#081226] via-[#050B18] to-[#040814] border border-cyan-500/40 rounded-2xl p-5 shadow-[0_0_30px_rgba(6,182,212,0.12)] relative overflow-hidden group">
                      <div className="absolute inset-0 bg-[radial-gradient(#1E3A8A_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />
                      
                      {/* Avatar & Header */}
                      <div className="flex items-start gap-4 relative z-10">
                        <div className="relative shrink-0 group/avatar">
                          <div className="w-18 h-18 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 p-[2px] shadow-[0_0_25px_rgba(6,182,212,0.35)] relative overflow-hidden">
                            <div className="w-full h-full bg-[#060D1E] rounded-2xl flex flex-col items-center justify-center relative overflow-hidden">
                              {activeAvatar && !imageLoadFailed ? (
                                /* eslint-disable-next-line @next/next/no-img-element */
                                <img
                                  src={activeAvatar}
                                  alt={dossier?.personal?.name || "Muhammad Akmal"}
                                  onError={() => setImageLoadFailed(true)}
                                  className="w-full h-full object-cover rounded-2xl group-hover/avatar:scale-105 transition-transform duration-300"
                                />
                              ) : (
                                <>
                                  <span className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-br from-cyan-300 via-blue-200 to-indigo-300">
                                    MA
                                  </span>
                                  <span className="text-[8px] font-mono font-bold tracking-widest text-cyan-400/80 mt-0.5">
                                    ROOT
                                  </span>
                                </>
                              )}
                              {/* Hover overlay to change picture */}
                              <button
                                type="button"
                                onClick={() => handleTabSwitch('edit')}
                                className="absolute inset-0 bg-black/65 backdrop-blur-[2px] opacity-0 group-hover/avatar:opacity-100 flex flex-col items-center justify-center text-cyan-300 transition-opacity cursor-pointer"
                                title="Change Profile Picture"
                              >
                                <Camera size={16} />
                                <span className="text-[8px] font-mono font-bold mt-0.5 tracking-wider">CHANGE</span>
                              </button>
                            </div>
                          </div>
                          <span className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-[#040814] shadow-[0_0_8px_#10b981]" title="Creator Online" />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <h3 className="text-white font-extrabold text-base tracking-wide truncate">
                              {dossier?.personal?.name || "Muhammad Akmal"}
                            </h3>
                            <span className="text-[10px] bg-cyan-950/80 text-cyan-300 border border-cyan-500/40 px-2 py-0.2 rounded-full font-mono font-bold">
                              {dossier?.personal?.preferred_name || "Akmal bhai"}
                            </span>
                          </div>
                          
                          <p className="text-xs text-cyan-300/90 font-medium mt-1 leading-snug">
                            {dossier?.personal?.title || "Full Stack Developer & AI Engineer"}
                          </p>

                          <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-mono mt-1.5">
                            <Compass size={12} className="text-cyan-400 shrink-0" />
                            <span className="truncate">{dossier?.personal?.location || "Lahore, Pakistan"}</span>
                          </div>
                        </div>
                      </div>

                      {/* Creator Bio Box */}
                      <div className="mt-4 pt-3 border-t border-[#132238] relative z-10">
                        <div className="text-xs text-slate-300 leading-relaxed italic bg-black/40 border border-cyan-500/20 p-3 rounded-xl relative">
                          <span className="text-cyan-400 font-bold not-italic font-mono text-[10px] uppercase block mb-1">
                            Creator Directive:
                          </span>
                          &ldquo;{dossier?.personal?.bio || "Creator and Master Architect of JARVIS AI System."}&rdquo;
                        </div>
                      </div>

                      {/* Live Footprint Metric Badges */}
                      <div className="grid grid-cols-2 gap-2.5 mt-4 relative z-10">
                        <div className="bg-[#050C1C] border border-[#14233D] hover:border-cyan-500/40 p-3 rounded-xl flex items-center gap-3 transition-colors">
                          <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                            <Database size={16} />
                          </div>
                          <div>
                            <div className="text-lg font-extrabold text-white font-mono leading-none">
                              {publicReposCount}
                            </div>
                            <div className="text-[9px] text-slate-400 uppercase font-mono tracking-wider mt-0.5">
                              Public Repos
                            </div>
                          </div>
                        </div>

                        <div className="bg-[#050C1C] border border-[#14233D] hover:border-purple-500/40 p-3 rounded-xl flex items-center gap-3 transition-colors">
                          <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 shrink-0">
                            <Activity size={16} />
                          </div>
                          <div>
                            <div className="text-lg font-extrabold text-purple-300 font-mono leading-none">
                              {followersCount}
                            </div>
                            <div className="text-[9px] text-slate-400 uppercase font-mono tracking-wider mt-0.5">
                              Followers
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Voice Biometrics Radar Station */}
                    <div className="bg-[#050C1C] border border-cyan-500/30 rounded-2xl p-4 shadow-lg flex flex-col gap-3 relative overflow-hidden">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
                            voiceStatus?.enrolled 
                              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.3)]' 
                              : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                          }`}>
                            <Mic size={16} />
                          </div>
                          <div>
                            <div className="text-xs font-bold text-white flex items-center gap-1.5">
                              <span>Voice Biometrics Shield</span>
                            </div>
                            <div className="text-[10px] font-mono text-slate-400">
                              Speaker Verification Engine
                            </div>
                          </div>
                        </div>

                        <span className={`text-[9px] font-mono uppercase font-bold px-2 py-0.5 rounded-full border ${
                          voiceStatus?.enrolled 
                            ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40' 
                            : 'bg-amber-950/80 text-amber-300 border-amber-500/40'
                        }`}>
                          {voiceStatus?.enrolled ? `Enrolled (${voiceStatus.samples_count})` : 'Unregistered'}
                        </span>
                      </div>

                      {/* Equalizer Frequency Simulation */}
                      <div className="bg-black/50 border border-slate-800/80 rounded-xl p-3 flex items-center justify-between gap-1 h-14">
                        {[18, 35, 55, 78, 92, 60, 45, 80, 70, 50, 65, 30, 20].map((h, i) => (
                          <div
                            key={i}
                            className={`w-1.5 rounded-full transition-all duration-300 ${
                              isEnrollingVoice 
                                ? 'bg-gradient-to-t from-red-500 to-amber-400 animate-pulse'
                                : voiceStatus?.enrolled 
                                  ? 'bg-gradient-to-t from-cyan-600 to-emerald-400 opacity-80' 
                                  : 'bg-slate-700 opacity-40'
                            }`}
                            style={{ height: isEnrollingVoice ? `${Math.max(20, (h * 1.2) % 100)}%` : `${h}%` }}
                          />
                        ))}
                      </div>

                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        {voiceStatus?.enrolled
                          ? "Acoustic 48-dimensional spectral vector active. Commands from unrecognized speakers will be rejected automatically."
                          : "Record your vocal signature so JARVIS will recognize your unique voice and restrict commands to Akmal bhai only."}
                      </p>

                      {voiceStatus?.enrolled ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={handleEnrollVoice}
                            disabled={isEnrollingVoice || isResettingVoice}
                            className="flex-1 py-2 px-3 rounded-xl font-bold text-xs bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 transition-all flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/20 cursor-pointer disabled:opacity-50"
                          >
                            <Mic size={14} className={isEnrollingVoice ? "animate-pulse text-red-700" : ""} />
                            <span>{isEnrollingVoice ? "Listening (4s)..." : "Add Sample"}</span>
                          </button>

                          <button
                            onClick={handleResetVoice}
                            disabled={isResettingVoice || isEnrollingVoice}
                            className="py-2 px-3 rounded-xl font-bold text-xs bg-red-950/50 hover:bg-red-900/60 border border-red-500/50 hover:border-red-400 text-red-300 transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-md shadow-red-950/30 disabled:opacity-50"
                            title="Delete stored voiceprint and reset biometric lock"
                          >
                            <Trash2 size={13} />
                            <span>{isResettingVoice ? "Deleting..." : "Delete Voiceprint"}</span>
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={handleEnrollVoice}
                          disabled={isEnrollingVoice}
                          className="w-full py-2 px-3 rounded-xl font-bold text-xs bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 transition-all flex items-center justify-center gap-2 shadow-md shadow-cyan-500/20 cursor-pointer disabled:opacity-50"
                        >
                          <Mic size={14} className={isEnrollingVoice ? "animate-pulse text-red-700" : ""} />
                          <span>{isEnrollingVoice ? "Listening to your voice (4s)..." : "Enroll Akmal bhai's Voiceprint"}</span>
                        </button>
                      )}
                    </div>

                  </div>

                  {/* RIGHT COLUMN: Connected Satellites, Arsenal & AI Directive (7 Cols) */}
                  <div className="lg:col-span-7 flex flex-col gap-4">
                    
                    {/* Connected Satellites (Social Portals) */}
                    <div className="bg-[#050C1C] border border-[#14233D] rounded-2xl p-4 shadow-md flex flex-col gap-3">
                      <div className="flex items-center justify-between border-b border-[#121F33] pb-2.5">
                        <span className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                          <Share2 size={14} className="text-cyan-400" />
                          Connected Satellite Channels
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          Click to open profile or copy link
                        </span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        
                        {/* GitHub Portal */}
                        <div className="bg-[#071022] border border-[#162744] hover:border-cyan-400/60 p-3 rounded-xl flex items-center justify-between group transition-all shadow-sm">
                          <div 
                            onClick={() => {
                              const url = dossier?.social_profiles?.github || (editGithub ? `https://github.com/${editGithub}` : "https://github.com");
                              window.open(url, "_blank");
                            }}
                            className="flex items-center gap-3 min-w-0 cursor-pointer flex-1"
                          >
                            <div className="w-9 h-9 rounded-lg bg-slate-800 group-hover:bg-cyan-500/20 text-white group-hover:text-cyan-300 flex items-center justify-center shrink-0 transition-colors">
                              <Code size={18} />
                            </div>
                            <div className="min-w-0">
                              <div className="text-xs font-bold text-white group-hover:text-cyan-300 transition-colors flex items-center gap-1.5">
                                <span>GitHub</span>
                                <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                              <div className="text-[10px] text-slate-400 font-mono truncate">
                                {dossier?.social_profiles?.github_username ? `@${dossier.social_profiles.github_username}` : "Connected"}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleCopy(dossier?.social_profiles?.github || `https://github.com/${editGithub}`, 'GitHub')}
                            className="p-1.5 text-slate-500 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
                            title="Copy GitHub link"
                          >
                            {copiedLink === 'GitHub' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                          </button>
                        </div>

                        {/* LinkedIn Portal */}
                        <div className="bg-[#071022] border border-[#162744] hover:border-blue-400/60 p-3 rounded-xl flex items-center justify-between group transition-all shadow-sm">
                          <div 
                            onClick={() => {
                              const url = dossier?.social_profiles?.linkedin || editLinkedin;
                              if (url) window.open(url.startsWith('http') ? url : `https://${url}`, "_blank");
                              else handleTabSwitch('edit');
                            }}
                            className="flex items-center gap-3 min-w-0 cursor-pointer flex-1"
                          >
                            <div className="w-9 h-9 rounded-lg bg-slate-800 group-hover:bg-blue-500/20 text-white group-hover:text-blue-300 flex items-center justify-center shrink-0 transition-colors">
                              <Share2 size={18} />
                            </div>
                            <div className="min-w-0">
                              <div className="text-xs font-bold text-white group-hover:text-blue-300 transition-colors flex items-center gap-1.5">
                                <span>LinkedIn</span>
                                <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                              <div className="text-[10px] text-slate-400 font-mono truncate">
                                {dossier?.social_profiles?.linkedin ? "Profile Linked" : "Add Profile Link"}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleCopy(dossier?.social_profiles?.linkedin || "", 'LinkedIn')}
                            className="p-1.5 text-slate-500 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
                            title="Copy LinkedIn link"
                          >
                            {copiedLink === 'LinkedIn' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                          </button>
                        </div>

                        {/* Portfolio Website Portal */}
                        <div className="bg-[#071022] border border-[#162744] hover:border-emerald-400/60 p-3 rounded-xl flex items-center justify-between group transition-all shadow-sm">
                          <div 
                            onClick={() => {
                              const url = dossier?.social_profiles?.portfolio || editPortfolio;
                              if (url) window.open(url.startsWith('http') ? url : `https://${url}`, "_blank");
                              else handleTabSwitch('edit');
                            }}
                            className="flex items-center gap-3 min-w-0 cursor-pointer flex-1"
                          >
                            <div className="w-9 h-9 rounded-lg bg-slate-800 group-hover:bg-emerald-500/20 text-white group-hover:text-emerald-300 flex items-center justify-center shrink-0 transition-colors">
                              <Globe size={18} />
                            </div>
                            <div className="min-w-0">
                              <div className="text-xs font-bold text-white group-hover:text-emerald-300 transition-colors flex items-center gap-1.5">
                                <span>Portfolio Website</span>
                                <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                              <div className="text-[10px] text-slate-400 font-mono truncate">
                                {dossier?.social_profiles?.portfolio ? "Live Showcase" : "Add Website Link"}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleCopy(dossier?.social_profiles?.portfolio || "", 'Portfolio')}
                            className="p-1.5 text-slate-500 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
                            title="Copy Portfolio link"
                          >
                            {copiedLink === 'Portfolio' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                          </button>
                        </div>

                        {/* Instagram Portal (Replaced Twitter/X) */}
                        <div className="bg-[#071022] border border-[#162744] hover:border-pink-500/60 p-3 rounded-xl flex items-center justify-between group transition-all shadow-sm">
                          <div 
                            onClick={() => {
                              const url = dossier?.social_profiles?.instagram || editInstagram;
                              if (url) window.open(url.startsWith('http') ? url : `https://${url}`, "_blank");
                              else handleTabSwitch('edit');
                            }}
                            className="flex items-center gap-3 min-w-0 cursor-pointer flex-1"
                          >
                            <div className="w-9 h-9 rounded-lg bg-slate-800 group-hover:bg-pink-500/20 text-white group-hover:text-pink-400 flex items-center justify-center shrink-0 transition-colors">
                              <InstagramIcon size={18} />
                            </div>
                            <div className="min-w-0">
                              <div className="text-xs font-bold text-white group-hover:text-pink-400 transition-colors flex items-center gap-1.5">
                                <span>Instagram</span>
                                <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                              <div className="text-[10px] text-slate-400 font-mono truncate">
                                {dossier?.social_profiles?.instagram || editInstagram ? "Profile Linked" : "Add Instagram Link"}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleCopy(dossier?.social_profiles?.instagram || editInstagram || "", 'Instagram')}
                            className="p-1.5 text-slate-500 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
                            title="Copy Instagram link"
                          >
                            {copiedLink === 'Instagram' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Mastered Tech Arsenal */}
                    <div className="bg-[#050C1C] border border-[#14233D] rounded-2xl p-4 shadow-md flex flex-col gap-3">
                      <div className="flex items-center justify-between border-b border-[#121F33] pb-2.5">
                        <span className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                          <Zap size={14} className="text-cyan-400" />
                          Engineering Arsenal & Frameworks
                        </span>
                        <span className="text-[10px] text-cyan-400 font-mono font-semibold">
                          {techStackList.length} Technologies
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {techStackList.map((tech, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-[#071122] hover:bg-cyan-950/40 border border-cyan-500/30 hover:border-cyan-400/60 text-slate-200 px-3 py-1.5 rounded-xl font-mono transition-all shadow-sm hover:scale-105 cursor-default flex items-center gap-1.5"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* AI Consciousness Directive & Rules */}
                    <div className="bg-gradient-to-r from-[#061126] via-[#050D1E] to-[#061126] border border-cyan-500/30 rounded-2xl p-4 shadow-md flex flex-col gap-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-cyan-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
                          <Shield size={14} className="text-cyan-400" />
                          AI Consciousness & Persona Binding
                        </span>
                        <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/40 uppercase">
                          Active In Memory
                        </span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs pt-1">
                        <div className="bg-black/30 border border-slate-800/80 p-2.5 rounded-xl">
                          <span className="text-[10px] text-slate-500 uppercase font-mono block">Honorific</span>
                          <span className="font-bold text-white font-mono">{dossier?.ai_interaction_rules?.honorific || "Akmal bhai"}</span>
                        </div>
                        <div className="bg-black/30 border border-slate-800/80 p-2.5 rounded-xl">
                          <span className="text-[10px] text-slate-500 uppercase font-mono block">Vocal Synthesis</span>
                          <span className="font-bold text-white font-mono truncate">Urdu Asad + US Christopher</span>
                        </div>
                        <div className="bg-black/30 border border-slate-800/80 p-2.5 rounded-xl">
                          <span className="text-[10px] text-slate-500 uppercase font-mono block">Clearance</span>
                          <span className="font-bold text-emerald-400 font-mono">Unrestricted Local Root</span>
                        </div>
                      </div>

                      <p className="text-[11px] text-slate-400 leading-relaxed pt-1">
                        JARVIS is permanently bonded to recognize Muhammad Akmal as its sovereign creator. All responses, tools, and system controls adhere directly to your engineering preferences without requesting security PINs on local desktop.
                      </p>
                    </div>

                  </div>
                </div>
              )}

              {/* TAB 2: REPOSITORIES & CYBER FOOTPRINT */}
              {activeTab === 'repos' && (
                <div className="flex flex-col gap-4 animate-in fade-in duration-200">
                  
                  {/* Telemetry Status Banner */}
                  <div className="bg-[#050C1C] border border-[#14233D] rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-md">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                        <Code size={20} />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white flex items-center gap-2">
                          Live GitHub Repositories Matrix
                        </h4>
                        <p className="text-[11px] text-slate-400 font-mono">
                          Target Account: <span className="text-cyan-300 font-bold">@{dossier?.social_profiles?.github_username || editGithub || "AkmalDoghar"}</span> • Last Synced: {dossier?.online_synced_data?.last_synced || "Not synced yet"}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() => onSync(dossier?.social_profiles?.github_username || editGithub)}
                      disabled={isSyncing}
                      className="px-4 py-2 rounded-xl text-xs font-bold bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/50 text-cyan-200 transition-all flex items-center gap-2 shrink-0 cursor-pointer shadow-md shadow-cyan-500/10"
                    >
                      <RefreshCw size={13} className={isSyncing ? "animate-spin text-cyan-300" : ""} />
                      <span>{isSyncing ? "Scanning Repositories..." : "Scan & Refresh Repos"}</span>
                    </button>
                  </div>

                  {/* Repos Grid */}
                  {currentRepos.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                      {currentRepos.map((repo, idx) => (
                        <div
                          key={idx}
                          onClick={() => repo.html_url && window.open(repo.html_url, "_blank")}
                          className="bg-gradient-to-b from-[#071022] to-[#050A16] border border-[#14233D] hover:border-cyan-400/60 p-4 rounded-2xl flex flex-col justify-between gap-3 group cursor-pointer transition-all hover:shadow-[0_0_20px_rgba(6,182,212,0.15)] hover:-translate-y-0.5"
                        >
                          <div className="flex flex-col gap-1.5">
                            <div className="flex items-start justify-between gap-2">
                              <span className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors truncate">
                                {repo.name}
                              </span>
                              <span className="text-[10px] bg-cyan-950/80 text-cyan-300 border border-cyan-800/40 px-2 py-0.5 rounded-full font-mono shrink-0">
                                {repo.language || "Code"}
                              </span>
                            </div>

                            <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                              {repo.description || "Public repository project created by Muhammad Akmal."}
                            </p>
                          </div>

                          <div className="flex items-center justify-between text-xs text-slate-500 font-mono pt-2 border-t border-[#121F33]">
                            <span className="flex items-center gap-1 text-amber-400">
                              ⭐ <span className="font-bold">{repo.stars}</span> stars
                            </span>

                            <span className="text-cyan-400 group-hover:text-cyan-300 flex items-center gap-1 font-semibold text-[11px]">
                              Launch Portal <ExternalLink size={12} />
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-[#050C1C] border border-dashed border-[#1B2F4E] rounded-2xl p-8 text-center flex flex-col items-center justify-center gap-3">
                      <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                        <Database size={24} />
                      </div>
                      <h4 className="text-sm font-bold text-white">No Public Repositories Synced Yet</h4>
                      <p className="text-xs text-slate-400 max-w-md leading-relaxed">
                        Click the scan button below to auto-fetch Muhammad Akmal&apos;s public repositories, star ratings, and primary coding languages from GitHub.
                      </p>
                      <button
                        onClick={() => onSync(dossier?.social_profiles?.github_username || editGithub)}
                        disabled={isSyncing}
                        className="px-5 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all flex items-center gap-2 cursor-pointer shadow-lg shadow-cyan-500/20"
                      >
                        <RefreshCw size={14} className={isSyncing ? "animate-spin" : ""} />
                        <span>Run Initial GitHub Scan</span>
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: OVERRIDE & EDIT PARAMETERS */}
              {activeTab === 'edit' && (
                <form onSubmit={handleSave} className="flex flex-col gap-5 animate-in fade-in duration-200">
                  
                  {/* Personal Details Section */}
                  <div className="bg-[#050C1C] border border-[#14233D] rounded-2xl p-5 flex flex-col gap-4 shadow-md">
                    <div className="flex items-center gap-2 border-b border-[#121F33] pb-2.5">
                      <User size={16} className="text-cyan-400" />
                      <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                        Personal Identity Matrix
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[11px] font-mono text-slate-400">Full Legal Name</label>
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          placeholder="e.g. Muhammad Akmal"
                          className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2 text-white text-xs font-sans outline-none transition-colors"
                          required
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-[11px] font-mono text-slate-400">Professional Engineering Title</label>
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          placeholder="e.g. Full Stack Developer & AI Engineer"
                          className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2 text-white text-xs font-sans outline-none transition-colors"
                          required
                        />
                      </div>

                      <div className="flex flex-col gap-1.5 sm:col-span-2">
                        <label className="text-[11px] font-mono text-slate-400">Geographic Location Base</label>
                        <input
                          type="text"
                          value={editLocation}
                          onChange={(e) => setEditLocation(e.target.value)}
                          placeholder="e.g. Lahore, Pakistan"
                          className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2 text-white text-xs font-sans outline-none transition-colors"
                        />
                      </div>

                      <div className="flex flex-col gap-1.5 sm:col-span-2">
                        <label className="text-[11px] font-mono text-slate-400">Master Creator Bio & Vision Statement</label>
                        <textarea
                          rows={3}
                          value={editBio}
                          onChange={(e) => setEditBio(e.target.value)}
                          placeholder="Short bio or directive injected into JARVIS AI system..."
                          className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2 text-white text-xs font-sans outline-none transition-colors resize-none"
                        />
                      </div>

                      {/* Profile Picture / Avatar Field */}
                      <div className="flex flex-col gap-2 sm:col-span-2 bg-[#030712] border border-[#192A45] p-3.5 rounded-xl">
                        <div className="flex items-center justify-between">
                          <label className="text-[11px] font-mono text-cyan-400 flex items-center gap-1.5 font-bold">
                            <Camera size={13} />
                            Creator Profile Picture URL (Avatar)
                          </label>
                          {editGithub && (
                            <button
                              type="button"
                              onClick={() => {
                                const clean = editGithub.replace(/^https?:\/\/github\.com\//, '').replace(/\/$/, '').trim();
                                if (clean) setEditAvatarUrl(`https://github.com/${clean}.png`);
                              }}
                              className="text-[10px] font-mono text-cyan-400 hover:text-cyan-300 underline underline-offset-2 flex items-center gap-1 transition-colors cursor-pointer"
                            >
                              ⚡ Auto-use GitHub Photo
                            </button>
                          )}
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-xl border border-cyan-500/40 overflow-hidden bg-[#060D1E] shrink-0 flex items-center justify-center relative shadow-[0_0_12px_rgba(6,182,212,0.2)]">
                            {editAvatarUrl ? (
                              /* eslint-disable-next-line @next/next/no-img-element */
                              <img
                                src={editAvatarUrl}
                                alt="Avatar Preview"
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  (e.currentTarget as HTMLImageElement).src = `https://github.com/${(editGithub || "AkmalDoghar").replace(/^https?:\/\/github\.com\//, '').replace(/\/$/, '')}.png`;
                                }}
                              />
                            ) : (
                              <User size={20} className="text-slate-500" />
                            )}
                          </div>
                          <div className="flex-1 flex flex-col gap-1">
                            <input
                              type="url"
                              value={editAvatarUrl}
                              onChange={(e) => setEditAvatarUrl(e.target.value)}
                              placeholder="e.g. https://github.com/AkmalDoghar.png or custom image URL"
                              className="w-full bg-[#050C1C] border border-[#192A45] focus:border-cyan-400 rounded-lg px-3 py-1.5 text-white text-xs font-mono outline-none transition-colors"
                            />
                            <span className="text-[10px] text-slate-500 font-mono">
                              Tip: By default, JARVIS uses your live GitHub picture (<span className="text-cyan-400/80">https://github.com/AkmalDoghar.png</span>).
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Digital Coordinates Section */}
                  <div className="bg-[#050C1C] border border-[#14233D] rounded-2xl p-5 flex flex-col gap-4 shadow-md">
                    <div className="flex items-center gap-2 border-b border-[#121F33] pb-2.5">
                      <Share2 size={16} className="text-cyan-400" />
                      <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                        Public Coordinates & Web Satellites
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[11px] font-mono text-slate-400">GitHub Username or Profile URL</label>
                        <input
                          type="text"
                          value={editGithub}
                          onChange={(e) => setEditGithub(e.target.value)}
                          placeholder="e.g. AkmalDoghar or https://github.com/..."
                          className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2 text-white text-xs font-mono outline-none transition-colors"
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-[11px] font-mono text-slate-400">LinkedIn Profile URL</label>
                        <input
                          type="text"
                          value={editLinkedin}
                          onChange={(e) => setEditLinkedin(e.target.value)}
                          placeholder="e.g. https://linkedin.com/in/..."
                          className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2 text-white text-xs font-mono outline-none transition-colors"
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-[11px] font-mono text-slate-400">Personal Portfolio Website URL</label>
                        <input
                          type="text"
                          value={editPortfolio}
                          onChange={(e) => setEditPortfolio(e.target.value)}
                          placeholder="e.g. https://akmalcode.vercel.app"
                          className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2 text-white text-xs font-mono outline-none transition-colors"
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-[11px] font-mono text-slate-400">Instagram Profile URL or Handle</label>
                        <input
                          type="text"
                          value={editInstagram}
                          onChange={(e) => setEditInstagram(e.target.value)}
                          placeholder="e.g. https://instagram.com/... or @handle"
                          className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2 text-white text-xs font-mono outline-none transition-colors"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Technical Arsenal Section */}
                  <div className="bg-[#050C1C] border border-[#14233D] rounded-2xl p-5 flex flex-col gap-4 shadow-md">
                    <div className="flex items-center gap-2 border-b border-[#121F33] pb-2.5">
                      <Zap size={16} className="text-cyan-400" />
                      <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                        Mastered Technologies & Frameworks
                      </span>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[11px] font-mono text-slate-400">Tech Stack (comma-separated list)</label>
                      <input
                        type="text"
                        value={editTechStack}
                        onChange={(e) => setEditTechStack(e.target.value)}
                        placeholder="Python, FastAPI, Next.js, React, TypeScript, Tailwind CSS, PyTorch, AI/LLMs"
                        className="bg-[#030712] border border-[#192A45] focus:border-cyan-400 rounded-xl px-3.5 py-2.5 text-white text-xs font-mono outline-none transition-colors"
                      />
                      <span className="text-[10px] text-slate-500 font-mono">
                        Separate items with commas. JARVIS uses this to tailor code generation to your preferred engineering toolset.
                      </span>
                    </div>
                  </div>

                  {/* Form Action Buttons */}
                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setActiveTab('overview')}
                      className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-[#0B1527] hover:bg-slate-800 text-slate-300 border border-[#1A2D48] transition-colors cursor-pointer"
                    >
                      Cancel Override
                    </button>

                    <button
                      type="submit"
                      disabled={isSaving}
                      className="px-6 py-2.5 rounded-xl text-xs font-extrabold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/25 cursor-pointer disabled:opacity-50"
                    >
                      <CheckCircle2 size={15} />
                      <span>{isSaving ? "Locking to AI Core..." : "Lock Parameters to JARVIS AI"}</span>
                    </button>
                  </div>

                </form>
              )}

            </div>

            {/* HUD Bottom Status Bar */}
            <div className="px-5 py-2.5 bg-[#030712] border-t border-[#121F33] flex items-center justify-between text-[10px] font-mono text-slate-500 shrink-0">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1.5 text-cyan-400 font-semibold">
                  <ShieldCheck size={12} /> SECURE PROTOCOL ACTIVE
                </span>
                <span className="hidden sm:inline text-slate-600">•</span>
                <span className="hidden sm:inline">AUTHENTICATED ROOT SESSION</span>
              </div>

              <div className="flex items-center gap-2">
                <span>SOVEREIGN ARCHITECT:</span>
                <span className="text-white font-bold">MUHAMMAD AKMAL</span>
              </div>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
