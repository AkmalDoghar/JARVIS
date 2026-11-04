import os
from typing import List, Dict, Literal, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import speech_recognition as sr

from backend.agent.brain import JarvisBrain
from backend.voice.speech_to_text import is_available as voice_input_available
from backend.voice.speech_to_text import listen, enroll_from_mic, UnauthorizedSpeakerError
from backend.security.voiceprint import get_voiceprint_status, reset_voiceprint

load_dotenv()

app = FastAPI(
    title="JARVIS AI Assistant",
    description="Backend API for JARVIS Personal AI Agent",
    version="1.0.0"
)

# Enable CORS for local development (e.g. Next.js frontend on localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

brain = JarvisBrain()

class ChatRequest(BaseModel):
    prompt: str = Field(..., description="User input message or prompt")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="Conversation history list")
    response_language: Literal["en", "ur", "hi", "auto"] = Field(
        default="auto",
        description="Language JARVIS must use for its response: English, Urdu, Hindi, or auto",
    )

class ChatResponse(BaseModel):
    response: str
    spoken_response: Optional[str] = None
    status: str
    model: str
    provider: str
    tool_executed: Optional[str] = None
    requires_pin: Optional[bool] = False
    confirmation_id: Optional[str] = None
    suggestions: Optional[List[str]] = Field(default_factory=list)

class VoiceInputResponse(BaseModel):
    transcript: str
    status: str = "success"

class SpeakRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "JARVIS AI Assistant",
        "version": "1.0.0",
        "message": "JARVIS core backend is active and ready."
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "phase": "Phase 1 - AI Core",
        "brain_status": "ready",
        "voice_input_available": voice_input_available(),
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    result = brain.process_message(
        message=request.prompt,
        history=request.history,
        response_language=request.response_language,
    )
    return ChatResponse(
        response=result["response"],
        spoken_response=result.get("spoken_response"),
        status=result["status"],
        model=result["model"],
        provider=result["provider"],
        tool_executed=result.get("tool_executed"),
        requires_pin=result.get("requires_pin", False),
        confirmation_id=result.get("confirmation_id"),
        suggestions=result.get("suggestions", []),
    )

@app.post("/api/voice/listen", response_model=VoiceInputResponse)
def voice_listen(language: Literal["en-US", "en-GB", "ur-PK", "hi-IN", "en-IN"] = "ur-PK"):
    from backend.voice.text_to_speech import stop_speech
    # Barge-in: stop any running speech immediately when user starts listening
    stop_speech()
    try:
        transcript = listen(timeout=7, language=language)
        return VoiceInputResponse(transcript=transcript, status="success")
    except sr.WaitTimeoutError:
        return VoiceInputResponse(transcript="[Silence]", status="timeout")
    except sr.UnknownValueError:
        return VoiceInputResponse(transcript="[Unintelligible]", status="unrecognized")
    except sr.RequestError as error:
        raise HTTPException(
            status_code=503,
            detail="Google speech recognition is unavailable. Check the internet connection and try again.",
        ) from error
    except UnauthorizedSpeakerError as error:
        raise HTTPException(
            status_code=403,
            detail=f"Security Alert: Voice unrecognized. Access limited to Akmal bhai. ({error})",
        )
    except OSError as error:
        raise HTTPException(
            status_code=503,
            detail="The backend could not access a microphone. Check the Windows default input device.",
        ) from error

@app.post("/api/voice/speak")
def voice_speak(request: SpeakRequest):
    from backend.voice.text_to_speech import speak
    success = speak(request.text)
    if not success:
        raise HTTPException(status_code=500, detail="TTS Engine failed to synthesize speech")
    return {"status": "ok"}

@app.post("/api/voice/stop")
def voice_stop():
    from backend.voice.text_to_speech import stop_speech
    stop_speech()
    return {"status": "stopped"}

@app.get("/api/voice/biometrics/status")
def voice_biometrics_status():
    """Retrieve voiceprint enrollment and biometric security status."""
    return {"status": "success", "biometrics": get_voiceprint_status()}

@app.post("/api/voice/biometrics/enroll")
def voice_biometrics_enroll():
    """Record a voice sample from creator's microphone and update the voiceprint."""
    try:
        result = enroll_from_mic(timeout=5)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/biometrics/reset")
