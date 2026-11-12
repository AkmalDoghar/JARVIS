"""
JARVIS Tool Registry & Function Calling Definitions
Phase 3A/3B Component: Schema definitions for LLM tool calling, risk validation, and audit dispatch.
"""

from typing import Dict, Any, List, Optional
from backend.security.risk import get_tool_risk, RiskLevel
from backend.security.pin import verify_pin
from backend.security.audit import log_tool_call
from backend.security.confirmation import create_confirmation_request
from backend.tools import system_control
from backend.tools import timers as timer_tools
from backend.tools import creator_tools
from backend.tools import code_tools
from backend.tools import web_tools
from backend.tools import memory_tools
from backend.tools import vision_tools
from backend.tools import chrome_bookmarks
from backend.tools import browser_agent

# Function Calling Tools Schemas for OpenAI / Groq / OpenRouter models
JARVIS_TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open any installed Windows application or software (e.g. 'github desktop', 'mongodb compass', 'whatsapp', 'chrome', 'vscode', 'android studio', 'calculator', 'paint', 'notepad').",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name or alias of the application to open (e.g. 'github desktop', 'mongodb compass', 'whatsapp', 'chrome','antigravity', 'vscode', 'calculator')."
                    },
                    "target_path": {
                        "type": "string",
                        "description": "Optional folder path, project path, or file to open inside the application (e.g. 'Desktop/CounterPage' for VS Code)."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Close running instances of any application or software (e.g. 'github desktop', 'mongodb compass', 'whatsapp', 'chrome', 'calculator'). If the user says 'close it' or 'ise band karo', pass the application name from recent context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The application to close (e.g. 'github desktop', 'mongodb compass', 'chrome', 'calculator')."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_folder",
            "description": "Open a folder in Windows File Explorer (e.g. 'projects', 'downloads', 'desktop', 'documents', or specific safe path).",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "The folder name, alias, or path to open in Explorer."
                    }
                },
                "required": ["folder_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_folder",
            "description": "Close an opened folder window or File Explorer tab/window (e.g. 'downloads', 'projects', 'desktop', or current open folder window).",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_name": {
                        "type": "string",
                        "description": "The name or alias of the folder window to close (e.g. 'downloads', 'documents', 'projects'). Optional."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_file",
            "description": "Open any document, PDF, image, video, code or text file on the computer. Automatically searches Desktop, Downloads, Documents, Projects folders if path is not specified.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name_or_path": {
                        "type": "string",
                        "description": "The file name or path to open (e.g. 'resume.pdf', 'notes.txt', 'screenshot.png', 'd:/projects/JARVIS/README.md')."
                    },
                    "app_name": {
                        "type": "string",
                        "description": "Optional application to open the file with (e.g. 'notepad', 'code', 'chrome', 'wordpad')."
                    }
                },
                "required": ["file_name_or_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a website or search URL in the user's default web browser. ALWAYS use this whenever the user asks to search on Google (e.g. 'search X on google', 'google per search karo', 'google open karo') or search on YouTube (e.g. 'youtube per search karo', 'search X on youtube'), or open any web page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The web address or Google/YouTube search URL to open in browser (e.g. 'https://www.google.com/search?q=jarvis', 'https://www.youtube.com/results?search_query=song', 'google.com', 'github.com')."
                    },
                    "inspect": {
                        "type": "boolean",
                        "description": "Optional: set to True if the user asks to inspect the page or open in developer mode / devtools.",
                        "default": False
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_in_vscode",
            "description": "Open any folder, project directory, or code file directly in Visual Studio Code (e.g. 'Desktop/CounterPage', 'D:/projects/JARVIS', 'Desktop/notes.txt'). Use this whenever the user asks to open something in VS Code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The folder path, project path, or file path to open in VS Code."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_file_in_browser",
            "description": "Open and run any local HTML file, web page, or web project in the default web browser (e.g. 'Desktop/CounterPage', 'Desktop/CounterPage/index.html'). Automatically finds index.html if a folder is provided. ALWAYS use this whenever the user asks to run or open an HTML page or web app in the browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The local file path or web project folder to run in browser."
                    },
                    "inspect": {
                        "type": "boolean",
                        "description": "Whether to launch with Developer Tools (Inspect mode) open (default false)."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_local_server",
            "description": "Start a lightweight local HTTP web server (http://localhost:<port>) for a project folder and optionally open it in the browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "The project folder to serve."
                    },
                    "port": {
                        "type": "integer",
                        "description": "Port number to host the server on (default 5500)."
                    },
                    "auto_open": {
                        "type": "boolean",
                        "description": "Whether to automatically open http://localhost:<port> in the browser (default true)."
                    }
                },
                "required": ["project_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_in_terminal",
            "description": "Open Windows Terminal or PowerShell at a specific project folder or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory or project folder path where the terminal should open."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Get current real-time hardware status metrics (CPU usage %, RAM usage %, Battery %, Disk free space).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_open_windows",
            "description": "List all active, visible applications and windows currently open on the computer desktop.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_volume",
            "description": "Control Windows system volume (mute, unmute, volume up, volume down, set exact percentage 0-100, or check current volume).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["mute", "unmute", "up", "down", "set", "get"],
                        "description": "Volume action to perform."
                    },
                    "level": {
                        "type": "integer",
                        "description": "Target volume percentage from 0 to 100 (e.g. 20, 50, 80). Optional for up/down."
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_brightness",
            "description": "Control screen brightness (increase, decrease, set percentage level 0-100, or check status).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["up", "down", "set", "get"],
                        "description": "Brightness action: 'up' (increase), 'down' (decrease), 'set' (exact level), or 'get' (check)."
                    },
                    "level": {
                        "type": "integer",
                        "description": "Target brightness percentage 0-100 (e.g. 50, 75, 100). Optional for up/down."
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_quick_setting",
            "description": "Control or open Windows quick settings: Wi-Fi, Bluetooth, Airplane mode, Night light, Display, Sound.",
            "parameters": {
                "type": "object",
                "properties": {
                    "setting_name": {
                        "type": "string",
                        "enum": ["wifi", "bluetooth", "airplane", "nightlight", "display", "sound"],
                        "description": "The setting to manage."
                    },
                    "action": {
                        "type": "string",
                        "enum": ["open", "status", "on", "off"],
                        "description": "Action: 'open' (open settings page), 'status' (check connection status), 'on' (enable), 'off' (disable)."
                    }
                },
                "required": ["setting_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lock_computer",
            "description": "Lock the Windows desktop session.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sleep_computer",
            "description": "Put the Windows computer into sleep mode.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_computer",
            "description": "Initiate computer shutdown with a countdown delay (HIGH Risk - requires PIN confirmation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "delay_seconds": {
                        "type": "integer",
                        "default": 30,
                        "description": "Delay in seconds before shutdown occurs."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_computer",
            "description": "Initiate computer restart with a countdown delay (HIGH Risk - requires PIN confirmation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "delay_seconds": {
                        "type": "integer",
                        "default": 30,
                        "description": "Delay in seconds before restart occurs."
                    }
                }
            }
        }
    }
    ,
    # Phase 3C: Timers
    {
        "type": "function",
        "function": {
            "name": "set_timer",
            "description": "Start a countdown timer that notifies the user when it ends. Examples: 'set a timer for 5 minutes', '30 second timer', '1 hour timer'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration": {
                        "type": "string",
                        "description": "Duration as a natural-language string, e.g. '5 minutes', '30 seconds', '1 hour', '2 hours 30 minutes'."
                    },
                    "label": {
                        "type": "string",
                        "description": "Optional name for this timer, e.g. 'Tea timer', 'Workout'. Default: generic."
                    }
                },
                "required": ["duration"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_alarm",
            "description": "Set an alarm for a specific time of day. Examples: 'set alarm for 7:30 am', '9 pm alarm', 'noon alarm'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alarm_time": {
                        "type": "string",
                        "description": "Time of day string, e.g. '7:30 am', '15:00', '9 pm', 'noon', 'midnight'."
                    },
                    "label": {
                        "type": "string",
                        "description": "Optional label for this alarm, e.g. 'Morning standup'."
                    }
                },
                "required": ["alarm_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a reminder with a message at a specific time or after a duration. Examples: 'remind me to call Ahmed at 5 pm', 'reminder: take medicine in 2 hours'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The reminder message text, e.g. 'Call Ahmed', 'Take medicine', 'Meeting with team'."
                    },
                    "when": {
                        "type": "string",
                        "description": "When to fire: time-of-day ('5 pm', '14:30') or duration ('in 30 minutes', '2 hours')."
                    }
                },
                "required": ["message", "when"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_timers",
            "description": "List all active countdown timers, alarms, and reminders.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_timer",
            "description": "Cancel an active timer by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timer_id": {"type": "string", "description": "The timer ID to cancel."}
                },
                "required": ["timer_id"]
            }
        }
    },
    # Creator Vault & Identity Tools
    {
        "type": "function",
        "function": {
            "name": "get_creator_info",
            "description": "Get information about the creator (Muhammad Akmal), such as his bio, title, tech stack, github, portfolio, linkedin, or current active goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "Specific field to retrieve (optional): 'goals', 'github', 'portfolio', 'linkedin', 'tech_stack', 'bio', 'title'."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_creator_link",
            "description": "Open creator's profile in browser: 'portfolio', 'github', or 'linkedin'. Use when creator asks to see/open his portfolio, github, or linkedin.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "enum": ["portfolio", "github", "linkedin"],
                        "description": "Which platform or link to open: 'portfolio', 'github', or 'linkedin'."
                    },
                    "inspect": {
                        "type": "boolean",
                        "description": "Optional: set to True if the user asks to inspect the page or open in developer mode / devtools.",
                        "default": False
                    }
                },
                "required": ["platform"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_creator_email",
            "description": "Open creator Akmal Sir's email inbox or compose window directly in browser. Supports multiple accounts: 'primary', 'personal', 'work', 'developer', 'official', '1', '2', '3', '4', or email address substring. Use when the user says 'open email', 'meri email check karo', 'open my work email', 'inbox open karo', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Which email account to open: 'primary', 'personal', 'work', 'developer', 'official', '1', '2', '3', '4', or specific email address/keyword."
                    },
                    "action": {
                        "type": "string",
                        "enum": ["inbox", "compose"],
                        "default": "inbox",
                        "description": "'inbox' to open mail inbox folder, or 'compose' to start a new draft."
                    },
                    "recipient": {
                        "type": "string",
                        "description": "Optional recipient email address if action is 'compose'."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_creator_emails_summary",
            "description": "Retrieve summary of creator Akmal Sir's registered email accounts (personal, work, developer, official).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_creator_thought",
            "description": "Save a personal thought, goal, plan, or note to the creator's private Vault. Use when the user says 'note this thought', 'save to vault', 'mera goal add karo', or 'yeh idea likh lo'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The thought, idea, or goal description to save."
                    },
                    "category": {
                        "type": "string",
                        "enum": ["thought", "goal", "plan", "note"],
                        "default": "thought",
                        "description": "Category: 'thought', 'goal', 'plan', or 'note'."
                    },
                    "title": {
                        "type": "string",
                        "description": "Short headline or title for this entry (optional)."
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_projects",
            "description": "List all active coding/software projects registered in the Creator Vault, including their names, folder paths, and tech stack.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_project",
            "description": "Open a registered project in Visual Studio Code (or File Explorer). E.g. 'open JARVIS project' or 'open portfolio in code'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name or keyword of the project to open (e.g. 'JARVIS', 'portfolio')."
                    },
                    "in_vscode": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to open in Visual Studio Code (True) or File Explorer (False)."
                    }
                },
                "required": ["project_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_today_focus",
            "description": "Retrieve today's daily focus / standup priority tasks list.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_today_focus_task",
            "description": "Add a new task to Today's Daily Focus list in the Creator Vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task description to add to today's focus."
                    }
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_creator_accounts_info",
            "description": "Retrieve all connected developer and social media accounts (GitHub, LinkedIn, Twitter/X, Instagram, YouTube, Portfolio, etc.) with handles, profile URLs, and content themes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "Optional: filter by platform name (e.g. 'github', 'linkedin', 'twitter', 'portfolio')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_creator_account",
            "description": "Inspect live public stats and recent activity on creator's account (e.g. GitHub repos/followers, LinkedIn profile, Twitter) and sync it into the Creator Vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "The platform to inspect (e.g. 'github', 'linkedin', 'twitter', 'portfolio')."
                    }
                },
                "required": ["platform"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_social_post",
            "description": "Draft high-impact content for creator's social media platforms (LinkedIn, Twitter/X, GitHub) and save to Creator Vault drafts for review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "Target platform: 'linkedin', 'twitter', 'github', or 'general'."
                    },
                    "topic": {
                        "type": "string",
                        "description": "The topic, technical achievement, project feature, or thought to write about."
                    },
                    "content_style": {
                        "type": "string",
                        "description": "Style of post: 'engaging', 'technical', 'concise', or 'story'."
                    },
                    "hashtags": {
                        "type": "string",
                        "description": "Optional custom hashtags (e.g. '#AI #NextJS #Engineering')."
                    }
                },
                "required": ["platform", "topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "publish_social_post",
            "description": "Stage or publish a post to social media (copies post content to Windows clipboard and opens the platform's posting window in the browser).",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "Platform to publish on (e.g. 'linkedin', 'twitter', 'github')."
                    },
                    "content": {
                        "type": "string",
                        "description": "The complete post text to publish."
                    },
                    "auto_open_browser": {
                        "type": "boolean",
                        "description": "Whether to automatically open the social media posting interface in browser (default True)."
                    }
                },
                "required": ["platform", "content"]
            }
        }
    },
    # Phase 4: Files and Coding Tools
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of any code or text file from anywhere on the PC (Documents, Desktop, projects, C:, D:, etc.). Supports pagination with max_lines and offset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The file path to read (can be anywhere on the PC: Documents, Downloads, Desktop, or full path like C:\\... or D:\\...)."
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of lines to read (default 250)."
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Starting line number (1-indexed, default 1)."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_project",
            "description": "Analyze an entire project workspace: detects tech stack, frameworks, dependencies, key entrypoints, and Git status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "The project folder path to inspect (defaults to current active project)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory_files",
            "description": "List files and subdirectories anywhere on the PC (Documents, Downloads, Desktop, or any drive/folder), automatically ignoring vendor/build caches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "The folder path to list."
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to list subfolders recursively (default false)."
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum recursion depth (default 2)."
                    }
                },
                "required": ["directory_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Search for a specific function, class, variable, or text string across code files in a project or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, function name, or pattern to find."
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Project directory to search in (defaults to current project)."
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Optional file name filter (e.g. '.tsx', '.py', 'route')."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file with specified content anywhere on the user's PC (e.g. Documents, Downloads, Desktop, or any drive/folder). No registration required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Destination file path (e.g. 'documents/filename.txt', 'downloads/file.py', or full path like 'C:\\...')."
                    },
                    "content": {
                        "type": "string",
                        "description": "The full code or text content to write into the file."
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a new directory or folder anywhere on the user's PC (e.g. Documents, Downloads, Desktop, or any drive/folder). No registration required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Directory path to create (e.g. 'documents/myfolder', 'downloads/private', or full path)."
                    }
                },
                "required": ["folder_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modify_file",
            "description": "Modify an existing file safely by replacing target_content with replacement_content. Generates unified git diff.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to modify."
                    },
                    "target_content": {
                        "type": "string",
                        "description": "The exact existing text block to be replaced."
                    },
                    "replacement_content": {
                        "type": "string",
                        "description": "The new replacement text block."
                    }
                },
                "required": ["file_path", "target_content", "replacement_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file_or_folder",
            "description": "HIGH RISK: Delete a file or folder. Requires explicit user confirmation and Security PIN.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_path": {
                        "type": "string",
                        "description": "The file or folder path to permanently delete."
                    }
                },
                "required": ["target_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_git_status",
            "description": "Check git branch, modified files, and working tree status of a project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Project path (defaults to current project)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_git_diff",
            "description": "View uncommitted Git diff changes for the project or a specific file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Project path (defaults to current project)."
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Optional specific file to check diff for."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_dev_tests",
            "description": "Run unit or integration tests (pytest, npm test, etc.) in a project and return results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Project directory path."
                    },
                    "test_command": {
                        "type": "string",
                        "description": "Custom test command (e.g. 'pytest tests/test_brain.py' or 'npm test'). Optional."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_code_error",
            "description": "Diagnose a runtime traceback, compiler error, or syntax exception and explain concrete solution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "error_log": {
                        "type": "string",
                        "description": "The raw terminal error log, stack trace, or compiler message."
                    },
                    "project_context": {
                        "type": "string",
                        "description": "Optional project path or context."
                    }
                },
                "required": ["error_log"]
            }
        }
    },
    # Phase 5: Web Intelligence Tools
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the internet for current real-time information, news, documentation, or answers to show or synthesize INSIDE the chat. DO NOT use this if the user asks to search on Google or open in browser (use open_website instead). Always cite sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g. 'Next.js 15 features', 'latest Pakistan tech news', 'FastAPI documentation')."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to retrieve (default 5)."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current real-time weather and forecast for any city or location (temperature, condition, humidity, wind).",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city (e.g. 'Lahore', 'Karachi', 'Islamabad', 'London'). Defaults to 'Lahore'."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Safely fetch and read documentation or article content from a specific web URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full webpage URL to read (e.g. 'https://docs.python.org/3/')."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters of text to extract (default 2500)."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_youtube_video",
            "description": "Search YouTube and automatically launch & play the top matching song or video directly in the browser (resolves direct watch URL in ~1s). Use when the user asks to play a song/video on YouTube (e.g. 'youtube per ye song play kro', 'youtube par tajdar e haram chalao', 'play satinder sartaaj on youtube').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The song, artist, video title, or search term to play (e.g. 'atif aslam tajdar e haram', 'punjabi song')."
                    },
                    "profile_name": {
                        "type": "string",
                        "description": "Optional Chrome profile to play in. Defaults strictly to 'Default' (Account 1 - Rana Akmal / ranaakmalr703@gmail.com - Primary Profile). Do NOT specify Account 2 unless user explicitly requests it."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_website",
            "description": "Open any website, portal, or web application, extract its content, and provide an instant structured analysis (Title, Domain, Summary, Key Highlights). If user mentions an account/profile, opens under that authenticated Chrome profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The website address or portal to analyze (e.g. 'https://nextjs.org', 'vercel', 'github', 'lms', 'https://python.org')."
                    },
                    "profile_name": {
                        "type": "string",
                        "description": "Optional Chrome profile or Google account (e.g. 'Account 1', 'Rana Akmal', 'Account 2', '84pakarmy', 'Account 3', 'vu', 'Account 4', 'developer')."
                    },
                    "open_in_browser": {
                        "type": "boolean",
                        "description": "Whether to also open the page visibly in the user's browser (default True)."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_google_accounts",
            "description": "List all 4 Google accounts / Chrome profiles configured on this PC with account numbers, user names, emails, and active aliases.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_chrome_bookmarks",
            "description": "List and search saved Chrome Bookmarks across the user's Google accounts/profiles. Use when user asks 'mere bookmarks dikhao' or 'bookmarks mein se X dhoondo'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional keyword or site name to search inside bookmarks."
                    },
                    "profile_name": {
                        "type": "string",
                        "description": "Optional specific profile/account to inspect (e.g. 'Account 1', 'Account 2', 'VU', 'developer')."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_chrome_history",
            "description": "Search Chrome browsing history for previously visited pages, portals, or topics across profiles. Use when user asks 'meri history mein se X dhoondo' or 'history search karo'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term, website title, or domain to look for in history."
                    },
                    "profile_name": {
                        "type": "string",
                        "description": "Optional specific profile/account."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of history results to return (default 15)."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_smart_website",
            "description": "Open any website, bookmark, portal, or history item directly in Google Chrome, automatically resolving to the user's exact logged-in account/dashboard URL (e.g. Vercel dashboard, VU LMS portal, Gmail direct inbox).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_or_url": {
                        "type": "string",
                        "description": "The website name, portal, or bookmark to open (e.g. 'vercel', 'lms', 'vu', 'gmail', 'github', 'chatgpt', 'https://...')."
                    },
                    "profile_name": {
                        "type": "string",
                        "description": "Optional Chrome profile or Google account."
                    },
                    "inspect": {
                        "type": "boolean",
                        "description": "Whether to open with Developer Tools / Inspect mode active."
                    }
                },
                "required": ["query_or_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_creator_dossier",
            "description": "Retrieve comprehensive digital dossier, online identity, social links, and tech stack of creator Akmal Sir.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sync_creator_online_presence",
            "description": "Automatically scrape and sync creator's public repositories, bio, follower count, and online footprint from GitHub.",
            "parameters": {
                "type": "object",
                "properties": {
                    "github_username": {
                        "type": "string",
                        "description": "Optional GitHub handle (e.g. 'ranaakmal'). If omitted, uses existing dossier handle."
                    }
                }
            }
        }
    },
    # Phase 6B: Long-Term Memory Matrix Tools
    {
        "type": "function",
        "function": {
            "name": "remember_information",
            "description": "Store an explicit user instruction, habit, fact, or preference into JARVIS's persistent memory matrix (e.g. 'user prefers VS Code as editor', 'favourite language is TypeScript', 'remember my meeting at 4 PM'). Refuses passwords, API keys, or financial credentials.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The exact fact, instruction, or preference to remember."
                    },
                    "category": {
                        "type": "string",
                        "enum": ["preference", "project", "instruction", "fact", "context"],
                        "description": "Category of the memory (default: 'preference')."
                    },
                    "key": {
                        "type": "string",
                        "description": "Optional short identifier or topic (e.g. 'default_editor', 'coding_style', 'favorite_theme')."
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memories",
            "description": "Search or retrieve stored memories from JARVIS's long-term memory matrix by keyword or category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional search term to find relevant memories."
                    },
                    "category": {
                        "type": "string",
                        "enum": ["preference", "project", "instruction", "fact", "context"],
                        "description": "Optional category filter."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forget_memory",
            "description": "Delete a memory item by ID, keyword, or clear all memories if explicitly requested by the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "integer",
                        "description": "ID of the specific memory to delete."
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Topic or keyword of memories to remove."
                    },
                    "forget_all": {
                        "type": "boolean",
                        "description": "Set to True if the user explicitly asks to forget everything (requires PIN confirmation)."
                    }
                }
            }
        }
    },
    # Phase 7: Desktop Vision & Screen Diagnostics Tools
    {
        "type": "function",
        "function": {
            "name": "inspect_screen",
            "description": "Capture the user's screen on-demand and perform visual analysis using Multimodal Vision AI. Can diagnose runtime errors, terminal output, code bugs, UI layouts, or provide a general summary. Privacy Rule: Captured on-demand only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus": {
                        "type": "string",
                        "enum": ["error", "code", "ui", "general"],
                        "description": "Inspection focus: 'error' (terminal crashes, red errors, dialogs), 'code' (syntax/logic review), 'ui' (window/button layout), or 'general' (summary). Default: 'general'."
                    },
                    "question": {
                        "type": "string",
                        "description": "Optional specific question or prompt about the screen (e.g. 'Why is this test failing?', 'What error is shown in the terminal?')."
                    },
                    "save_screenshot": {
                        "type": "boolean",
                        "description": "If True, saves a copy of the screenshot to user's Desktop; otherwise purely in-memory."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_screenshot",
            "description": "Explicitly capture and save a screenshot of the user's desktop to file (e.g. on Desktop). Use when user asks 'take a screenshot' or 'save screenshot'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Optional custom filename or destination (e.g. 'Desktop/error.png')."
                    }
                }
            }
        }
    },
    # Phase 8: Autonomous Multi-Step Agent Tools
    {
        "type": "function",
        "function": {
            "name": "execute_agent_mission",
            "description": "Execute an autonomous multi-step engineering or deployment mission (e.g. 'prepare project for deployment', 'diagnose and fix errors', 'workspace audit'). Automatically sequences steps, tests, and verifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "The high-level autonomous goal to achieve (e.g. 'prepare project for deployment', 'workspace audit')."
                    },
                    "template": {
                        "type": "string",
                        "description": "Optional workflow template key: 'deployment_prep', 'bug_diagnosis', or 'workspace_audit'."
                    }
                },
                "required": ["goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_agent_plan",
            "description": "Generate a structured multi-step plan for a complex objective without executing it immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "The goal to break down into steps."
                    }
                },
                "required": ["goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_agent_mission",
            "description": "Immediately abort and stop any running autonomous agent workflow (Emergency STOP).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # Autonomous Browser-Use Agent Tool
    {
        "type": "function",
        "function": {
            "name": "autonomous_browser_agent",
            "description": "Deploy an autonomous AI web agent (powered by Browser-Use) that can autonomously navigate real websites in Google Chrome/Chromium, click buttons, fill forms, compare prices, research products, extract structured information, or complete complex multi-step online workflows. Use when the user asks JARVIS to perform active actions on the web (e.g. 'Daraz per laptops search karke price compare karo', 'YouTube per video dhund kar play karo', 'is website per login form fill karo', 'web page se data scrape ya extract karo', 'browser agent chalao').",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The exact step-by-step goal or instruction for the autonomous browser agent."
                    },
                    "visible": {
                        "type": "boolean",
                        "description": "Whether to keep the browser visible so user can watch the agent work live (default True)."
                    },
                    "max_steps": {
                        "type": "integer",
                        "description": "Maximum action steps allowed (default 15)."
                    }
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_chrome_profile",
            "description": "Open Google Chrome under a specific user profile (e.g. 'M. Akmal', 'Next.js Developer', 'Default', 'vu.edu.pk') and optionally navigate directly to a website or portal dashboard (e.g. 'vercel', 'leetcode', 'expo', 'maps').",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_name": {
                        "type": "string",
                        "description": "The name or alias of the Chrome profile to open (e.g. 'M. Akmal', 'Next.js Developer', 'Default', 'vu.edu.pk')."
                    },
                    "url": {
                        "type": "string",
                        "description": "Optional website URL or portal shortcut to open directly in that profile (e.g. 'vercel', 'leetcode', 'expo', 'https://...')."
                    }
                },
                "required": ["profile_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_message",
            "description": "Open WhatsApp (Desktop or Web), search for the contact name or phone number, open their conversation, and draft the message ready to send. Always call this first when asked to message someone on WhatsApp. NEVER call confirm_send_whatsapp in the same turn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_name_or_phone": {
                        "type": "string",
                        "description": "Contact name (e.g. 'Wajid', 'Ali', 'Ahmed') or direct phone number (e.g. '03001234567', '+92...')."
                    },
                    "message": {
                        "type": "string",
                        "description": "The message text to draft. Check if the message is in proper format: if already clean and proper, keep it as is; if rough, informal slang, unpunctuated, or has typos, automatically correct and polish it into proper, clean, respectful and well-punctuated text while preserving its exact meaning and language."
                    },
                    "platform": {
                        "type": "string",
                        "description": "WhatsApp platform: 'auto' (default, detects active desktop app or browser), 'web' (WhatsApp Web in browser), or 'desktop' (native WhatsApp Desktop app). Pass 'web' if user explicitly asks for WhatsApp Web.",
                        "enum": ["auto", "web", "desktop"]
                    }
                },
                "required": ["contact_name_or_phone", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_whatsapp_web",
            "description": "Open WhatsApp Web directly in default browser or bring active WhatsApp Web browser window to foreground.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section of WhatsApp Web to open: 'chats' (default), 'status', or 'channels'.",
                        "enum": ["chats", "status", "channels"]
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_contact",
            "description": "Save or update a contact's phone number in JARVIS address book for quick WhatsApp messaging.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Contact name (e.g. 'Ali')."
                    },
                    "phone": {
                        "type": "string",
                        "description": "Phone number (e.g. '03001234567', '+923001234567')."
                    }
                },
                "required": ["name", "phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_send_whatsapp",
            "description": "Send the currently drafted WhatsApp message by focusing WhatsApp and pressing Enter. Call this ONLY when the user explicitly confirms sending a previously drafted message (e.g. 'send kr do', 'send it', 'ab bhej do', 'haan bhej do', 'yes send'). NEVER call this in the same turn as send_whatsapp_message.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_contacts",
            "description": "List all saved contacts in the JARVIS address book.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_whatsapp_status",
            "description": "Prepare and draft a status on WhatsApp Desktop (Text status with styled fonts/colors or TikTok video status) ready for the user to review. Always call this first when asked to post or update a WhatsApp status. NEVER call confirm_post_whatsapp_status in the same turn! Ask the user if they want to upload it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_text": {
                        "type": "string",
                        "description": "Text content, quote, or topic for the status (e.g. 'Saturday status', 'Islamic quote', 'Jumma Mubarak', 'Achi baat', or custom quote)."
                    },
                    "media_url": {
                        "type": "string",
                        "description": "Optional TikTok URL or search topic for video status."
                    },
                    "status_type": {
                        "type": "string",
                        "enum": ["text", "tiktok", "video"],
                        "default": "text",
                        "description": "Type of status: 'text' or 'tiktok'/'video'."
                    },
                    "cycle_background": {
                        "type": "integer",
                        "default": 3,
                        "description": "Number of times to click Palette button to cycle background color (1-5)."
                    },
                    "cycle_font": {
                        "type": "integer",
                        "default": 2,
                        "description": "Number of times to click Font button to cycle font style (1-5)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "customize_whatsapp_status",
            "description": "Change or customize the WhatsApp status draft: change background color, change font style, or update/replace the status text (e.g. 'background color change karo', 'font badlo', 'ise change karo', 'kuch or acha status lagao', 'color change karo', 'text change karo').",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_text": {
                        "type": "string",
                        "description": "Optional new text, quote, or topic for the status if replacing text."
                    },
                    "cycle_background": {
                        "type": "integer",
                        "default": 1,
                        "description": "Number of times to click the Palette button to cycle background color (1-5)."
                    },
                    "cycle_font": {
                        "type": "integer",
                        "default": 1,
                        "description": "Number of times to click the Font button to cycle font style (1-5)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_post_whatsapp_status",
            "description": "Confirm and upload/publish the currently prepared WhatsApp status. Call this ONLY after post_whatsapp_status was called and the user explicitly confirms with 'upload kar do', 'post kar do', 'laga do', 'send kar do', 'haan upload karo', 'upload it', etc.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_whatsapp_status",
            "description": "Delete the currently active WhatsApp status update, or discard an in-progress status draft. Call whenever the user asks to delete their status ('status delete kr do', 'status hata do', 'delete status', 'status mita do').",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "discard_whatsapp_status",
            "description": "Discard an in-progress WhatsApp status draft, close the status posting view, and return WhatsApp to the main Chats screen. Call this whenever the user says not to upload the status, cancel it, discard it, or says not to post it (e.g. 'upload mat karna', 'status mat lagao', 'discard kar do', 'cancel kar do', 'upload na karo', 'rehne do', 'status na lagao').",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "make_whatsapp_call",
            "description": "Start a WhatsApp voice or video call with a contact or phone number. Automatically focuses WhatsApp Desktop, opens their conversation, and dials the call. Call immediately when the user asks to call someone (e.g. 'Ali ko call milao', 'Wajid ko voice call karo', 'Ali ko video call lagao', 'call Ali on WhatsApp').",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_name_or_phone": {
                        "type": "string",
                        "description": "Contact name (e.g. 'Wajid', 'Ali', 'Ahmed') or direct phone number."
                    },
                    "call_type": {
                        "type": "string",
                        "enum": ["voice", "video"],
                        "default": "voice",
                        "description": "Type of call: 'voice' for voice/audio call, 'video' for video call."
                    }
                },
                "required": ["contact_name_or_phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "end_whatsapp_call",
            "description": "Disconnect or end an active, outgoing, or incoming WhatsApp voice or video call. Call immediately when the user asks to hang up or end the call (e.g. 'call kaat do', 'call end karo', 'call band karo', 'disconnect call', 'hang up').",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_whatsapp_call_mute",
            "description": "Mute or unmute the microphone during a WhatsApp call. Call when the user asks to mute or unmute their mic (e.g. 'mic mute kar do', 'call mute karo', 'unmute karo').",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["mute", "unmute", "toggle"],
                        "default": "toggle",
                        "description": "Action: 'mute', 'unmute', or 'toggle'."
                    }
                }
            }
        }
    }
]

