"use client";

import React, { useEffect, useRef, useState } from "react";
import { 
  MessageSquare, Mic, BrainCircuit,    
  BatteryMedium, Send, Trash2, Volume2, 
  VolumeX, Sparkles, ShieldAlert, KeyRound, 
  Timer, ShieldCheck, 
  Radio, Cpu, Zap, Layers, Eye, Bot,
  Copy, Check
} from "lucide-react";
import { JarvisOrb } from "@/components/JarvisOrb";
import { CreatorDossierModal, CreatorDossierData } from "@/components/CreatorDossierModal";
import { Sidebar } from "@/components/Sidebar";
import { HudModuleModal, HudModuleTab } from "@/components/HudModuleModal";

interface SpeechResultAlternative {
  transcript: string;
}

interface SpeechResultItem {
  isFinal?: boolean;
  length: number;
  [index: number]: SpeechResultAlternative;
}

interface SpeechResultList {
  length: number;
  [index: number]: SpeechResultItem;
}

interface BrowserSpeechRecognizer {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: { results: SpeechResultList; resultIndex?: number }) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  abort: () => void;
  stop: () => void;
}

export function cleanTextForSpeech(text: string): string {
  if (!text) return "";
  let cleaned = text.replace(/```[\s\S]*?```/g, "Code screen par display kar diya hai.");
  cleaned = cleaned.replace(/`([^`]+)`/g, "$1");
  cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  cleaned = cleaned.replace(/!\[([^\]]*)\]\([^)]+\)/g, "");
  cleaned = cleaned.replace(/^#+\s+/gm, "");
  cleaned = cleaned.replace(/[*_~#|]/g, "");
  cleaned = cleaned.replace(/^[-*+]\s+/gm, "");
  cleaned = cleaned.replace(/\s+/g, " ").trim();

  if (!cleaned) {
    return "Ji Akmal bhai, details screen par display kar di hain.";
  }

  if (cleaned.length > 200) {
    const sentences = cleaned.match(/[^.!?]+[.!?]+/g);
    if (sentences && sentences.length > 0) {
      cleaned = sentences.slice(0, 2).join(" ").trim();
    } else {
      cleaned = cleaned.slice(0, 180).trim() + "...";
    }
  }
  return cleaned;
}

let messageSequenceId = 0;
function createMessageId(): string {
  messageSequenceId += 1;
  return `msg_${messageSequenceId}`;
}

export default function Dashboard() {
  // Chat & Messaging State
  const [messages, setMessages] = useState<{
    id: string;
    sender: "user" | "jarvis";
    text: string;
    spokenText?: string;
    time: string;
    suggestions?: string[];
  }[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [isWakeWordEnabled, setIsWakeWordEnabled] = useState(true);
  const [isContinuousConversation, setIsContinuousConversation] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<"ur" | "en" | "hi" | "auto">("ur");
  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  // Synchronized Engine Refs (prevents state-closure race conditions in async voice recognizers)
  const isListeningRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const isWakeWordEnabledRef = useRef(true);
  const isContinuousConversationRef = useRef(false);
  const loadingRef = useRef(false);
  const selectedLanguageRef = useRef<"ur" | "en" | "hi" | "auto">("ur");
  const currentRecognizerRef = useRef<BrowserSpeechRecognizer | null>(null);
  const activeModeRef = useRef<"idle" | "wake" | "active">("idle");
  const isTransitioningRef = useRef(false);
  const startWakeWordListeningRef = useRef<() => void>(() => {});

  useEffect(() => {
    isListeningRef.current = isListening;
    isSpeakingRef.current = isSpeaking;
    isWakeWordEnabledRef.current = isWakeWordEnabled;
    isContinuousConversationRef.current = isContinuousConversation;
    loadingRef.current = loading;
    selectedLanguageRef.current = selectedLanguage;
  }, [isListening, isSpeaking, isWakeWordEnabled, isContinuousConversation, loading, selectedLanguage]);

  const handleCopyText = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(id);
      setTimeout(() => {
        setCopiedMessageId((prev) => (prev === id ? null : prev));
      }, 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Time & Date
  const [time, setTime] = useState("");
  const [date, setDate] = useState("");
  
  // Hardware Telemetry
  const [batteryLevel, setBatteryLevel] = useState<number | null>(null);
  const [isCharging, setIsCharging] = useState(false);
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: 0,
    ram: 0,
    ramUsed: 0,
    ramTotal: 0,
    diskFree: 0,
  });

  // Security Confirmation & PIN State (Phase 3)
  const [pendingAction, setPendingAction] = useState<{
    confirmationId: string;
    requiresPin: boolean;
    description: string;
    toolName: string;
  } | null>(null);
  const [pinInput, setPinInput] = useState("");
  const [confirmingAction, setConfirmingAction] = useState(false);

  // Timers, Alarms, Reminders State (Phase 3C)
  const [activeTimers, setActiveTimers] = useState<{
    id: string;
    label: string;
    remaining: string;
    duration_seconds?: number;
    fire_at?: number;
  }[]>([]);
  const [activeAlarms, setActiveAlarms] = useState<{ id: string; label: string; fires_at: string }[]>([]);
  const [activeReminders, setActiveReminders] = useState<{ id: string; message: string; fires_at: string }[]>([]);
  const [showTimerCreator, setShowTimerCreator] = useState(false);
  const [creatorTab, setCreatorTab] = useState<"timer" | "alarm" | "reminder">("timer");
  const [customLabel, setCustomLabel] = useState("");
  const [customHours, setCustomHours] = useState(0);
  const [customMinutes, setCustomMinutes] = useState(5);
  const [customSeconds, setCustomSeconds] = useState(0);
  const [alarmTimeInput, setAlarmTimeInput] = useState("07:30");
  const [reminderTextInput, setReminderTextInput] = useState("");
  const [reminderWhenInput, setReminderWhenInput] = useState("30 minutes");
  const [creatingTimer, setCreatingTimer] = useState(false);
  const [currentTimeSec, setCurrentTimeSec] = useState<number>(0);
  const notifiedTimersRef = useRef<Set<string>>(new Set());

  // Creator Digital Dossier Modal State (Phase 6A)
  const [showVaultModal, setShowVaultModal] = useState(false);
  const [dossier, setDossier] = useState<CreatorDossierData | null>(null);
  const [isSyncingDossier, setIsSyncingDossier] = useState(false);

  // Tactical HUD Subsystems Modal State
  const [isHudModalOpen, setIsHudModalOpen] = useState(false);
  const [activeDockTab, setActiveDockTab] = useState<HudModuleTab>("memory");

  const openHudModal = (tab: HudModuleTab) => {
    setActiveDockTab(tab);
    setIsHudModalOpen(true);
  };

  const showNotice = (msg: string) => {
    setVoiceNotice(msg);
    setTimeout(() => setVoiceNotice(null), 3000);
  };

  // Fetch Creator Dossier
  const fetchDossier = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/dossier");
      if (res.ok) {
        const data = await res.json();
        setDossier(data.dossier || null);
      }
    } catch {
      // offline
    }
  };

  const handleSyncOnlineFootprint = async (customGh?: string) => {
    setIsSyncingDossier(true);
    showNotice("Scanning GitHub & synchronizing online footprint...");
    try {
      const ghToUse = customGh !== undefined 
        ? customGh 
        : (dossier?.social_profiles?.github_username || dossier?.social_profiles?.github || "");
      const cleanGh = ghToUse.trim().replace("https://github.com/", "").replace("/", "");
      const res = await fetch("http://127.0.0.1:8000/api/dossier/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ github_username: cleanGh || undefined }),
      });
      const data = await res.json();
      if (data.status === "success" && data.sync_result?.success) {
        showNotice(`Online footprint synced! ${data.sync_result.public_repos} public repos retrieved.`);
        await fetchDossier();
      } else {
        showNotice(data.sync_result?.message || "Sync completed. Check dossier details.");
        await fetchDossier();
      }
    } catch {
      showNotice("Network error during online sync.");
    } finally {
      setIsSyncingDossier(false);
    }
  };

  const handleSaveDossier = async (updates: Partial<CreatorDossierData>) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/dossier/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ updates }),
      });
      if (res.ok) {
        showNotice("Creator Digital Dossier updated & locked into JARVIS AI Brain!");
        await fetchDossier();
      } else {
        showNotice("Failed to save dossier.");
      }
    } catch {
      showNotice("Network error saving dossier.");
    }
  };

  // 1-second real-time ticker for Timers, Clock & System Date
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTimeSec(Math.floor(Date.now() / 1000));
      setTime(now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true }));
      setDate(now.toLocaleDateString("en-US", { weekday: "short", day: "2-digit", month: "short", year: "numeric" }));
    };
    updateTime();
    const ticker = setInterval(updateTime, 1000);
    return () => {
      clearInterval(ticker);
    };
  }, []);

  // Web Audio API Futuristic Chime Alert
  const playTimerChime = () => {
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const playTone = (freq: number, start: number, dur: number) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, ctx.currentTime + start);
        gain.gain.setValueAtTime(0.2, ctx.currentTime + start);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + dur);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + start);
        osc.stop(ctx.currentTime + start + dur);
      };
      playTone(587.33, 0.0, 0.22); // D5
      playTone(880.00, 0.16, 0.22); // A5
      playTone(1174.66, 0.32, 0.45); // D6
    } catch {
      // AudioContext unavailable
    }
  };

  // Poll real-time hardware status every 3.5s
  useEffect(() => {
    let active = true;
    const fetchStatus = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/system/status");
        if (res.ok) {
          const data = await res.json();
          if (active && data.success) {
            setSystemMetrics({
              cpu: data.cpu_percent,
              ram: data.ram_percent,
              ramUsed: data.ram_used_gb,
              ramTotal: data.ram_total_gb,
              diskFree: data.disk_free_gb,
            });
            if (data.battery) {
              setBatteryLevel(data.battery.percent);
              setIsCharging(data.battery.power_plugged);
            }
          }
        }
      } catch {
        // Backend offline or polling idle
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3500);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  // Browser Battery API integration
  useEffect(() => {
    if (typeof navigator !== "undefined" && "getBattery" in navigator) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (navigator as any).getBattery?.().then((bat: any) => {
        if (bat) {
          setBatteryLevel(Math.round(bat.level * 100));
          setIsCharging(bat.charging);
          bat.addEventListener("levelchange", () => {
            setBatteryLevel(Math.round(bat.level * 100));
          });
          bat.addEventListener("chargingchange", () => {
            setIsCharging(bat.charging);
          });
        }
      }).catch(() => {});
    }
  }, []);

  // Fetch active timers list
  const fetchTimersList = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/timers");
      if (res.ok) {
        const data = await res.json();
        setActiveTimers(data.timers || []);
        setActiveAlarms(data.alarms || []);
        setActiveReminders(data.reminders || []);

        if (Array.isArray(data.timers)) {
          data.timers.forEach((t: { id: string; remaining: string; label: string }) => {
            if (t.remaining === "00:00" && !notifiedTimersRef.current.has(t.id)) {
              notifiedTimersRef.current.add(t.id);
              playTimerChime();
              showNotice(`🔔 Timer '${t.label}' has completed!`);
            }
          });
        }
      }
    } catch {
      // silent
    }
  };

  useEffect(() => {
    let active = true;

    const pollTimers = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/timers");
        if (res.ok && active) {
          const data = await res.json();
          setActiveTimers(data.timers || []);
          setActiveAlarms(data.alarms || []);
          setActiveReminders(data.reminders || []);

          if (Array.isArray(data.timers)) {
            data.timers.forEach((t: { id: string; remaining: string; label: string }) => {
              if (t.remaining === "00:00" && !notifiedTimersRef.current.has(t.id)) {
                notifiedTimersRef.current.add(t.id);
                playTimerChime();
                showNotice(`🔔 Timer '${t.label}' has completed!`);
              }
            });
          }
        }
      } catch {
        // silent
      }
    };

    const loadDossier = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/dossier");
        if (res.ok && active) {
          const data = await res.json();
          setDossier(data.dossier || null);
        }
      } catch {
        // offline
      }
    };

    pollTimers();
    loadDossier();

    const timerInterval = setInterval(pollTimers, 1500);
    return () => {
      active = false;
      clearInterval(timerInterval);
    };
  }, []);

  // Custom Timer Creation
  const handleCreateCustomTimer = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const totalSecs = customHours * 3600 + customMinutes * 60 + customSeconds;
    if (totalSecs <= 0) return;
    setCreatingTimer(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/timers/set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          seconds: totalSecs,
          label: customLabel.trim() || undefined,
        })
      });
      if (res.ok) {
        const data = await res.json();
        showNotice(`Timer set for ${data.label}!`);
        setShowTimerCreator(false);
        setCustomLabel("");
        fetchTimersList();
      }
    } catch {
      showNotice("Failed to create timer.");
    } finally {
      setCreatingTimer(false);
    }
  };

  const handleLaunchPreset = async (presetSeconds: number, presetName: string) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/timers/set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          seconds: presetSeconds,
          label: presetName,
        })
      });
      if (res.ok) {
        showNotice(`Started ${presetName}!`);
        fetchTimersList();
      }
    } catch {
      showNotice("Preset timer failed to launch.");
    }
  };

  const handleCreateCustomAlarm = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!alarmTimeInput.trim()) return;
    setCreatingTimer(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/alarms/set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alarm_time: alarmTimeInput.trim(),
          label: customLabel.trim() || undefined,
        })
      });
      if (res.ok) {
        const data = await res.json();
        showNotice(`Alarm set for ${data.fires_at}!`);
        setShowTimerCreator(false);
        setCustomLabel("");
        fetchTimersList();
      }
    } catch {
      showNotice("Failed to set alarm.");
    } finally {
      setCreatingTimer(false);
    }
  };

  const handleCreateCustomReminder = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!reminderTextInput.trim()) return;
    setCreatingTimer(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/reminders/set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: reminderTextInput.trim(),
          when: reminderWhenInput.trim() || "30 minutes",
        })
      });
      if (res.ok) {
        const data = await res.json();
        showNotice(`Reminder scheduled: ${data.message_text}!`);
        setShowTimerCreator(false);
        setReminderTextInput("");
        fetchTimersList();
      }
    } catch {
      showNotice("Failed to schedule reminder.");
    } finally {
      setCreatingTimer(false);
    }
  };

  const handleCancelItem = async (itemId: string, itemType: string) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/timers/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timer_id: itemId })
      });
      if (res.ok) {
        showNotice(`${itemType} cancelled.`);
        fetchTimersList();
      }
    } catch {
      showNotice("Failed to cancel item.");
    }
  };

  const formatSecondsToClock = (sec: number) => {
    if (sec <= 0) return "00:00";
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    if (h > 0) {
      return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    }
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  // Battery Status
  useEffect(() => {
    let active = true;
    if ("getBattery" in navigator) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (navigator as any).getBattery().then((batt: any) => {
        if (!active) return;
        setBatteryLevel(Math.round(batt.level * 100));
        setIsCharging(batt.charging);

        batt.addEventListener("levelchange", () => {
          setBatteryLevel(Math.round(batt.level * 100));
        });
        batt.addEventListener("chargingchange", () => {
          setIsCharging(batt.charging);
        });
      });
    } else {
      setTimeout(() => {
        if (active) {
          setBatteryLevel(100);
          setIsCharging(true);
        }
      }, 0);
    }
    return () => { active = false; };
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    if (messages.length > 0 && chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [messages, loading]);

  // Audio Speech Control
  const stopSpeaking = async () => {
    setIsSpeaking(false);
    try {
      await fetch("http://127.0.0.1:8000/api/voice/stop", { method: "POST" });
    } catch {
      // ignore
    }
  };

  const speakResponse = async (text: string) => {
    if (!isVoiceEnabled || !text.trim()) return;
    setIsSpeaking(true);
    try {
      await fetch("http://127.0.0.1:8000/api/voice/speak", {
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
    } catch {
      // ignore
    } finally {
      setIsSpeaking(false);
    }
  };

  const toggleVoiceOutput = () => {
    if (isVoiceEnabled) {
      stopSpeaking();
      setIsVoiceEnabled(false);
      showNotice("Voice Output Muted");
    } else {
      setIsVoiceEnabled(true);
      showNotice("Neural Voice Output Enabled");
    }
  };

  const playWakeChime = () => {
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(587.33, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.28, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.38);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.4);
    } catch {
      // ignore
    }
  };

  const getSpeechRecognizer = () => {
    if (typeof window === "undefined") return null;
    const win = window as unknown as { 
      SpeechRecognition?: new () => BrowserSpeechRecognizer; 
      webkitSpeechRecognition?: new () => BrowserSpeechRecognizer 
    };
    return win.SpeechRecognition || win.webkitSpeechRecognition || null;
  };

  const stopCurrentRecognizer = () => {
    if (currentRecognizerRef.current) {
      try {
        const rec = currentRecognizerRef.current;
        currentRecognizerRef.current = null;
        rec.onresult = null;
        rec.onerror = null;
        rec.onend = null;
        rec.stop();
      } catch {
        // ignore
      }
    }
  };

  const checkWakeWord = (rawText: string) => {
    if (!rawText) return { detected: false, command: "" };
    const lower = rawText.toLowerCase().trim();

    // Comprehensive phonetic & multilingual wake word markers
    const wakeMarkers = [
      "jarvis", "jarvice", "jervis", "zarvis", "yarvis", "service",
      "hey jarvis", "hay jarvis", "aye jarvis", "oye jarvis",
      "suno jarvis", "jarvis suno", "hello jarvis", "hi jarvis",
      "ok jarvis", "okay jarvis", "جاروس", "جارویس", "سنو جاروس"
    ];

    const hasWakeWord = wakeMarkers.some(m => lower.includes(m));
    if (!hasWakeWord) return { detected: false, command: "" };

    // Extract command after wake word
    const command = rawText
      .replace(/^(?:hey|hay|aye|oi|oye|ok|okay|suno|hello|hi|سنو|اوئے|ہیلو)?\s*(?:jarvis|jarvice|jervis|zarvis|yarvis|service|جاروس|جارویس)\s*[,.:!?-]?\s*/i, "")
      .replace(/\b(?:hey|suno|oye)?\s*(?:jarvis|jarvice|jervis|zarvis|yarvis|service|جاروس|جارویس)\b/i, "")
      .trim();

    return { detected: true, command };
  };

  const onWakeWordTriggered = async (command: string) => {
    if (isTransitioningRef.current) return;
    isTransitioningRef.current = true;

    stopCurrentRecognizer();
    playWakeChime();

    if (command && command.length > 1) {
      showNotice(`🎙️ Wake Command: "${command}"`);
      isTransitioningRef.current = false;
      handleSend(undefined, command);
    } else {
      showNotice("🎙️ JARVIS: Ji Akmal bhai? Listening...");
      await speakResponse("Ji Akmal bhai?");
      isTransitioningRef.current = false;
      setTimeout(() => {
        startActiveListening("Ji Akmal bhai, sun raha hoon...");
      }, 250);
    }
  };

  const startWakeWordListening = () => {
    if (!isWakeWordEnabledRef.current || isListeningRef.current || isSpeakingRef.current || loadingRef.current || isTransitioningRef.current) {
      return;
    }

    stopCurrentRecognizer();

    const SpeechRec = getSpeechRecognizer();
    if (!SpeechRec) return;

    try {
      const recognizer = new SpeechRec();
      recognizer.continuous = true;
      recognizer.interimResults = true;
      recognizer.lang = "en-US";

      activeModeRef.current = "wake";

      recognizer.onresult = (event) => {
        if (isSpeakingRef.current || isListeningRef.current || loadingRef.current || isTransitioningRef.current) {
          return;
        }

        const startIdx = event.resultIndex ?? 0;
        for (let i = startIdx; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript.trim();
          if (!transcript) continue;

          const match = checkWakeWord(transcript);
          if (match.detected) {
            onWakeWordTriggered(match.command);
            break;
          }
        }
      };

      recognizer.onerror = (err: { error?: string }) => {
        if (err.error === "not-allowed") {
          showNotice("Microphone permission blocked. Please allow microphone in browser.");
        }
      };

      recognizer.onend = () => {
        if (activeModeRef.current === "wake" && isWakeWordEnabledRef.current && !isListeningRef.current && !isSpeakingRef.current && !loadingRef.current && !isTransitioningRef.current) {
          setTimeout(() => {
            if (activeModeRef.current === "wake" && isWakeWordEnabledRef.current && !isListeningRef.current && !isSpeakingRef.current) {
              startWakeWordListening();
            }
          }, 450);
        }
      };

      currentRecognizerRef.current = recognizer;
      recognizer.start();
    } catch (e) {
      console.warn("Wake word listener init notice:", e);
    }
  };
  useEffect(() => {
    startWakeWordListeningRef.current = startWakeWordListening;
  });

  const startActiveListening = (customPrompt?: string) => {
    if (isSpeakingRef.current) {
      stopSpeaking();
    }
    stopCurrentRecognizer();

    activeModeRef.current = "active";
    setIsListening(true);
    isListeningRef.current = true;

    const langLabel = selectedLanguageRef.current === "ur" ? "Urdu" : selectedLanguageRef.current === "hi" ? "Hindi" : selectedLanguageRef.current === "en" ? "English" : "Auto";
    setInputValue(customPrompt || `Listening... [${langLabel}]`);

    const sttLanguage = selectedLanguageRef.current === "en" ? "en-US" : selectedLanguageRef.current === "hi" ? "hi-IN" : "ur-PK";

    const SpeechRec = getSpeechRecognizer();
    if (SpeechRec) {
      try {
        const recognizer = new SpeechRec();
        recognizer.continuous = false;
        recognizer.interimResults = true;
        recognizer.lang = sttLanguage;

        let finalTranscript = "";

        recognizer.onresult = (event) => {
          let interim = "";
          for (let i = 0; i < event.results.length; i++) {
            const res = event.results[i];
            if (res.isFinal || (res as unknown as SpeechResultAlternative[])[0]) {
              const text = res[0].transcript;
              if (res.isFinal) {
                finalTranscript = text;
              } else {
                interim += text;
              }
            }
          }
          if (interim) {
            setInputValue(interim);
          }
        };

        recognizer.onerror = async (err: { error?: string }) => {
          console.warn("SpeechRecognition active notice:", err);
          if (err.error === "not-allowed") {
            showNotice("Microphone permission blocked. Please click the lock icon in address bar to Allow.");
            setIsListening(false);
            isListeningRef.current = false;
            setInputValue("");
          } else if (err.error === "no-speech") {
            setIsListening(false);
            isListeningRef.current = false;
            setInputValue("");
            if (isContinuousConversationRef.current) {
              setTimeout(() => {
                if (isContinuousConversationRef.current && !isSpeakingRef.current && !loadingRef.current) {
                  startActiveListening();
                }
              }, 400);
            } else if (isWakeWordEnabledRef.current) {
              setTimeout(() => {
                startWakeWordListening();
              }, 300);
            }
          } else {
            setIsListening(false);
            isListeningRef.current = false;
            await fallbackBackendListen(sttLanguage);
          }
        };

        recognizer.onend = () => {
          setIsListening(false);
          isListeningRef.current = false;
          const trimmed = finalTranscript.trim();
          if (trimmed) {
            setInputValue(trimmed);

            // Check for Open Mic exit phrases
            const lower = trimmed.toLowerCase();
            const exitPhrases = ["stop conversation", "band karo", "shukriya jarvis", "alvida", "goodbye", "sleep mode", "stop listening"];
            if (isContinuousConversationRef.current && exitPhrases.some(p => lower.includes(p))) {
              setIsContinuousConversation(false);
              isContinuousConversationRef.current = false;
              showNotice("Open Mic mode ended.");
              speakResponse("Ji Akmal bhai, open mic band kar diya hai. Standby mode active.");
              setTimeout(() => {
                if (isWakeWordEnabledRef.current) startWakeWordListening();
              }, 400);
              return;
            }

            handleSend(undefined, trimmed);
          } else {
            setInputValue("");
            if (isContinuousConversationRef.current) {
              setTimeout(() => {
                if (isContinuousConversationRef.current && !isSpeakingRef.current && !loadingRef.current) {
                  startActiveListening();
                }
              }, 400);
            } else if (isWakeWordEnabledRef.current) {
              setTimeout(() => {
                startWakeWordListening();
              }, 300);
            }
          }
        };

        currentRecognizerRef.current = recognizer;
        recognizer.start();
        return;
      } catch (e) {
        console.warn("Native speech start failed, falling back to backend:", e);
      }
    }

    fallbackBackendListen(sttLanguage);
  };

  const fallbackBackendListen = async (sttLanguage: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/voice/listen?language=${sttLanguage}`, {
        method: "POST"
      });
      if (response.ok) {
        const data = await response.json();
        if (data.status === "timeout" || data.status === "unrecognized") {
          setInputValue("");
          if (isContinuousConversationRef.current) {
            setTimeout(() => {
              if (isContinuousConversationRef.current && !isSpeakingRef.current && !loadingRef.current) {
                startActiveListening();
              }
            }, 500);
          } else if (isWakeWordEnabledRef.current) {
            setTimeout(() => {
              startWakeWordListening();
            }, 300);
          }
          return;
        }

        setInputValue(data.transcript);
        handleSend(undefined, data.transcript);
      } else {
        const err = await response.json();
        setInputValue("");
        showNotice(err.detail || "Couldn't catch that clearly.");
      }
    } catch {
      setInputValue("");
      showNotice("Failed to connect to JARVIS Voice Engine.");
    } finally {
      setIsListening(false);
      isListeningRef.current = false;
    }
  };

  const toggleWakeWord = async () => {
    const nextState = !isWakeWordEnabled;
    setIsWakeWordEnabled(nextState);
    isWakeWordEnabledRef.current = nextState;
    try {
      await fetch("http://127.0.0.1:8000/api/voice/wake-word/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: nextState })
      });
    } catch {
      // ignore
    }
    showNotice(nextState ? "🎙️ Hands-Free Wake Word armed! Say 'Hey JARVIS' or 'Suno JARVIS' anytime." : "Wake Word listening paused.");
    if (nextState) {
      playWakeChime();
      setTimeout(() => {
        startWakeWordListening();
      }, 300);
    } else {
      stopCurrentRecognizer();
    }
  };

  const toggleContinuousConversation = async () => {
    const nextState = !isContinuousConversation;
    setIsContinuousConversation(nextState);
    isContinuousConversationRef.current = nextState;

    if (nextState) {
      if (!isWakeWordEnabled) {
        setIsWakeWordEnabled(true);
        isWakeWordEnabledRef.current = true;
      }
      playWakeChime();
      showNotice("🎙️ Open Mic Mode ACTIVATED! Speak freely without saying 'JARVIS'.");
      await speakResponse("Ji Akmal bhai, open mic active hai. Aap direct baat kar sakte hain.");
      setTimeout(() => {
        startActiveListening();
      }, 350);
    } else {
      showNotice("Open Mic Mode paused. Standby mode active.");
      stopCurrentRecognizer();
      await speakResponse("Open mic paused.");
      setTimeout(() => {
        if (isWakeWordEnabledRef.current) {
          startWakeWordListening();
        }
      }, 300);
    }
  };

  const toggleListen = () => {
    if (isListeningRef.current) {
      stopCurrentRecognizer();
      setIsListening(false);
      isListeningRef.current = false;
      setInputValue("");
      if (isWakeWordEnabledRef.current) {
        setTimeout(() => startWakeWordListening(), 300);
      }
    } else {
      startActiveListening();
    }
  };

  const handleOrbClick = () => {
    if (isSpeaking) {
      stopSpeaking();
    } else {
      toggleListen();
    }
  };

  const handleSend = async (e?: React.FormEvent, overrideText?: string) => {
    e?.preventDefault();
    const textToSend = overrideText || inputValue;
    if (!textToSend.trim() || loading) return;
    
    if (isSpeaking) {
      await stopSpeaking();
    }

    const userMsg = { id: createMessageId(), sender: "user" as const, text: textToSend, time };
    setMessages(prev => [...prev, userMsg]);
    setInputValue("");
    setLoading(true);
    loadingRef.current = true;

    const conversationHistory = messages.map(m => ({
      role: m.sender === "user" ? "user" : "assistant",
      content: m.text
    }));

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ 
          prompt: userMsg.text, 
          history: conversationHistory, 
          response_language: selectedLanguage 
        })
      });
      clearTimeout(timeoutId);
      const data = await response.json();
      const reply = data.response || "No response";
      const spoken = data.spoken_response || cleanTextForSpeech(reply);

      if (data.status === "pending_confirmation") {
        setPendingAction({
          confirmationId: data.confirmation_id,
          requiresPin: data.requires_pin,
          description: data.response,
          toolName: data.tool_name || "System Action",
        });
      }

      setMessages(prev => [...prev, { 
        id: createMessageId(), 
        sender: "jarvis", 
        text: reply, 
        spokenText: spoken,
        suggestions: data.suggestions || [],
        time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }) 
      }]);
      await speakResponse(spoken);
    } catch (err: unknown) {
      const isAbort = err instanceof Error && err.name === "AbortError";
      const errorMsg = isAbort 
        ? "JARVIS AI core request timed out. Please try again." 
        : "Connection error with JARVIS AI core.";
      setMessages(prev => [...prev, { 
        id: createMessageId(), 
        sender: "jarvis", 
        text: errorMsg, 
        spokenText: errorMsg,
        time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }) 
      }]);
    } finally {
      setLoading(false);
      loadingRef.current = false;

      // Seamless hands-free continuation
      if (isContinuousConversationRef.current) {
        setTimeout(() => {
          if (isContinuousConversationRef.current && !isSpeakingRef.current) {
            startActiveListening();
          }
        }, 350);
      } else if (isWakeWordEnabledRef.current) {
        setTimeout(() => {
          if (!isListeningRef.current && !isSpeakingRef.current) {
            startWakeWordListening();
          }
        }, 250);
      }
    }
  };

  const handleConfirmAction = async () => {
    if (!pendingAction) return;
    setConfirmingAction(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/security/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          confirmation_id: pendingAction.confirmationId,
          pin: pendingAction.requiresPin ? pinInput : undefined,
        })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(`Action '${pendingAction.toolName}' approved and executed!`);
        const confirmMsg = data.result?.result?.message || `Executed ${pendingAction.toolName}.`;
        const spokenConfirm = "Ji Akmal bhai, action approve kar ke execute kar diya hai.";
        setMessages(prev => [...prev, {
          id: createMessageId(),
          sender: "jarvis",
          text: confirmMsg,
          spokenText: spokenConfirm,
          time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
        }]);
        await speakResponse(spokenConfirm);
        setPendingAction(null);
        setPinInput("");

        if (isContinuousConversationRef.current) {
          setTimeout(() => {
            if (isContinuousConversationRef.current && !isSpeakingRef.current) {
              startActiveListening();
            }
          }, 350);
        } else if (isWakeWordEnabledRef.current) {
          setTimeout(() => {
            if (!isListeningRef.current && !isSpeakingRef.current) {
              startWakeWordListening();
            }
          }, 250);
        }
      } else {
        showNotice(data.detail || "Confirmation rejected.");
      }
    } catch {
      showNotice("Security confirmation request failed.");
    } finally {
      setConfirmingAction(false);
    }
  };

  const handleCancelAction = async () => {
    if (!pendingAction) return;
    try {
      await fetch("http://127.0.0.1:8000/api/security/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmation_id: pendingAction.confirmationId })
      });
    } catch {
      // ignore
    }
    showNotice("Action cancelled by user.");
    setPendingAction(null);
    setPinInput("");
  };

  // Push-To-Talk Spacebar shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeEl = document.activeElement;
      const isInput = activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA");
      if (e.code === "Space" && !isInput && !e.repeat) {
        e.preventDefault();
        const trigger = document.getElementById("jarvis-orb-trigger");
        if (trigger) trigger.click();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Initialize Background Wake Word on load + Microphone permission unlock
  useEffect(() => {
    if (typeof window === "undefined") return;

    // Silent microphone permission unlock on first user gesture
    const handleFirstInteraction = () => {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ audio: true }).catch(() => {});
      }
      window.removeEventListener("click", handleFirstInteraction);
      window.removeEventListener("keydown", handleFirstInteraction);
    };
    window.addEventListener("click", handleFirstInteraction);
    window.addEventListener("keydown", handleFirstInteraction);

    if (isWakeWordEnabledRef.current) {
      const timer = setTimeout(() => {
        startWakeWordListeningRef.current();
      }, 700);
      return () => {
        clearTimeout(timer);
        stopCurrentRecognizer();
      };
    }
  }, []);

  const previewVoice = async (lang: "ur" | "en") => {
    const text = lang === "ur" 
      ? "Ji Akmal bhai! Main Asad hoon, aapka neural AI voice assistant." 
      : "Hello Akmal! I am Christopher, your dedicated English neural assistant.";
    await speakResponse(text);
  };

  const orbStatus = isListening ? "listening" : loading ? "thinking" : isSpeaking ? "speaking" : "idle";

  return (
    <main className="h-screen w-screen overflow-hidden flex flex-col bg-[#030712] font-sans text-slate-100 select-none relative">
      {/* Holographic Top Horizon Laser Bar */}
      <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22d3ee] shrink-0" />

      {/* ==================== 1. ULTRA-SLEEK MINIMAL HUD NAVBAR ==================== */}
      <header className="h-14 border-b border-cyan-500/15 bg-[#030712]/75 backdrop-blur-xl px-5 flex items-center justify-between shrink-0 z-30 shadow-sm">
          {/* Left: Minimal Futuristic Brand */}
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg border border-cyan-400/40 bg-cyan-950/40 flex items-center justify-center shadow-[0_0_12px_rgba(6,182,212,0.3)]">
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_#22d3ee]" />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-hud font-bold text-sm tracking-[0.2em] text-white">
                J.A.R.V.I.S
              </span>
              <span className="text-[10px] font-mono text-cyan-400/90 font-semibold px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/25">
                MARK IX
              </span>
            </div>
          </div>

          {/* Center: Featherlight Compact Voice Control Strip */}
          <div className="flex items-center gap-1 px-3 py-1 rounded-full bg-[#07132B]/70 border border-cyan-500/20 backdrop-blur-md shadow-inner">
            {/* Wake Word Arming Toggle */}
            <button
              onClick={toggleWakeWord}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono transition-all cursor-pointer ${
                isWakeWordEnabled
                  ? "bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-400/30 shadow-[0_0_8px_rgba(6,182,212,0.25)]"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Hands-free Wake Word Detection (Hey JARVIS / Suno JARVIS)"
            >
              <Radio size={12} className={isWakeWordEnabled ? "text-cyan-400 animate-pulse" : "text-slate-500"} />
              <span className="text-[11px]">Wake</span>
            </button>

            {/* Continuous Open Mic Toggle */}
            <button
              onClick={toggleContinuousConversation}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono transition-all cursor-pointer ${
                isContinuousConversation
                  ? "bg-emerald-500/25 text-emerald-300 font-bold border border-emerald-400/30 shadow-[0_0_8px_rgba(16,185,129,0.25)]"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Continuous Open Mic Mode"
            >
              <Mic size={12} className={isContinuousConversation ? "text-emerald-400 animate-pulse" : "text-slate-500"} />
              <span className="text-[11px]">Open Mic</span>
            </button>

            {/* Mute/Unmute Audio Voice */}
            <button
              onClick={toggleVoiceOutput}
              className={`p-1.5 rounded-full transition-all cursor-pointer ${
                isVoiceEnabled ? "text-cyan-400 hover:bg-cyan-500/15" : "text-slate-500 hover:text-white"
              }`}
              title={isVoiceEnabled ? "Mute Voice Output" : "Enable Voice Output"}
            >
              {isVoiceEnabled ? <Volume2 size={13} /> : <VolumeX size={13} />}
            </button>

            <div className="w-[1px] h-3.5 bg-cyan-500/20 mx-1" />

            {/* Sleek Minimalist Language Micro-Buttons */}
            <div className="flex items-center gap-0.5 text-[10px] font-mono">
              {(["ur", "en", "auto"] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setSelectedLanguage(lang)}
                  className={`px-2 py-0.5 rounded-full transition-all cursor-pointer ${
                    selectedLanguage === lang
                      ? "bg-cyan-500/25 text-cyan-200 font-bold border border-cyan-400/40 shadow-[0_0_8px_rgba(6,182,212,0.2)]"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {lang === "ur" ? "UR" : lang === "en" ? "EN" : "AUTO"}
                </button>
              ))}
            </div>

            <div className="w-[1px] h-3.5 bg-cyan-500/20 mx-1 hidden md:block" />

            {/* Global System Hotkey Badge (Phase 9 & 10) */}
            <div 
              className="hidden md:flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950/40 text-cyan-300/90 border border-cyan-500/25 shadow-sm"
              title="Global Windows Summon: Press 'Ctrl + Space' from any app to summon JARVIS"
            >
              <Zap size={10} className="text-cyan-400 animate-pulse" />
              <span>Ctrl+Space</span>
            </div>
          </div>

          {/* Right: Unified System Vitals Capsule, Clock & Date Stack, Minimal Creator Profile */}
          <div className="flex items-center gap-3">
            {/* Unified Cyber Hardware Telemetry Capsule (CPU • RAM • BAT) */}
            <div
              className="hidden sm:flex items-center gap-2.5 lg:gap-3 px-3.5 py-1 rounded-full bg-[#07132B]/85 border border-cyan-500/25 shadow-[0_0_15px_rgba(6,182,212,0.12)] backdrop-blur-md text-xs font-mono transition-all hover:border-cyan-400/50 hover:shadow-[0_0_20px_rgba(6,182,212,0.2)]"
            >
              {/* CPU Compute Telemetry */}
              <div
                className="flex items-center gap-1.5 cursor-pointer group"
                title={`CPU Compute Load: ${systemMetrics.cpu}%`}
              >
                <Cpu
                  size={13}
                  className={`transition-colors ${
                    systemMetrics.cpu > 80
                      ? "text-rose-400 animate-pulse"
                      : systemMetrics.cpu > 60
                      ? "text-amber-400"
                      : "text-cyan-400"
                  }`}
                />
                <div className="flex items-baseline gap-1">
                  <span className="text-[10px] text-slate-400 group-hover:text-slate-300 font-semibold tracking-wider">CPU</span>
                  <span
                    className={`font-bold ${
                      systemMetrics.cpu > 80
                        ? "text-rose-400"
                        : systemMetrics.cpu > 60
                        ? "text-amber-300"
                        : "text-white"
                    }`}
                  >
                    {systemMetrics.cpu !== undefined ? `${Math.round(systemMetrics.cpu)}%` : "--%"}
                  </span>
                </div>
              </div>

              {/* Cyber Divider */}
              <div className="w-[1px] h-3 bg-cyan-500/25" />

              {/* RAM Memory Telemetry */}
              <div
                className="flex items-center gap-1.5 cursor-pointer group"
                title={`RAM Allocation: ${systemMetrics.ram}% (${systemMetrics.ramUsed}GB / ${systemMetrics.ramTotal}GB)`}
              >
                <BrainCircuit
                  size={13}
                  className={`transition-colors ${
                    systemMetrics.ram > 85
                      ? "text-rose-400 animate-pulse"
                      : systemMetrics.ram > 70
                      ? "text-amber-400"
                      : "text-emerald-400"
                  }`}
                />
                <div className="flex items-baseline gap-1">
                  <span className="text-[10px] text-slate-400 group-hover:text-slate-300 font-semibold tracking-wider">RAM</span>
                  <span
                    className={`font-bold ${
                      systemMetrics.ram > 85
                        ? "text-rose-400"
                        : systemMetrics.ram > 70
                        ? "text-amber-300"
                        : "text-white"
                    }`}
                  >
                    {systemMetrics.ram !== undefined ? `${Math.round(systemMetrics.ram)}%` : "--%"}
                  </span>
                </div>
              </div>

              {/* Cyber Divider */}
              <div className="w-[1px] h-3 bg-cyan-500/25" />

              {/* Battery Telemetry */}
              <div
                className="flex items-center gap-1.5 cursor-pointer group"
                title={isCharging ? "Power Connected - Charging" : `Battery: ${batteryLevel !== null ? `${batteryLevel}%` : "Offline"}`}
              >
                <div className="relative flex items-center">
                  <BatteryMedium
                    size={14}
                    className={
                      isCharging
                        ? "text-amber-400"
                        : batteryLevel !== null && batteryLevel <= 20
                        ? "text-rose-400 animate-pulse"
                        : "text-emerald-400"
                    }
                  />
                  {isCharging && (
                    <Zap size={9} className="absolute -top-1 -right-1 text-amber-300 fill-amber-300 animate-bounce" />
                  )}
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-[10px] text-slate-400 group-hover:text-slate-300 font-semibold tracking-wider">BAT</span>
                  <span
                    className={`font-bold ${
                      isCharging
                        ? "text-amber-300"
                        : batteryLevel !== null && batteryLevel <= 20
                        ? "text-rose-400"
                        : "text-white"
                    }`}
                  >
                    {batteryLevel !== null ? `${batteryLevel}%` : "--%"}
                  </span>
                  {isCharging && (
                    <span className="text-[8px] text-amber-400 font-bold tracking-widest ml-0.5">CHG</span>
                  )}
                </div>
              </div>
            </div>

            {/* Subtle Live Clock with System Date Stacked Directly Below */}
            <div className="flex flex-col items-end text-right justify-center shrink-0">
              <div className="flex items-center gap-1.5 text-xs font-mono text-slate-200 leading-tight">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_6px_#34d399]" />
                <span className="font-bold text-white tracking-wider">{time || "--:--:--"}</span>
              </div>
              <span className="text-[9px] font-mono text-cyan-400/80 font-medium tracking-tight mt-0.5">
                {date || "System Date"}
              </span>
            </div>

            {/* Minimal Creator Avatar Button */}
            <button
              onClick={() => setShowVaultModal(true)}
              className="flex items-center gap-2 pl-1.5 pr-3 py-1 rounded-full bg-[#07132B]/80 border border-cyan-500/25 hover:border-cyan-400/60 hover:shadow-[0_0_12px_rgba(6,182,212,0.25)] transition-all cursor-pointer group"
              title="Open Master Creator Digital Dossier"
            >
              <div className="w-6 h-6 rounded-full overflow-hidden border border-cyan-400/60 bg-cyan-900/40 flex items-center justify-center shrink-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={dossier?.personal?.avatar_url || "https://github.com/AkmalDoghar.png"}
                  alt="Akmal"
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              </div>
              <span className="text-xs font-medium text-slate-200 group-hover:text-cyan-300 transition-colors">
                {dossier?.personal?.preferred_name || "Akmal"}
              </span>
              <ShieldCheck size={13} className="text-emerald-400 shrink-0" />
            </button>
          </div>
        </header>

        {/* Floating Futuristic Toast Notice */}
        {voiceNotice && (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 bg-[#09152C]/95 border border-cyan-400/60 text-cyan-100 px-5 py-2 rounded-full text-xs font-mono shadow-[0_0_25px_rgba(6,182,212,0.5)] backdrop-blur-xl flex items-center gap-2.5 animate-in fade-in slide-in-from-top-3">
            <Sparkles size={14} className="text-cyan-300 animate-spin" />
            <span>{voiceNotice}</span>
          </div>
        )}

        {/* ==================== 2. WORKSPACE LAYOUT (OPTION A: HUD DUAL-ZONE) ==================== */}
        <div className="flex-1 flex flex-col lg:flex-row p-3.5 gap-3.5 overflow-hidden relative z-10 min-h-0">
          
          {/* COLUMN 1: ULTRA-SLEEK TACTICAL SIDEBAR (~250px) */}
          <div className="w-full lg:w-[245px] xl:w-[255px] shrink-0 h-full flex flex-col overflow-hidden">
            <Sidebar
              dossier={dossier}
              isVaultUnlocked={true}
              onOpenDossier={() => setShowVaultModal(true)}
              onPreviewVoice={previewVoice}
              isSpeaking={isSpeaking}
              isListening={isListening}
              isWakeWordEnabled={isWakeWordEnabled}
              isContinuousConversation={isContinuousConversation}
              onToggleWakeWord={toggleWakeWord}
              onToggleContinuous={toggleContinuousConversation}
              systemMetrics={systemMetrics}
              activeTimersCount={activeTimers.length + activeAlarms.length + activeReminders.length}
              onOpenTimerCreator={() => {
                openHudModal("timers");
                setShowTimerCreator(true);
              }}
              onFocusChatInput={() => {
                const el = document.getElementById("jarvis-chat-input");
                el?.focus();
              }}
              className="w-full h-full rounded-3xl cyber-glass border border-cyan-500/25 shadow-[0_8px_35px_rgba(0,0,0,0.5)] overflow-hidden"
              collapsible={false}
            />
          </div>

          {/* COLUMN 2: CENTER HERO — HOLOGRAPHIC ARC REACTOR & HUD MODULE LAUNCHERS */}
          <div className="w-full lg:flex-[1] xl:flex-[1] min-w-[340px] max-w-[560px] h-full flex flex-col gap-3.5 overflow-hidden min-h-0">
            {/* Center Hero: Pure Tony Stark Holographic Arc Reactor Stage */}
            <div
              id="jarvis-orb-stage"
              className="flex-1 flex items-center justify-center overflow-hidden py-4 rounded-3xl cyber-glass border border-cyan-500/25 shadow-[0_8px_35px_rgba(0,0,0,0.5)] bg-gradient-to-b from-[#08152E]/60 via-[#040A18]/80 to-[#020610]/95 min-h-[320px]"
            >
              <div
                id="jarvis-orb-trigger"
                className="z-10 cursor-pointer"
              >
                <JarvisOrb
                  status={orbStatus}
                  size="lg"
                  userName={dossier?.personal?.preferred_name || "Sir"}
                  caption={inputValue.trim() ? inputValue : undefined}
                  onClick={handleOrbClick}
                />
              </div>
            </div>

            {/* Tactical Subsystems Control Dock (Multi-Phase Launch Matrix) */}
            <div className="shrink-0 rounded-2xl cyber-glass border border-cyan-500/25 p-2 bg-gradient-to-b from-[#08132A]/90 via-[#040A18]/95 to-[#020510]/98 shadow-[0_4px_25px_rgba(0,0,0,0.5)] flex flex-col gap-1.5">
              {/* Micro Status Bar */}
              <div className="flex items-center justify-between px-1 text-[10px] font-mono">
                <div className="flex items-center gap-1.5 text-cyan-300">
                  <Sparkles size={11} className="text-cyan-400 animate-pulse" />
                  <span className="font-hud tracking-wider font-bold text-[9px] sm:text-[10px]">
                    TACTICAL SUBSYSTEMS MATRIX
                  </span>
                </div>
                <span className="text-slate-400 text-[9px]">
                  MULTI-PHASE CONTROLS
                </span>
              </div>

              {/* Row 1: Core Operational Subsystems */}
              <div className="grid grid-cols-3 gap-1.5 text-xs font-mono">
                {/* 1. Memory */}
                <button
                  onClick={() => openHudModal("memory")}
                  className="py-1.5 px-2 rounded-xl bg-[#061024]/80 hover:bg-[#0d1a38] border border-purple-500/30 hover:border-purple-400/70 text-slate-300 hover:text-purple-200 flex items-center justify-center gap-1.5 transition-all cursor-pointer group shadow-sm"
                  title="Open Neural Memory Matrix"
                >
                  <BrainCircuit size={13} className="text-purple-400 group-hover:scale-110 transition-transform shrink-0" />
                  <span className="font-semibold truncate">Memory</span>
                </button>

                {/* 2. Timers */}
                <button
                  onClick={() => openHudModal("timers")}
                  className="py-1.5 px-2 rounded-xl bg-[#061024]/80 hover:bg-[#0d1a38] border border-amber-500/30 hover:border-amber-400/70 text-slate-300 hover:text-amber-200 flex items-center justify-center gap-1.5 transition-all cursor-pointer group shadow-sm"
                  title="Open Chrono Hub (Timers & Alarms)"
                >
                  <Timer size={13} className="text-amber-400 group-hover:scale-110 transition-transform shrink-0" />
                  <span className="font-semibold truncate">Timers</span>
                  {(activeTimers.length + activeAlarms.length + activeReminders.length) > 0 && (
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping shrink-0" />
                  )}
                </button>

                {/* 3. System */}
                <button
                  onClick={() => openHudModal("system")}
                  className="py-1.5 px-2 rounded-xl bg-[#061024]/80 hover:bg-[#0d1a38] border border-cyan-500/30 hover:border-cyan-400/70 text-slate-300 hover:text-cyan-200 flex items-center justify-center gap-1.5 transition-all cursor-pointer group shadow-sm"
                  title="Open Hardware Diagnostics"
                >
                  <Cpu size={13} className="text-cyan-400 group-hover:scale-110 transition-transform shrink-0" />
                  <span className="font-semibold truncate">System</span>
                  <span className="text-[10px] text-cyan-400/80 font-mono hidden xl:inline shrink-0">{systemMetrics.cpu}%</span>
                </button>
              </div>

              {/* Row 2: Advanced Phases & Master HUD */}
              <div className="grid grid-cols-3 gap-1.5 text-xs font-mono">
                {/* 4. Desktop Vision (Phase 7) */}
                <button
                  onClick={() => openHudModal("vision")}
                  className="py-1.5 px-2 rounded-xl bg-[#061024]/80 hover:bg-[#0d1a38] border border-emerald-500/30 hover:border-emerald-400/70 text-slate-300 hover:text-emerald-200 flex items-center justify-center gap-1.5 transition-all cursor-pointer group shadow-sm"
                  title="Open Phase 7 Desktop Vision Diagnostics"
                >
                  <Eye size={13} className="text-emerald-400 group-hover:scale-110 transition-transform shrink-0" />
                  <span className="font-semibold truncate">Vision AI</span>
                </button>

                {/* 5. Autonomous Coding Agent (Phase 8) */}
                <button
                  onClick={() => openHudModal("agent")}
                  className="py-1.5 px-2 rounded-xl bg-[#061024]/80 hover:bg-[#0d1a38] border border-rose-500/30 hover:border-rose-400/70 text-slate-300 hover:text-rose-200 flex items-center justify-center gap-1.5 transition-all cursor-pointer group shadow-sm"
                  title="Open Phase 8 Autonomous Agent Mission Control"
                >
                  <Bot size={13} className="text-rose-400 group-hover:scale-110 transition-transform shrink-0" />
                  <span className="font-semibold truncate">Auto Agent</span>
                </button>

                {/* 6. All Systems Master HUD */}
                <button
                  onClick={() => openHudModal("all")}
                  className="py-1.5 px-2 rounded-xl bg-[#061024]/80 hover:bg-[#0d1a38] border border-blue-500/30 hover:border-blue-400/70 text-slate-300 hover:text-blue-200 flex items-center justify-center gap-1.5 transition-all cursor-pointer group shadow-sm"
                  title="Open Complete Command HUD"
                >
                  <Layers size={13} className="text-blue-400 group-hover:scale-110 transition-transform shrink-0" />
                  <span className="font-semibold truncate">All HUD</span>
                </button>
              </div>
            </div>
          </div>

          {/* COLUMN 3: RIGHT DEDICATED FULL-HEIGHT CONVERSATION BOX */}
          <div className="flex-1 xl:flex-[1.2] min-w-[380px] h-full flex flex-col overflow-hidden min-h-0">
            {/* Tactical Command Console & Conversation Stream */}
            <div className="flex-1 h-full rounded-3xl cyber-glass flex flex-col overflow-hidden shadow-[0_8px_35px_rgba(0,0,0,0.5)] border border-cyan-500/25 min-h-0">
              {/* Mission Log Header */}
              <div className="px-5 py-3 border-b border-cyan-500/20 flex items-center justify-between bg-[#061024]/80 shrink-0">
                <div className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                  <MessageSquare size={15} className="text-cyan-400" />
                  <span className="font-hud text-xs font-bold text-white tracking-wider">
                    Tactical Mission Log
                  </span>
                  <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/40">
                    REAL-TIME STREAM
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {messages.length > 0 && (
                    <button
                      onClick={() => setMessages([])}
                      className="text-slate-400 hover:text-rose-400 text-[10px] font-mono flex items-center gap-1 transition-colors cursor-pointer"
                      title="Clear console feed"
                    >
                      <Trash2 size={12} />
                      <span>Clear Log</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Messages Container */}
              <div
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar min-h-0"
              >
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 gap-3 py-8">
                    <div className="w-14 h-14 rounded-2xl bg-cyan-500/15 border border-cyan-400/40 flex items-center justify-center text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.3)]">
                      <BrainCircuit size={28} />
                    </div>
                    <span className="font-hud text-sm font-bold text-white tracking-wider">
                      J.A.R.V.I.S Neural Stream Armed &amp; Ready
                    </span>
                    <span className="text-xs text-slate-400 max-w-md leading-relaxed">
                      Aap voice ya text ke zariye sawal pooch saktay hain, system diagnostic run karwa saktay hain, files manage kar saktay hain, aur automation tasks execute karwa saktay hain.
                    </span>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex flex-col gap-1.5 ${msg.sender === "user" ? "items-end" : "items-start"}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-lg ${
                          msg.sender === "user"
                            ? "bg-[#08152E]/95 from-cyan-600 via-blue-600 to-indigo-600 text-white rounded-br-none border border-cyan-400/40 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                            : "bg-[#08152E]/95 border border-cyan-500/35 text-slate-100 rounded-bl-none shadow-[0_0_20px_rgba(6,182,212,0.12)]"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-4 mb-1.5 pb-1.5 border-b border-white/10 text-[9px] font-mono opacity-85">
                          <span className="font-bold uppercase tracking-wider text-cyan-300">
                            {msg.sender === "user" ? "AK" : "JARVIS"}
                          </span>
                          <div className="flex items-center gap-2">
                            <span>{msg.time}</span>
                            <button
                              type="button"
                              onClick={() => handleCopyText(msg.text, msg.id)}
                              className="p-1 rounded hover:bg-white/15 text-slate-400 hover:text-cyan-300 transition-all cursor-pointer flex items-center gap-1 group/copy"
                              title="Copy message to clipboard"
                            >
                              {copiedMessageId === msg.id ? (
                                <span className="flex items-center gap-1 text-emerald-400 font-bold">
                                  <Check size={11} />
                                  <span className="text-[8px] uppercase">Copied</span>
                                </span>
                              ) : (
                                <Copy size={11} className="group-hover/copy:scale-110 transition-transform" />
                              )}
                            </button>
                          </div>
                        </div>
                        <div className="whitespace-pre-wrap selection:bg-cyan-500/40 font-sans">
                          {msg.text}
                        </div>
                      </div>

                      {/* Proactive Follow-up Suggestion Chips */}
                      {msg.sender === "jarvis" && msg.suggestions && msg.suggestions.length > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap pt-1 pl-1">
                          {msg.suggestions.map((sug, i) => (
                            <button
                              key={i}
                              onClick={() => handleSend(undefined, sug)}
                              className="text-[10px] font-mono font-medium px-2.5 py-1 rounded-xl bg-[#09152B] hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/40 transition-all cursor-pointer shadow-sm hover:scale-[1.02]"
                            >
                              💡 {sug}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}

                {loading && (
                  <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-[#08152E]/90 border border-cyan-400/40 text-xs text-cyan-300 w-fit shadow-[0_0_15px_rgba(6,182,212,0.25)] animate-pulse">
                    <Sparkles size={16} className="animate-spin text-cyan-400" />
                    <span className="font-mono">Neural heuristics reasoning &amp; tool execution in progress...</span>
                  </div>
                )}
              </div>

              {/* Chat Command Input Bar */}
              <form
                onSubmit={handleSend}
                className="p-3.5 border-t border-cyan-500/20 bg-[#061024]/90 flex items-center gap-2.5 shrink-0"
              >
                <button
                  type="button"
                  onClick={toggleListen}
                  disabled={loading}
                  className={`p-3 rounded-2xl border transition-all cursor-pointer ${
                    isListening
                      ? "bg-rose-500 text-white border-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.5)] animate-pulse"
                      : "bg-[#09152B] text-cyan-300 border-cyan-500/35 hover:border-cyan-400 hover:bg-cyan-500/20 shadow-sm"
                  }`}
                  title="Toggle Microphone"
                >
                  <Mic size={17} />
                </button>

                <input
                  id="jarvis-chat-input"
                  type="text"
                  placeholder="Ask JARVIS or enter tactical command (Roman Urdu / English)..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={loading}
                  className="flex-1 bg-[#09152C] border border-cyan-500/30 rounded-2xl px-5 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:shadow-[0_0_15px_rgba(6,182,212,0.25)] shadow-inner font-sans"
                />

                <button
                  type="submit"
                  disabled={loading || !inputValue.trim()}
                  className="px-5 py-3 rounded-2xl bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-40 text-white font-bold text-xs font-mono flex items-center gap-2 transition-all cursor-pointer shadow-[0_0_15px_rgba(6,182,212,0.35)]"
                >
                  <Send size={14} />
                  <span>Execute</span>
                </button>
              </form>
            </div>
          </div>
        </div>

      {/* Security Confirmation Dialog Modal (Phase 3 High Risk PIN Gate) */}
      {pendingAction && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xl flex items-center justify-center p-4">
          <div className="bg-[#0B132B] border border-rose-500/60 rounded-3xl max-w-md w-full p-6 shadow-[0_0_60px_rgba(244,63,94,0.4)] flex flex-col gap-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.4)]">
                <ShieldAlert size={24} />
              </div>
              <div className="flex flex-col">
                <span className="font-hud text-white font-bold text-sm tracking-wider">
                  Security Clearance Required
                </span>
                <span className="text-[10px] font-mono text-rose-400">
                  Tool: {pendingAction.toolName} • High Risk
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed bg-[#070D1B] p-3.5 rounded-2xl border border-rose-500/25 font-sans">
              {pendingAction.description}
            </p>

            {pendingAction.requiresPin && (
              <div className="flex flex-col gap-2">
                <label className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                  <KeyRound size={13} className="text-rose-400" />
                  <span>Enter Security PIN to authorize:</span>
                </label>
                <input
                  type="password"
                  maxLength={6}
                  placeholder="PIN"
                  value={pinInput}
                  onChange={(e) => setPinInput(e.target.value)}
                  className="bg-[#070D1B] border border-rose-500/50 rounded-2xl px-4 py-2.5 text-center text-sm font-mono tracking-widest text-white focus:outline-none focus:border-rose-400 shadow-inner"
                  autoFocus
                />
              </div>
            )}

            <div className="flex items-center justify-end gap-2.5 pt-2.5 border-t border-slate-800">
              <button
                onClick={handleCancelAction}
                disabled={confirmingAction}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono font-semibold cursor-pointer"
              >
                Deny &amp; Cancel
              </button>
              <button
                onClick={handleConfirmAction}
                disabled={confirmingAction || (pendingAction.requiresPin && !pinInput)}
                className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-mono font-bold shadow-[0_0_20px_rgba(244,63,94,0.45)] cursor-pointer disabled:opacity-50"
              >
                {confirmingAction ? "Verifying..." : "Authorize & Execute"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tactical HUD Subsystems Modal Popup (Phase 6B, 3C, System) */}
      <HudModuleModal
        isOpen={isHudModalOpen}
        onClose={() => setIsHudModalOpen(false)}
        activeTab={activeDockTab}
        onTabChange={(tab) => setActiveDockTab(tab)}
        activeTimers={activeTimers}
        activeAlarms={activeAlarms}
        activeReminders={activeReminders}
        currentTimeSec={currentTimeSec}
        formatSecondsToClock={formatSecondsToClock}
        handleCancelItem={handleCancelItem}
        handleLaunchPreset={handleLaunchPreset}
        showTimerCreator={showTimerCreator}
        setShowTimerCreator={setShowTimerCreator}
        creatorTab={creatorTab}
        setCreatorTab={setCreatorTab}
        customLabel={customLabel}
        setCustomLabel={setCustomLabel}
        customHours={customHours}
        setCustomHours={setCustomHours}
        customMinutes={customMinutes}
        setCustomMinutes={setCustomMinutes}
        customSeconds={customSeconds}
        setCustomSeconds={setCustomSeconds}
        handleCreateCustomTimer={handleCreateCustomTimer}
        alarmTimeInput={alarmTimeInput}
        setAlarmTimeInput={setAlarmTimeInput}
        handleCreateCustomAlarm={handleCreateCustomAlarm}
        reminderTextInput={reminderTextInput}
        setReminderTextInput={setReminderTextInput}
        reminderWhenInput={reminderWhenInput}
        setReminderWhenInput={setReminderWhenInput}
        handleCreateCustomReminder={handleCreateCustomReminder}
        creatingTimer={creatingTimer}
        systemMetrics={systemMetrics}
        isCharging={isCharging}
        batteryLevel={batteryLevel}
      />

      {/* Creator Digital Dossier Modal (Phase 6A) */}
      <CreatorDossierModal
        isOpen={showVaultModal}
        onClose={() => setShowVaultModal(false)}
        dossier={dossier}
        onSync={handleSyncOnlineFootprint}
        isSyncing={isSyncingDossier}
        onSave={handleSaveDossier}
        showNotice={showNotice}
      />
    </main>
  );
}