def voice_biometrics_reset():
    """Reset the stored voiceprint."""
    result = reset_voiceprint()
    return {"status": "success", "result": result}

# ─────────────────────────────────────────────
# Phase 10A: Hands-Free Wake Word Endpoints
# ─────────────────────────────────────────────
class WakeWordToggleRequest(BaseModel):
    enabled: bool
    chime: Optional[bool] = None
    sensitivity: Optional[str] = None

class WakeWordDetectRequest(BaseModel):
    text: str

@app.get("/api/voice/wake-word/status")
def voice_wake_word_status():
    """Retrieve Wake Word detection configuration and state."""
    from backend.voice.wake_word import get_wake_word_status
    return {"status": "success", "config": get_wake_word_status()}

@app.post("/api/voice/wake-word/toggle")
def voice_wake_word_toggle(request: WakeWordToggleRequest):
    """Enable or disable hands-free wake word listening."""
    from backend.voice.wake_word import set_wake_word_status
    cfg = set_wake_word_status(enabled=request.enabled, chime=request.chime, sensitivity=request.sensitivity)
    return {"status": "success", "config": cfg}

@app.post("/api/voice/wake-word/detect")
def voice_wake_word_detect(request: WakeWordDetectRequest):
    """Parse text/transcript for wake words and extract the subsequent command."""
    from backend.voice.wake_word import parse_wake_word
    parsed = parse_wake_word(request.text)
    return {"status": "success", "result": parsed}

class ConfirmActionRequest(BaseModel):
    confirmation_id: str
    pin: Optional[str] = None

class CancelActionRequest(BaseModel):
    confirmation_id: str

@app.get("/api/system/status")
def system_status():
    from backend.tools.system_control import get_system_status
    return get_system_status()

@app.get("/api/security/audit")
def security_audit(limit: int = 20):
    from backend.security.audit import get_recent_audit_logs
    return {"logs": get_recent_audit_logs(limit=limit)}

@app.post("/api/security/confirm")
def security_confirm(request: ConfirmActionRequest):
    from backend.security.confirmation import validate_and_consume_confirmation
    from backend.tools.registry import execute_tool

    valid, msg, req = validate_and_consume_confirmation(request.confirmation_id, request.pin)
    if not valid or not req:
        raise HTTPException(status_code=400, detail=msg)

    result = execute_tool(req["tool_name"], req["arguments"], confirmed=True, pin=request.pin)
    return {"status": "success", "result": result}

@app.post("/api/security/cancel")
def security_cancel(request: CancelActionRequest):
    from backend.security.confirmation import cancel_confirmation
    canceled = cancel_confirmation(request.confirmation_id)
    return {"status": "cancelled" if canceled else "not_found"}


# ─────────────────────────────────────────────
# Phase 3C: Timer, Alarm & Reminder Endpoints
# ─────────────────────────────────────────────
class TimerRequest(BaseModel):
    duration: Optional[str] = ""
    label: Optional[str] = ""
    seconds: Optional[int] = None

class AlarmRequest(BaseModel):
    alarm_time: str
    label: Optional[str] = ""

class ReminderRequest(BaseModel):
    message: str
    when: str

class CancelTimerRequest(BaseModel):
    timer_id: str

@app.post("/api/timers/set")
def api_set_timer(request: TimerRequest):
    from backend.tools.timers import set_timer
    return set_timer(duration=request.duration or "", label=request.label or "", seconds=request.seconds)

@app.post("/api/alarms/set")
def api_set_alarm(request: AlarmRequest):
    from backend.tools.timers import set_alarm
    return set_alarm(alarm_time=request.alarm_time, label=request.label or "")

@app.post("/api/reminders/set")
def api_set_reminder(request: ReminderRequest):
    from backend.tools.timers import set_reminder
    return set_reminder(message=request.message, when=request.when)

@app.get("/api/timers")
@app.get("/api/timers/list")
def api_list_all():
    from backend.tools.timers import get_all_active
    return get_all_active()

@app.post("/api/timers/cancel")
def api_cancel_timer(request: CancelTimerRequest):
    from backend.tools.timers import cancel_any
    return cancel_any(item_id=request.timer_id)


# ─────────────────────────────────────────────
# Creator Vault & Identity Endpoints (PIN Protected)
# ─────────────────────────────────────────────
class VaultUnlockRequest(BaseModel):
    pin: str

