# ⚡ JARVIS AI ASSISTANT

**Next-Generation Autonomous Personal AI Operating System for Windows**  
Designed, Architected & Created for **Muhammad Akmal (Akmal bhai)**.

---

## 🌟 Overview

**JARVIS** is an autonomous desktop and web AI agent built for Windows. Inspired by the vision of a practical personal operating assistant, JARVIS executes commands, automates development workflows, controls the operating system safely, browses the web, verifies biometric speaker identity, and communicates in natural Roman Urdu and English.

---

## 🚀 Key Features

### 1. 🧬 Creator Digital Dossier & Holographic Hub
- **Open Identity Matrix:** Complete real-time awareness of creator profile (Full Name: *Muhammad Akmal*, Title, Bio, Location).
- **Public Satellite Coordinates:** Live integration with GitHub ([@AkmalDoghar](https://github.com/AkmalDoghar)), LinkedIn, Portfolio ([akmalcode.vercel.app](https://akmalcode.vercel.app)), and Instagram.
- **Automated Live Footprint Scraper:** Live GitHub scraper fetching recent public repositories, stargazers, languages, and followers.
- **Live Avatar Profile Picture:** Instant sync with GitHub CDN (`https://github.com/AkmalDoghar.png`) plus custom URL support with live thumbnail preview.
- **High-Security PIN Gate:** Protected by Salted PBKDF2 SHA-256 PIN authentication with **immediate auto-lock** upon modal close.

### 2. 🛡️ Voice Biometrics & Security Engine
- **48-Dimensional Speaker Verification:** Audio feature extraction (MFCCs, spectral centroid, spectral rolloff, zero-crossing rate) computing cosine similarity against enrolled creator voiceprints.
- **Unauthorized Speaker Shield:** Commands from unregistered speakers are blocked (`403 Forbidden`) with an audible defense alert.
- **Three-Tier Risk Architecture:**
  - **LOW Risk:** Volume, status, read-only system information.
  - **MEDIUM Risk:** File edits, app launching, lock/sleep.
  - **HIGH Risk:** File/folder deletion, system shutdown/restart, external messages — requires explicit confirmation + PIN.
- **Enrolled Voice Control:** Live status radar, enrollment sample counter, and single-click voiceprint reset.

### 3. 🎙️ Edge-TTS Neural Voice (100% Free & Lifelike)
- **Zero API Key Requirement:** Powered by Microsoft Edge-TTS neural cloud engines.
- **Roman Urdu & Hindi Phonetic Engine:** Automated Nastaliq transliteration passing phonetic Urdu to `ur-PK-AsadNeural` for realistic Pakistani male cadence.
- **Deep English Neural Cadence:** Natural, commanding male voice via `en-US-ChristopherNeural`.
- **Zero-Latency In-Memory Playback:** Local caching and fallback to pyttsx3.

### 4. 💻 Developer & System Tooling
- **Files & Code (Phase 4):** Reads projects, creates files, shows unified diffs before writing, runs tests, inspects git status.
- **Web Intelligence (Phase 5):** Real-time web search (DuckDuckGo), live weather forecasts, safe webpage scraper with prompt-injection defense.
- **System Controls (Phase 3):** App launcher/closer, volume/media keys, clipboard control, power options (lock, sleep, restart, shutdown).
- **Time Engine (Phase 3C):** Background timers, alarms, and persistent reminders.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide React, Framer Motion |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Requests, WebSockets |
| **Voice & Speech** | Edge-TTS (`ur-PK-AsadNeural`, `en-US-ChristopherNeural`), SpeechRecognition, PyAudio, SoundFile, NumPy, SciPy |
| **Security** | Salted PBKDF2 SHA-256, Cosine Similarity Voiceprints, Path Traversal Allowlist |
| **Data & Storage** | Local JSON Store (`creator_dossier.json`, `voiceprint.json`), SQLite |

---

## 🚦 How to Run JARVIS

### Quick Launch (Recommended)
Double-click the root batch script:
```cmd
start_jarvis.bat
```
or to start both frontend and backend concurrently:
```cmd
start_jarvis_all.bat
```

### Manual Execution

#### 1. Backend Server
```bash
# Activate virtual environment
.venv\Scripts\activate

# Launch FastAPI server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Dashboard
```bash
cd frontend
npm run dev
```
Navigate to `http://localhost:3000` in your browser.

---

## 🗺️ Roadmap & Development Phases

- [x] **Phase 0:** Environment Setup (Python 3.11, Node, .venv)
- [x] **Phase 1 & 1.5:** AI Core & Futuristic Desktop Dashboard
- [x] **Phase 2 & 2+:** Voice Interaction, Biometric Speaker Verification & Edge-TTS Neural Voice
- [x] **Phase 3:** Security Foundation (Risk Engine, PIN Gate) + Computer Controls
- [x] **Phase 4:** Files, Code Inspection, Diffs & Development Tools
- [x] **Phase 5:** Web Intelligence & Live Weather Forecaster
- [x] **Phase 6A:** Creator Digital Dossier, Online Footprint & Profile Picture
- [x] **Phase 6B:** Persistent Episodic & Project Long-Term Memory Matrix (Local SQLite, Privacy Guard, Contextual Recall)
- [x] **Phase 10A:** Hands-Free Wake Word Engine (`"Hey JARVIS"` / `"Suno JARVIS"`)
- [x] **Phase 10B:** Continuous Dialogue & Open Mic Conversation Mode (Wake-word free continuous speech)
- [x] **Phase 7:** Desktop Vision & Screenshot Error Diagnostics (High-speed capture, Multimodal Vision AI, Bug Diagnostics, Prompt Injection Defense)
- [x] **Phase 8:** Developer Workstation & Autonomous Web Execution (Direct VS Code Project Opener, Live Browser Runner, Local HTTP Dev Server, Terminal Launcher)
- [x] **Phase 9 & 10:** Windows Desktop Integration & System Packaging (Native System Tray Arc Reactor, Global Hotkey `Ctrl + Space`, Windows Startup Registry Autorun, WScript Silent Launcher)
- [x] **Phase 11:** Offline & Hybrid Fallback Engine (Real-Time Network Heartbeat, Local Ollama / LM Studio Discovery, Deterministic Offline System Rules, Offline STT Fallback & HUD Network Badge)

---

## 🔒 Security Policy
- The backend listens **strictly on `127.0.0.1`** (localhost only) with CORS restricted to local frontend origins.
- Sensitive credentials, PINs, and hashes are never exposed to the client or written to version control.
- Critical system destructive actions strictly enforce dual-factor verification (User Confirmation + Master PIN).

---

## 👤 Master Creator
**Muhammad Akmal (Akmal bhai)**  
- Portfolio: [akmalcode.vercel.app](https://akmalcode.vercel.app)  
- GitHub: [@AkmalDoghar](https://github.com/AkmalDoghar)  
- LinkedIn: [linkedin.com/in/muhammad-akmal-dev](https://linkedin.com/in/muhammad-akmal-dev/)
