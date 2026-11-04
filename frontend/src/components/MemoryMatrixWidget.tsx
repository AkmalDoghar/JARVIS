"use client";

import React, { useState, useEffect, useMemo } from "react";
import { 
  BrainCircuit, Plus, Trash2, RefreshCw, Check, Sparkles, 
  Search, Copy, CheckCheck, Database, Tag, ShieldCheck, X} from "lucide-react";

export type MemoryCategory = "preference" | "project" | "instruction" | "fact";

export interface MemoryItem {
  id: number;
  category: "preference" | "project" | "instruction" | "fact" | "context";
  key: string | null;
  content: string;
  tags?: string;
  importance?: number;
  created_at: string;
  updated_at?: string;
}

export function MemoryMatrixWidget() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedId, setCopiedId] = useState<number | null>(null);
  
  // New memory form state
  const [newContent, setNewContent] = useState("");
  const [newCategory, setNewCategory] = useState<MemoryCategory>("preference");
  const [newKey, setNewKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchMemories = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/memory");
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success" && Array.isArray(data.memories)) {
          setMemories(data.memories);
        }
      }
    } catch {
      // silent fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    fetch("http://127.0.0.1:8000/api/memory")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data?.status === "success" && Array.isArray(data.memories)) {
          setMemories(data.memories);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSaveMemory = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!newContent.trim()) return;

    setSaving(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: newContent.trim(),
          category: newCategory,
          key: newKey.trim() || undefined,
        }),
      });

      if (res.ok) {
        setNewContent("");
        setNewKey("");
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 2200);
        await fetchMemories();
        setShowAddForm(false);
      }
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteMemory = async (id: number) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/memory/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setMemories((prev) => prev.filter((m) => m.id !== id));
      }
    } catch {
      // ignore
    }
  };

  const handleCopyContent = (id: number, text: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredMemories = useMemo(() => {
    return memories.filter((m) => {
      const matchesCategory = selectedFilter === "all" || m.category === selectedFilter;
      if (!matchesCategory) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const inContent = m.content.toLowerCase().includes(q);
      const inKey = m.key ? m.key.toLowerCase().includes(q) : false;
      const inCat = m.category.toLowerCase().includes(q);
      return inContent || inKey || inCat;
    });
  }, [memories, selectedFilter, searchQuery]);

  const categoryMeta = (cat: string) => {
    switch (cat) {
      case "preference":
        return {
          label: "PREFERENCE",
          icon: "🧠",
          pillClass: "bg-cyan-500/15 text-cyan-300 border-cyan-400/35 shadow-[0_0_8px_rgba(6,182,212,0.2)]",
          glow: "group-hover:border-cyan-400/50"
        };
      case "project":
        return {
          label: "PROJECT",
          icon: "🚀",
          pillClass: "bg-emerald-500/15 text-emerald-300 border-emerald-400/35 shadow-[0_0_8px_rgba(16,185,129,0.2)]",
          glow: "group-hover:border-emerald-400/50"
        };
      case "instruction":
        return {
          label: "INSTRUCTION",
          icon: "⚡",
          pillClass: "bg-amber-500/15 text-amber-300 border-amber-400/35 shadow-[0_0_8px_rgba(245,158,11,0.2)]",
          glow: "group-hover:border-amber-400/50"
        };
      case "fact":
        return {
          label: "FACT",
          icon: "💎",
          pillClass: "bg-purple-500/15 text-purple-300 border-purple-400/35 shadow-[0_0_8px_rgba(168,85,247,0.2)]",
          glow: "group-hover:border-purple-400/50"
        };
      default:
        return {
          label: "CONTEXT",
          icon: "🌐",
          pillClass: "bg-blue-500/15 text-blue-300 border-blue-400/35 shadow-[0_0_8px_rgba(59,130,246,0.2)]",
          glow: "group-hover:border-blue-400/50"
        };
    }
  };

  return (
    <div
      id="section-memory-matrix"
      className="relative rounded-3xl bg-gradient-to-b from-[#0B1124]/90 via-[#060B18]/95 to-[#03060E]/98 border border-purple-500/30 p-4 sm:p-5 shadow-[0_0_35px_rgba(168,85,247,0.12)] flex flex-col gap-3.5 overflow-hidden transition-all hover:border-purple-500/45 scroll-mt-20 group"
    >
      {/* Ambient Neon Atmosphere Orbs */}
      <div className="absolute -top-16 -right-16 w-36 h-36 bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-16 -left-16 w-36 h-36 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header: Neural Holographic Core */}
      <div className="flex items-center justify-between gap-3 relative z-10">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-2xl bg-gradient-to-br from-purple-500/25 via-purple-900/40 to-cyan-500/20 border border-purple-400/40 flex items-center justify-center text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.35)] shrink-0">
            <BrainCircuit size={20} className="text-purple-300 animate-pulse" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[#0B1124] animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[#0B1124]" />
          </div>
          
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-hud text-white font-bold text-xs sm:text-sm tracking-wider">
                SYNAPTIC MEMORY MATRIX
              </span>
              <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-200 border border-purple-400/35 font-bold tracking-widest hidden xs:inline-block">
                PHASE 6B
              </span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono text-purple-300/80 mt-0.5">
              <span className="flex items-center gap-1">
                <Database size={10} className="text-purple-400" />
                <span>SQLite Secured</span>
              </span>
              <span>•</span>
              <span className="text-emerald-400 font-semibold">100% Offline Active</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={fetchMemories}
            className="w-8 h-8 rounded-xl bg-[#081226] hover:bg-slate-800 border border-cyan-500/25 hover:border-cyan-400/50 text-slate-300 hover:text-cyan-300 flex items-center justify-center transition-all cursor-pointer shadow-sm"
            title="Resync Synaptic Memories"
          >
            <RefreshCw size={13} className={loading ? "animate-spin text-cyan-400" : ""} />
          </button>
          
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className={`flex items-center gap-1.5 text-xs font-mono font-bold px-3 py-1.5 rounded-xl border transition-all cursor-pointer shadow-md ${
              showAddForm
                ? "bg-purple-600 text-white border-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.4)]"
                : "bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 border-purple-400/40 hover:shadow-[0_0_12px_rgba(168,85,247,0.3)]"
            }`}
            title="Create an explicit synaptic memory node"
          >
            <Plus size={13} className={showAddForm ? "rotate-45 transition-transform" : "transition-transform"} />
            <span>{showAddForm ? "Cancel" : "+ Remember"}</span>
          </button>
        </div>
      </div>

      {/* Quick Add Synaptic Node Drawer Form */}
      {showAddForm && (
        <form
          onSubmit={handleSaveMemory}
          className="p-4 rounded-2xl bg-[#070F22]/90 border border-purple-400/40 backdrop-blur-xl flex flex-col gap-3 animate-in fade-in slide-in-from-top-2 duration-200 shadow-inner relative z-10"
        >
          <div className="flex items-center justify-between border-b border-purple-500/20 pb-2">
            <span className="text-xs font-mono font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles size={13} className="text-purple-400 animate-spin" /> Encode New Synaptic Knowledge
            </span>
            {saveSuccess && (
              <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 font-bold animate-pulse">
                <Check size={11} /> Synapse Encoded!
              </span>
            )}
          </div>

          <textarea
            placeholder="What should JARVIS remember? (e.g., Master prefers Next.js for web apps, or Deployment key is Vercel)"
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            rows={2}
            className="w-full bg-[#050B18] border border-purple-500/30 rounded-xl p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-400 focus:shadow-[0_0_12px_rgba(168,85,247,0.3)] resize-none"
            autoFocus
          />

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            {/* Category Micro Picker */}
            <div className="flex items-center gap-1">
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value as MemoryCategory)}
                className="bg-[#050B18] border border-purple-500/30 rounded-xl px-2.5 py-1.5 text-xs text-purple-200 focus:outline-none focus:border-purple-400 cursor-pointer font-mono font-bold"
              >
                <option value="preference">🧠 Preference</option>
                <option value="project">🚀 Project</option>
                <option value="instruction">⚡ Instruction</option>
                <option value="fact">💎 Fact</option>
              </select>
            </div>

            {/* Key Field */}
            <div className="flex-1 relative">
              <Tag size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-purple-400" />
              <input
                type="text"
                placeholder="Key / Topic (e.g. editor, theme, framework)"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                className="w-full bg-[#050B18] border border-purple-500/25 rounded-xl pl-8 pr-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-400/60 font-mono"
              />
            </div>

            <button
              type="submit"
              disabled={saving || !newContent.trim()}
              className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 disabled:opacity-50 text-white font-mono font-bold text-xs transition-all shadow-md cursor-pointer flex items-center justify-center gap-1.5 shrink-0"
            >
              {saving ? "Encoding..." : "Save Synapse"}
            </button>
          </div>
        </form>
      )}

      {/* Cyber Search & Filter Hub */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 relative z-10">
        {/* Search Bar */}
        <div className="relative flex-1">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search synaptic matrix by keyword or tag..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#060D1E]/90 border border-cyan-500/20 focus:border-cyan-400/50 rounded-xl pl-8 pr-7 py-1.5 text-xs text-white placeholder-slate-500 font-mono focus:outline-none transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
            >
              <X size={12} />
            </button>
          )}
        </div>

        {/* Category Filter Chips */}
        <div className="flex items-center gap-1 overflow-x-auto pb-0.5 custom-scrollbar shrink-0">
          {[
            { id: "all", label: `All (${memories.length})` },
            { id: "preference", label: "Preferences" },
            { id: "project", label: "Projects" },
            { id: "instruction", label: "Instructions" },
            { id: "fact", label: "Facts" },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setSelectedFilter(f.id)}
              className={`text-[10px] font-mono px-2.5 py-1 rounded-lg border transition-all shrink-0 cursor-pointer ${
                selectedFilter === f.id
                  ? "bg-purple-500/25 text-purple-200 border-purple-400/50 font-bold shadow-[0_0_8px_rgba(168,85,247,0.25)]"
                  : "bg-[#060E20] text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Synaptic Memory Nodes List */}
      <div className="relative z-10">
        {filteredMemories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-7 px-4 text-center bg-[#050C1B]/60 border border-dashed border-purple-500/25 rounded-2xl">
            <div className="w-10 h-10 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-2 shadow-inner">
              <BrainCircuit size={20} className="text-purple-400/80 animate-pulse" />
            </div>
            <span className="text-white text-xs font-semibold">
              {searchQuery ? "No matching synapses found" : "Neural Memory Matrix Idle"}
            </span>
            <p className="text-slate-400 text-[11px] mt-1 max-w-[280px]">
              {searchQuery
                ? `No memory entries matching "${searchQuery}". Clear search to view all.`
                : "JARVIS automatically remembers facts from conversations, or click '+ Remember' above to add custom preferences."}
            </p>

            {/* Quick Suggestion Pills */}
            {!searchQuery && (
              <div className="flex items-center gap-1.5 mt-3 flex-wrap justify-center">
                <button
                  onClick={() => {
                    setNewContent("Prefers VS Code as primary IDE for full-stack development");
                    setNewCategory("preference");
                    setNewKey("editor");
                    setShowAddForm(true);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-purple-500/10 border border-purple-500/25 text-[10px] text-purple-300 hover:bg-purple-500/20 transition-all font-mono"
                >
                  + Add Editor Pref
                </button>
                <button
                  onClick={() => {
                    setNewContent("Primary project is JARVIS Autonomous Voice AI Assistant");
                    setNewCategory("project");
                    setNewKey("active_project");
                    setShowAddForm(true);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-[10px] text-emerald-300 hover:bg-emerald-500/20 transition-all font-mono"
                >
                  + Add Active Project
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto custom-scrollbar pr-1">
            {filteredMemories.map((m) => {
              const meta = categoryMeta(m.category);
              return (
                <div
                  key={m.id}
                  className={`flex items-start justify-between gap-3 p-3 rounded-2xl bg-[#060D1E]/90 border border-slate-800/90 hover:border-purple-500/40 transition-all group/item shadow-sm hover:shadow-[0_0_15px_rgba(168,85,247,0.12)] relative ${meta.glow}`}
                >
                  <div className="flex flex-col gap-1.5 min-w-0 flex-1">
                    {/* Badge Row */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-full border flex items-center gap-1 ${meta.pillClass}`}>
                        <span>{meta.icon}</span>
                        <span>{meta.label}</span>
                      </span>

                      {m.key && (
                        <span className="text-[10px] font-mono font-semibold text-slate-300 bg-[#08132B] px-2 py-0.5 rounded-md border border-cyan-500/20">
                          <span className="text-cyan-400 font-bold">#</span>{m.key}
                        </span>
                      )}

                      <span className="text-[9px] font-mono text-slate-500 ml-auto">
                        ID: {m.id}
                      </span>
                    </div>

                    {/* Content */}
                    <p className="text-slate-100 text-xs font-normal leading-relaxed break-words font-sans">
                      {m.content}
                    </p>
                  </div>

                  {/* Quick Action Buttons */}
                  <div className="flex items-center gap-1 shrink-0 opacity-80 group-hover/item:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleCopyContent(m.id, m.content)}
                      className="w-7 h-7 rounded-lg bg-[#081226] hover:bg-purple-500/20 text-slate-400 hover:text-purple-300 border border-slate-800 hover:border-purple-400/40 flex items-center justify-center transition-all cursor-pointer"
                      title="Copy memory content"
                    >
                      {copiedId === m.id ? (
                        <CheckCheck size={12} className="text-emerald-400" />
                      ) : (
                        <Copy size={12} />
                      )}
                    </button>

                    <button
                      onClick={() => handleDeleteMemory(m.id)}
                      className="w-7 h-7 rounded-lg bg-[#081226] hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-400/40 flex items-center justify-center transition-all cursor-pointer"
                      title="Purge synapse from matrix"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Synapse Stats Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-purple-500/20 text-[10px] font-mono text-slate-400 relative z-10">
        <div className="flex items-center gap-1.5">
          <ShieldCheck size={12} className="text-emerald-400" />
          <span>Local Memory Guard Active</span>
        </div>
        <span className="text-purple-300 font-bold">
          {memories.length} Stored Synapses
        </span>
      </div>
    </div>
  );
}