class VaultProfileUpdateRequest(BaseModel):
    pin: str
    name: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    email: Optional[str] = None
    tech_stack: Optional[str] = None

class VaultFetchEntriesRequest(BaseModel):
    pin: str
    category: Optional[str] = None
    status: Optional[str] = None

class VaultAddEntryRequest(BaseModel):
    pin: str
    category: str
    content: str
    title: Optional[str] = ""
    priority: Optional[str] = "medium"

class VaultEntryActionRequest(BaseModel):
    pin: str
    entry_id: int
    status: Optional[str] = None

@app.get("/api/vault/profile")
def api_get_vault_profile():
    """Retrieve creator profile information (public display)."""
    from backend.database.vault import get_creator_profile
    return {"status": "success", "profile": get_creator_profile()}

@app.post("/api/vault/unlock")
def api_vault_unlock(request: VaultUnlockRequest):
    """Verify security PIN to unlock Creator Vault access."""
    from backend.security.pin import verify_pin
    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)
    return {"status": "success", "message": "Creator Vault unlocked."}

@app.post("/api/vault/profile/update")
def api_update_vault_profile(request: VaultProfileUpdateRequest):
    """Update creator profile details (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import update_creator_profile

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    data = {k: v for k, v in request.dict().items() if k != "pin" and v is not None}
    updated = update_creator_profile(data)
    return {"status": "success", "profile": updated, "message": "Profile updated successfully."}

@app.post("/api/vault/entries")
def api_get_vault_entries(request: VaultFetchEntriesRequest):
    """Fetch private thoughts, goals, and notes (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import get_vault_entries

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    entries = get_vault_entries(category=request.category, status=request.status)
    return {"status": "success", "entries": entries}

@app.post("/api/vault/add")
def api_add_vault_entry(request: VaultAddEntryRequest):
    """Add a new private goal, thought, plan, or note (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import add_vault_entry

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    entry = add_vault_entry(
        category=request.category,
        content=request.content,
        title=request.title or "",
        priority=request.priority or "medium"
    )
    return {"status": "success", "entry": entry, "message": "Saved to Creator Vault."}

@app.post("/api/vault/entry/status")
def api_update_vault_entry_status(request: VaultEntryActionRequest):
    """Toggle status (active/completed) of a vault entry (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import update_vault_entry

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    updated = update_vault_entry(entry_id=request.entry_id, status=request.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Vault entry not found.")
    return {"status": "success", "entry": updated}

@app.post("/api/vault/entry/delete")
def api_delete_vault_entry(request: VaultEntryActionRequest):
    """Delete a vault entry (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import delete_vault_entry

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    success = delete_vault_entry(entry_id=request.entry_id)
    return {"status": "success" if success else "not_found"}


# ─────────────────────────────────────────────
# Projects Directory Endpoints
# ─────────────────────────────────────────────
class VaultAddProjectRequest(BaseModel):
    pin: str
    name: str
    path: str
    repo_url: Optional[str] = ""
    tech_stack: Optional[str] = ""
    status: Optional[str] = "active"

class VaultDeleteProjectRequest(BaseModel):
    pin: str
    project_id: int

@app.get("/api/vault/projects")
def api_get_vault_projects():
    """Retrieve registered developer projects."""
    from backend.database.vault import get_creator_projects
    return {"status": "success", "projects": get_creator_projects()}

@app.post("/api/vault/projects/add")
def api_add_vault_project(request: VaultAddProjectRequest):
    """Register a new developer project (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import add_creator_project

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    project = add_creator_project(
        name=request.name,
        path=request.path,
        repo_url=request.repo_url or "",
        tech_stack=request.tech_stack or "",
        status=request.status or "active"
    )
    return {"status": "success", "project": project, "message": "Project registered."}

@app.post("/api/vault/projects/delete")
def api_delete_vault_project(request: VaultDeleteProjectRequest):
    """Delete a registered project (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import delete_creator_project

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    success = delete_creator_project(request.project_id)
    return {"status": "success" if success else "not_found"}

class VaultOpenProjectRequest(BaseModel):
    project_name: str
    in_vscode: Optional[bool] = True

@app.post("/api/vault/projects/open")
def api_open_vault_project(request: VaultOpenProjectRequest):
    """Open a project in VS Code or Windows File Explorer."""
    from backend.tools.creator_tools import open_project
    res = open_project(project_name=request.project_name, in_vscode=request.in_vscode)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to open project."))
    return res


# ─────────────────────────────────────────────
# Daily Focus / Standup Endpoints
# ─────────────────────────────────────────────
class VaultAddFocusRequest(BaseModel):
    pin: str
    task: str

class VaultActionFocusRequest(BaseModel):
    pin: str
    task_id: int

@app.get("/api/vault/focus")
def api_get_vault_focus():
    """Retrieve today's priority focus tasks."""
    from backend.database.vault import get_daily_focus
    return {"status": "success", "tasks": get_daily_focus()}

@app.post("/api/vault/focus/add")
def api_add_vault_focus(request: VaultAddFocusRequest):
    """Add a task to Today's Focus (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import add_daily_focus

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    task = add_daily_focus(task=request.task)
    return {"status": "success", "task": task}

@app.post("/api/vault/focus/toggle")
def api_toggle_vault_focus(request: VaultActionFocusRequest):
    """Toggle completed state of a daily focus task (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import toggle_daily_focus

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    task = toggle_daily_focus(request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"status": "success", "task": task}

@app.post("/api/vault/focus/delete")
def api_delete_vault_focus(request: VaultActionFocusRequest):
    """Delete a task from daily focus (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import delete_daily_focus

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    success = delete_daily_focus(request.task_id)
    return {"status": "success" if success else "not_found"}


# ─────────────────────────────────────────────
# Backup Export Endpoint
# ─────────────────────────────────────────────
@app.post("/api/vault/export")
def api_export_vault_data(request: VaultUnlockRequest):
    """Export complete Creator Vault data (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import export_vault_data

# ─────────────────────────────────────────────
# Connected Accounts Endpoints
# ─────────────────────────────────────────────
class VaultAddAccountRequest(BaseModel):
    pin: str
    platform: str
    account_name: str
    handle: str
    profile_url: str
    content_theme: Optional[str] = ""
    audience: Optional[str] = ""
    api_key_or_token: Optional[str] = ""

class VaultSyncAccountRequest(BaseModel):
    platform: str

class VaultDeleteAccountRequest(BaseModel):
    pin: str
    account_id: int

@app.get("/api/vault/accounts")
def api_get_vault_accounts(platform: Optional[str] = None):
    """Retrieve all connected accounts or by platform."""
    from backend.database.vault import get_creator_accounts
    return {"status": "success", "accounts": get_creator_accounts(platform=platform)}

@app.post("/api/vault/accounts/add")
def api_add_vault_account(request: VaultAddAccountRequest):
    """Register or update a connected account in Creator Vault (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import add_or_update_creator_account

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    acc = add_or_update_creator_account(
        platform=request.platform,
        account_name=request.account_name,
        handle=request.handle,
        profile_url=request.profile_url,
        content_theme=request.content_theme or "",
        audience=request.audience or "",
        api_key_or_token=request.api_key_or_token or "",
    )
    return {"status": "success", "account": acc}

@app.post("/api/vault/accounts/sync")
def api_sync_vault_account(request: VaultSyncAccountRequest):
    """Inspect and live sync stats for an account."""
    from backend.tools.creator_tools import inspect_creator_account
    res = inspect_creator_account(request.platform)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to sync account."))
    return res

@app.post("/api/vault/accounts/delete")
def api_delete_vault_account(request: VaultDeleteAccountRequest):
    """Delete a connected account (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import delete_creator_account

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    success = delete_creator_account(request.account_id)
    return {"status": "success" if success else "not_found"}

# ─────────────────────────────────────────────
# Social Media Posts Endpoints
# ─────────────────────────────────────────────
class VaultAddSocialPostRequest(BaseModel):
    platform: str
    topic: str
    content_style: Optional[str] = "engaging"
    hashtags: Optional[str] = ""

class VaultPublishSocialPostRequest(BaseModel):
    platform: str
    content: str
    auto_open_browser: Optional[bool] = True

class VaultDeleteSocialPostRequest(BaseModel):
    pin: str
    post_id: int

@app.get("/api/vault/posts")
def api_get_vault_posts(platform: Optional[str] = None, status: Optional[str] = None):
    """Retrieve social media posts (drafts, published)."""
    from backend.database.vault import get_social_posts
    return {"status": "success", "posts": get_social_posts(platform=platform, status=status)}

@app.post("/api/vault/posts/add")
def api_add_vault_social_post(request: VaultAddSocialPostRequest):
    """Draft a new social post using AI creator tool."""
    from backend.tools.creator_tools import draft_social_post
    res = draft_social_post(
        platform=request.platform,
        topic=request.topic,
        content_style=request.content_style or "engaging",
        hashtags=request.hashtags or ""
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to draft post."))
    return res

@app.post("/api/vault/posts/publish")
def api_publish_vault_social_post(request: VaultPublishSocialPostRequest):
    """Publish/stage a social post (copies to clipboard and opens browser)."""
    from backend.tools.creator_tools import publish_social_post
    res = publish_social_post(
        platform=request.platform,
        content=request.content,
        auto_open_browser=request.auto_open_browser if request.auto_open_browser is not None else True
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to publish post."))
    return res

@app.post("/api/vault/posts/delete")
def api_delete_vault_social_post(request: VaultDeleteSocialPostRequest):
    """Delete a social post draft or record (PIN protected)."""
    from backend.security.pin import verify_pin
    from backend.database.vault import delete_social_post

    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    success = delete_social_post(request.post_id)
    return {"status": "success" if success else "not_found"}


# ─────────────────────────────────────────────
# Creator Digital Dossier & Online Presence Endpoints
# ─────────────────────────────────────────────
class DossierUpdateRequest(BaseModel):
    updates: Dict[str, Any]

class DossierSyncRequest(BaseModel):
    github_username: Optional[str] = None

@app.get("/api/dossier")
def api_get_dossier():
    """Retrieve full creator digital dossier (no PIN required for local dashboard view)."""
    from backend.database.creator_dossier import get_dossier
    return {"status": "success", "dossier": get_dossier()}

@app.post("/api/dossier/update")
def api_update_dossier(request: DossierUpdateRequest):
    """Update creator digital dossier."""
    from backend.database.creator_dossier import update_dossier
    updated = update_dossier(request.updates)
    return {"status": "success", "dossier": updated, "message": "Creator dossier updated."}

@app.post("/api/dossier/sync")
def api_sync_dossier(request: DossierSyncRequest):
    """Auto-sync creator's online presence, GitHub repos, and public footprint."""
    from backend.database.creator_dossier import sync_creator_online
    result = sync_creator_online(github_username=request.github_username)
    return {"status": "success" if result.get("success") else "error", "sync_result": result}


# ─────────────────────────────────────────────
# Phase 6B: Long-Term Memory Matrix Endpoints
# ─────────────────────────────────────────────
class MemoryCreateRequest(BaseModel):
    content: str
    category: Optional[str] = "preference"
    key: Optional[str] = None
    tags: Optional[List[str]] = None
    importance: Optional[int] = 1

@app.get("/api/memory")
def api_get_memories(category: Optional[str] = None, query: Optional[str] = None):
    """List or search stored memories in JARVIS's long-term memory matrix."""
    from backend.database import memory as memory_db
    if query:
        memories = memory_db.recall(query=query, category=category)
    elif category:
        memories = memory_db.recall(category=category, limit=100)
    else:
        memories = memory_db.get_all_memories()
    return {"status": "success", "count": len(memories), "memories": memories}

@app.post("/api/memory")
def api_save_memory(request: MemoryCreateRequest):
    """Save an instruction, habit, or preference into long-term memory."""
    from backend.database import memory as memory_db
    res = memory_db.remember(
        content=request.content,
        category=request.category or "preference",
        key=request.key,
        tags=request.tags,
        importance=request.importance or 1
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to store memory."))
    return {"status": "success", "memory": res}

@app.delete("/api/memory/{memory_id}")
def api_delete_memory(memory_id: int):
    """Delete a memory item by ID."""
    from backend.database import memory as memory_db
    success = memory_db.forget(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory #{memory_id} not found.")
    return {"status": "success", "message": f"Memory #{memory_id} deleted."}

class MemoryClearRequest(BaseModel):
    pin: str

@app.post("/api/memory/clear")
def api_clear_all_memories(request: MemoryClearRequest):
    """Forget all memories (requires PIN validation)."""
    from backend.security.pin import verify_pin
    from backend.database import memory as memory_db
    valid, msg = verify_pin(request.pin)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)
    count = memory_db.forget_all()
    return {"status": "success", "message": f"All {count} memories erased.", "count": count}


# ─────────────────────────────────────────────
# Phase 7: Desktop Vision & Screen Diagnostics
# ─────────────────────────────────────────────
class VisionInspectRequest(BaseModel):
    focus: Optional[str] = "general"
    question: Optional[str] = None
    save_screenshot: Optional[bool] = False
    save_path: Optional[str] = None

class VisionCaptureRequest(BaseModel):
    save_path: Optional[str] = None

@app.get("/api/vision/status")
def api_vision_status():
    """Check availability of vision models and screen capture capability."""
    from backend.tools import vision_tools
    client, provider, models = vision_tools.get_vision_llm_client()
    return {
        "status": "online" if client and models else "offline",
        "provider": provider,
        "models": models,
        "capture_engine": "Win32_GDI"
    }

@app.post("/api/vision/capture")
def api_vision_capture(request: VisionCaptureRequest):
    """Capture active desktop screen and return base64 image."""
    from backend.tools import vision_tools
    res = vision_tools.capture_desktop_screenshot(save_path=request.save_path)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to capture screen."))
    return res

@app.post("/api/vision/inspect")
def api_vision_inspect(request: VisionInspectRequest):
    """Capture screen and perform multimodal visual analysis / error diagnosis."""
    from backend.tools import vision_tools
    res = vision_tools.inspect_screen(
        focus=request.focus or "general",
        question=request.question,
        save_screenshot=bool(request.save_screenshot),
        save_path=request.save_path
    )
    if not res.get("success") and not res.get("offline"):
        raise HTTPException(status_code=500, detail=res.get("error", "Vision inspection failed."))
    return res


# ─────────────────────────────────────────────
# Phase 8: Autonomous Multi-Step Agent
# ─────────────────────────────────────────────
class AgentPlanRequest(BaseModel):
    goal: str
    template: Optional[str] = None
    context: Optional[str] = None

class AgentExecuteRequest(BaseModel):
    goal: Optional[str] = None
    template: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None

class AgentConfirmRequest(BaseModel):
    task_id: str
    pin: Optional[str] = None

class AgentStopRequest(BaseModel):
    task_id: Optional[str] = None

@app.get("/api/agent/status")
def api_agent_status():
    """Retrieve current autonomous plan execution status and live logs."""
    from backend.agent.executor import global_agent_executor
    return global_agent_executor.get_status()

@app.get("/api/agent/templates")
def api_agent_templates():
    """List available pre-configured autonomous engineering mission templates."""
    from backend.agent.planner import TEMPLATES
    return {
        "templates": [
            {
                "key": k,
                "title": v["title"],
                "description": v["description"],
                "steps_count": len(v["steps"])
            }
            for k, v in TEMPLATES.items()
        ]
    }

@app.post("/api/agent/plan")
def api_agent_plan(request: AgentPlanRequest):
    """Generate a structured multi-step execution plan for an autonomous goal."""
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty.")
    from backend.agent.planner import generate_plan
    plan = generate_plan(goal=request.goal, template_key=request.template, context=request.context)
    return {"status": "success", "plan": plan.to_dict()}

@app.post("/api/agent/execute")
def api_agent_execute(request: AgentExecuteRequest):
    """Start or resume execution of an autonomous mission."""
    from backend.agent.planner import generate_plan, TaskPlan
    from backend.agent.executor import global_agent_executor
    
    if request.plan:
        plan = TaskPlan.from_dict(request.plan)
    elif request.goal:
        plan = generate_plan(goal=request.goal, template_key=request.template)
    else:
        raise HTTPException(status_code=400, detail="Must provide either 'goal' or 'plan'.")
        
    res_plan = global_agent_executor.execute_plan(plan)
    return {"status": "success", "plan": res_plan.to_dict()}

@app.post("/api/agent/confirm")
def api_agent_confirm(request: AgentConfirmRequest):
    """Confirm a paused/gated step and resume execution."""
    from backend.agent.executor import global_agent_executor
    try:
        res_plan = global_agent_executor.confirm_step(task_id=request.task_id, pin=request.pin)
        return {"status": "success", "plan": res_plan.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/agent/stop")
def api_agent_stop(request: AgentStopRequest = None):
    """Emergency STOP: Halt any running autonomous mission immediately."""
    from backend.agent.executor import global_agent_executor
    res = global_agent_executor.stop_execution()
    return res


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)