def _create_agent_plan_wrapper(goal: str, template: Optional[str] = None) -> Dict[str, Any]:
    from backend.agent.planner import generate_plan
    plan = generate_plan(goal=goal, template_key=template)
    return {
        "success": True,
        "task_id": plan.task_id,
        "goal": plan.goal,
        "steps_count": len(plan.steps),
        "steps": [s.to_dict() for s in plan.steps],
        "message": f"Autonomous plan generated with {len(plan.steps)} steps."
    }

def _execute_agent_mission_wrapper(goal: str, template: Optional[str] = None) -> Dict[str, Any]:
    from backend.agent.planner import generate_plan
    from backend.agent.executor import global_agent_executor
    plan = generate_plan(goal=goal, template_key=template)
    res_plan = global_agent_executor.execute_plan(plan)
    return {
        "success": res_plan.status == "completed",
        "task_id": res_plan.task_id,
        "status": res_plan.status,
        "summary": res_plan.summary or "Mission completed.",
        "steps_completed": sum(1 for s in res_plan.steps if s.status == "completed"),
        "total_steps": len(res_plan.steps)
    }

def _stop_agent_mission_wrapper() -> Dict[str, Any]:
    from backend.agent.executor import global_agent_executor
    return global_agent_executor.stop_execution()

# Dispatcher mapping
TOOL_HANDLERS = {
    "open_application": system_control.open_application,
    "close_application": system_control.close_application,
    "open_folder": system_control.open_folder,
    "close_folder": system_control.close_folder,
    "open_file": system_control.open_file,
    "open_website": system_control.open_website,
    "open_in_vscode": system_control.open_in_vscode,
    "open_file_in_browser": system_control.open_file_in_browser,
    "start_local_server": system_control.start_local_server,
    "open_in_terminal": system_control.open_in_terminal,
    "get_system_status": system_control.get_system_status,
    "get_open_windows": system_control.get_open_windows,
    "set_system_volume": system_control.set_system_volume,
    "set_system_brightness": system_control.set_system_brightness,
    "control_quick_setting": system_control.control_quick_setting,
    "lock_computer": system_control.lock_computer,
    "sleep_computer": system_control.sleep_computer,
    "shutdown_computer": system_control.shutdown_computer,
    "restart_computer": system_control.restart_computer,
    "open_chrome_profile": system_control.open_chrome_profile,
    "send_whatsapp_message": system_control.send_whatsapp_message,
    "confirm_send_whatsapp": system_control.confirm_send_whatsapp,
    "open_whatsapp_web": system_control.open_whatsapp_web,
    "save_contact": system_control.save_contact,
    "list_contacts": system_control.list_contacts,
    "post_whatsapp_status": system_control.post_whatsapp_status,
    "customize_whatsapp_status": system_control.customize_whatsapp_status,
    "confirm_post_whatsapp_status": system_control.confirm_post_whatsapp_status,
    "delete_whatsapp_status": system_control.delete_whatsapp_status,
    "discard_whatsapp_status": system_control.discard_whatsapp_status,
    "make_whatsapp_call": system_control.make_whatsapp_call,
    "end_whatsapp_call": system_control.end_whatsapp_call,
    "toggle_whatsapp_call_mute": system_control.toggle_whatsapp_call_mute,
    # Phase 3C: Timer tools
    "set_timer": timer_tools.set_timer,
    "set_alarm": timer_tools.set_alarm,
    "set_reminder": timer_tools.set_reminder,
    "list_timers": timer_tools.get_all_active,
    "cancel_timer": timer_tools.cancel_timer,
    # Creator Vault & Dossier tools
    "get_creator_info": creator_tools.get_creator_info,
    "open_creator_link": creator_tools.open_creator_link,
    "open_creator_email": creator_tools.open_creator_email,
    "get_creator_emails_summary": creator_tools.get_creator_emails_summary,
    "save_creator_thought": creator_tools.save_creator_thought,
    "get_active_projects": creator_tools.get_active_projects,
    "open_project": creator_tools.open_project,
    "get_today_focus": creator_tools.get_today_focus,
    "add_today_focus_task": creator_tools.add_today_focus_task,
    "get_creator_accounts_info": creator_tools.get_creator_accounts_info,
    "inspect_creator_account": creator_tools.inspect_creator_account,
    "draft_social_post": creator_tools.draft_social_post,
    "publish_social_post": creator_tools.publish_social_post,
    "get_creator_dossier": lambda **kwargs: __import__("backend.database.creator_dossier", fromlist=["get_dossier"]).get_dossier(),
    "sync_creator_online_presence": lambda github_username=None, **kwargs: __import__("backend.database.creator_dossier", fromlist=["sync_creator_online"]).sync_creator_online(github_username=github_username),
    # Phase 4: Coding & File Tools
    "read_file": code_tools.read_file,
    "inspect_project": code_tools.inspect_project,
    "list_directory_files": code_tools.list_directory_files,
    "search_codebase": code_tools.search_codebase,
    "create_file": code_tools.create_file,
    "create_folder": code_tools.create_folder,
    "modify_file": code_tools.modify_file,
    "delete_file_or_folder": code_tools.delete_file_or_folder,
    "run_git_status": code_tools.run_git_status,
    "run_git_diff": code_tools.run_git_diff,
    "run_dev_tests": code_tools.run_dev_tests,
    "explain_code_error": code_tools.explain_code_error,
    # Phase 5: Web Intelligence Tools
    "search_web": web_tools.search_web,
    "get_weather": web_tools.get_weather,
    "read_webpage": web_tools.read_webpage,
    "play_youtube_video": web_tools.play_youtube_video,
    "analyze_website": web_tools.analyze_website,
    "list_google_accounts": system_control.list_google_accounts,
    "list_chrome_bookmarks": chrome_bookmarks.list_chrome_bookmarks,
    "search_chrome_history": chrome_bookmarks.search_chrome_history_tool,
    "open_smart_website": chrome_bookmarks.open_smart_website,
    # Phase 6B: Long-Term Memory Matrix Tools
    "remember_information": memory_tools.remember_information,
    "recall_memories": memory_tools.recall_memories,
    "forget_memory": memory_tools.forget_memory,
    # Phase 7: Desktop Vision Tools
    "inspect_screen": vision_tools.inspect_screen,
    "capture_screenshot": vision_tools.save_screenshot,
    # Phase 8: Autonomous Multi-Step Agent Tools
    "create_agent_plan": _create_agent_plan_wrapper,
    "execute_agent_mission": _execute_agent_mission_wrapper,
    "stop_agent_mission": _stop_agent_mission_wrapper,
    "autonomous_browser_agent": browser_agent.execute_autonomous_browser,
}


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    confirmed: bool = False,
    pin: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a requested tool with risk enforcement, confirmation checks, and audit logging.
    """
    if tool_name not in TOOL_HANDLERS:
        log_tool_call(tool_name, arguments, RiskLevel.HIGH.value, confirmed, "DENIED", error="Unknown tool")
        return {
            "success": False,
            "status": "DENIED",
            "error": f"Tool '{tool_name}' is not recognized or permitted in JARVIS."
        }

    risk_level = get_tool_risk(tool_name, arguments)
    handler = TOOL_HANDLERS[tool_name]

    # LOW RISK: Execute automatically without prompt
    if risk_level == RiskLevel.LOW:
        try:
            result = handler(**arguments) if arguments else handler()
            status = "SUCCESS" if result.get("success", True) else "FAILED"
            err = result.get("error") if not result.get("success", True) else None
            msg = result.get("message", "")
            log_tool_call(tool_name, arguments, risk_level.value, True, status, msg, error=err)
            return {
                "success": result.get("success", True),
                "status": status,
                "risk_level": risk_level.value,
                "result": result,
                "error": err,
                "message": msg
            }
        except Exception as e:
            log_tool_call(tool_name, arguments, risk_level.value, True, "FAILED", error=str(e))
            return {"success": False, "status": "FAILED", "risk_level": risk_level.value, "error": str(e), "message": str(e)}

    # MEDIUM RISK: Requires user confirmation
    if risk_level == RiskLevel.MEDIUM:
        if not confirmed:
            desc = f"Execute action '{tool_name}' with parameters {arguments}."
            req = create_confirmation_request(tool_name, arguments, risk_level, desc)
            log_tool_call(tool_name, arguments, risk_level.value, False, "PENDING_CONFIRMATION")
            return {
                "success": False,
                "status": "PENDING_CONFIRMATION",
                "risk_level": risk_level.value,
                "requires_pin": False,
                "confirmation_id": req["confirmation_id"],
                "message": f"Action '{tool_name}' requires your confirmation.",
                "description": desc
            }
        # If confirmed, proceed
        try:
            result = handler(**arguments) if arguments else handler()
            status = "SUCCESS" if result.get("success", True) else "FAILED"
            log_tool_call(tool_name, arguments, risk_level.value, True, status, result.get("message", ""))
            return {"success": result.get("success", True), "status": status, "risk_level": risk_level.value, "result": result}
        except Exception as e:
            log_tool_call(tool_name, arguments, risk_level.value, True, "FAILED", error=str(e))
            return {"success": False, "status": "FAILED", "risk_level": risk_level.value, "error": str(e)}

    # HIGH RISK: Requires user confirmation + PIN
    if risk_level == RiskLevel.HIGH:
        if not confirmed or not pin:
            desc = f"Execute HIGH risk action '{tool_name}' with parameters {arguments}."
            req = create_confirmation_request(tool_name, arguments, risk_level, desc)
            log_tool_call(tool_name, arguments, risk_level.value, False, "PENDING_CONFIRMATION")
            return {
                "success": False,
                "status": "PENDING_CONFIRMATION",
                "risk_level": risk_level.value,
                "requires_pin": True,
                "confirmation_id": req["confirmation_id"],
                "message": f"HIGH RISK: Action '{tool_name}' requires your security PIN to proceed.",
                "description": desc
            }

        # Verify PIN
        pin_valid, pin_msg = verify_pin(pin)
        if not pin_valid:
            log_tool_call(tool_name, arguments, risk_level.value, False, "DENIED", error=pin_msg)
            return {
                "success": False,
                "status": "DENIED",
                "risk_level": risk_level.value,
                "error": pin_msg
            }

        # Execute HIGH risk action
        try:
            result = handler(**arguments) if arguments else handler()
            status = "SUCCESS" if result.get("success", True) else "FAILED"
            log_tool_call(tool_name, arguments, risk_level.value, True, status, result.get("message", ""))
            return {"success": result.get("success", True), "status": status, "risk_level": risk_level.value, "result": result}
        except Exception as e:
            log_tool_call(tool_name, arguments, risk_level.value, True, "FAILED", error=str(e))
            return {"success": False, "status": "FAILED", "risk_level": risk_level.value, "error": str(e)}


def get_relevant_tools_schema(query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Dynamically prune the 56-tool schema to only the tools relevant to the user's intent.
    Reduces prompt token payload by 75-85%, preventing Groq free-tier rate limits (TPM).
    """
    if not query:
        core_names = {
            "open_application", "close_application", "open_folder", "create_file", 
            "create_folder", "search_web", "open_website", "get_system_status",
            "open_in_vscode", "open_file_in_browser"
        }
        return [t for t in JARVIS_TOOLS_SCHEMA if t["function"]["name"] in core_names]

    q = query.lower()
    selected_names = {
        "open_application", "close_application", "open_folder", "create_file", 
        "create_folder", "open_in_vscode", "open_file_in_browser"
    }

    # Coding & Files & Projects & Developer Workstation
    coding_triggers = (
        "file", "folder", "todo", "app", "project", "code", "banao", "create", 
        "python", "html", "css", "js", "fastapi", "react", "next", "script", 
        "write", "read", "inspect", "search", "git", "status", "diff", "test", 
        "delete", "remove", "clean", "desktop", "document", "download",
        "vscode", "vs code", "browser", "run", "launch", "page", "server", 
        "live", "preview", "terminal", "cmd"
    )
    if any(k in q for k in coding_triggers):
        selected_names.update({
            "create_file", "create_folder", "modify_file", "read_file", 
            "list_directory_files", "delete_file_or_folder", "search_codebase", 
            "inspect_project", "run_git_status", "run_git_diff", "run_dev_tests", 
            "explain_code_error", "get_active_projects",
            "open_in_vscode", "open_file_in_browser", "start_local_server", "open_in_terminal"
        })

    # Web & Weather
    # Web, Portals & Chrome Profiles
    web_triggers = (
        "search", "google", "youtube", "weather", "forecast", "barish", "rain", 
        "temp", "temperature", "mausam", "url", "link", "web", "internet", "news", "site",
        "vercel", "leetcode", "leetcord", "expo", "map", "maps", "dashboard", "portal",
        "play", "song", "chalao", "sunao", "lagao", "analyze", "analyse", "summary",
        "bookmark", "bookmarks", "book mark", "history", "saved page"
    )
    if any(k in q for k in web_triggers):
        selected_names.update({
            "open_website", "search_web", "read_webpage", "get_weather", "open_chrome_profile",
            "play_youtube_video", "analyze_website", "list_chrome_bookmarks", "search_chrome_history", "open_smart_website"
        })

    # Chrome Profiles & Google Accounts
    chrome_triggers = (
        "chrome", "profile", "m akmal", "akmal", "nextjs", "next.js", "vu", "developer profile",
        "account", "accounts", "google account", "google accounts", "ids", "id", "meri id",
        "rana akmal", "84pakarmy", "lms", "pakarmy", "bookmark", "bookmarks", "book mark", "history"
    )
    if any(k in q for k in chrome_triggers):
        selected_names.update({
            "open_chrome_profile", "open_website", "open_application", "list_google_accounts",
            "analyze_website", "list_chrome_bookmarks", "search_chrome_history", "open_smart_website"
        })

    # WhatsApp & Contacts Messaging
    whatsapp_triggers = (
        "whatsapp", "whatsapp web", "web", "message", "msg", "chat", "contact", "contacts", "bhejo", "bejo", 
        "send", "phone", "number", "ali", "ahmed", "adnan", "wajid", "draft", "raabta", "kr do", "kar do",
        "status", "tiktok", "tik tok", "juma", "jumma", "islamic", "delete status", "upload", "uplord", "discard",
        "mat lagao", "mat upload", "font", "color", "background", "rang", "badlo", "change", "palette", "quote",
        "call", "voice call", "video call", "kaat do", "end call", "hang up", "mute", "unmute"
    )
    if any(k in q for k in whatsapp_triggers):
        selected_names.update({
            "send_whatsapp_message", "confirm_send_whatsapp", "open_whatsapp_web", "save_contact", "list_contacts", "open_application",
            "post_whatsapp_status", "customize_whatsapp_status", "confirm_post_whatsapp_status", "delete_whatsapp_status", "discard_whatsapp_status",
            "make_whatsapp_call", "end_whatsapp_call", "toggle_whatsapp_call_mute"
        })

    # System & Hardware & Brightness/Volume
    sys_triggers = (
        "volume", "sound", "awaz", "brightness", "light", "wifi", "bluetooth", 
        "battery", "charge", "settings", "shut", "restart", "sleep", "pc", "system"
    )
    if any(k in q for k in sys_triggers):
        selected_names.update({
            "set_system_volume", "set_system_brightness", "control_quick_setting", 
            "get_battery_status", "get_system_status", "get_system_specs", "shutdown_system"
        })

    # Timers, Alarms, Reminders
    timer_triggers = (
        "timer", "alarm", "remind", "reminder", "countdown", "ghanta", "minute"
    )
    if any(k in q for k in timer_triggers):
        selected_names.update({
            "set_timer", "cancel_timer", "list_timers", "set_alarm", "set_reminder"
        })

    # Memory
    mem_triggers = (
        "remember", "yad", "yaad", "preference", "pasand", "forget", "bhool", 
        "recall", "memory", "memories"
    )
    if any(k in q for k in mem_triggers):
        selected_names.update({
            "remember_information", "recall_memories", "forget_memory"
        })

    # Vision & Screenshots
    vision_triggers = (
        "screen", "monitor", "screenshot", "error dekho", "ye error", "kya chal raha", 
        "diagnose", "dekho", "look", "see", "capture"
    )
    if any(k in q for k in vision_triggers):
        selected_names.update({
            "inspect_screen", "capture_screenshot"
        })

    # Social & Creator Accounts
    social_triggers = (
        "post", "tweet", "linkedin", "twitter", "instagram", "youtube", "github", 
        "social", "draft", "publish", "account", "profile"
    )
    if any(k in q for k in social_triggers):
        selected_names.update({
            "get_creator_accounts_info", "inspect_creator_account", "draft_social_post", 
            "publish_social_post", "open_creator_link"
        })

    # Email & Communications Matrix
    email_triggers = (
        "email", "mail", "gmail", "inbox", "outlook", "hotmail", "dak", "khat", 
        "compose", "inboxes", "charo email", "chaaro email", "sari email", "saari email",
        "meri email", "mere email", "email check", "email open"
    )
    if any(k in q for k in email_triggers):
        selected_names.update({
            "open_creator_email", "get_creator_emails_summary", "open_creator_link"
        })

    # Autonomous Planning / Missions
    mission_triggers = (
        "plan", "mission", "goal", "autonomous", "maqsad", "step by step"
    )
    if any(k in q for k in mission_triggers):
        selected_names.update({
            "create_agent_plan", "execute_agent_mission", "stop_agent_mission"
        })

    # Autonomous Browser-Use Agent
    browser_agent_triggers = (
        "browser agent", "web agent", "browser-use", "autonomous browser",
        "daraz", "amazon", "scrape", "extract from web", "fill form", "price compare",
        "compare prices", "website per jao aur", "web task"
    )
    if any(k in q for k in browser_agent_triggers):
        selected_names.add("autonomous_browser_agent")

    filtered = [t for t in JARVIS_TOOLS_SCHEMA if t["function"]["name"] in selected_names]
    return filtered if filtered else JARVIS_TOOLS_SCHEMA
