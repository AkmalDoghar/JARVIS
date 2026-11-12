import os
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


def get_browser_llm():
    """
    Resolve the best available LLM for Browser-Use in order of preference:
    1. OpenAI (gpt-4o-mini / gpt-4o)
    2. OpenRouter (gemini-2.0-flash or gpt-4o-mini)
    3. Gemini API direct
    4. Groq (llama-3.3-70b)
    """
    from browser_use.llm import ChatOpenAI

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and not openai_key.startswith("your_"):
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model, api_key=openai_key)

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and not openrouter_key.startswith("your_"):
        return ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free"),
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and not gemini_key.startswith("your_"):
        return ChatOpenAI(
            model="gemini-1.5-flash",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=gemini_key,
        )

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and not groq_key.startswith("your_"):
        return ChatOpenAI(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
        )

    raise ValueError("No valid AI API key found for Browser-Use. Please configure OPENAI_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY in .env.")


async def run_autonomous_browser_async(
    task: str,
    visible: bool = True,
    max_steps: int = 15,
    kind: str = "chromium"
) -> Dict[str, Any]:
    """
    Run an autonomous browser agent with browser-use.
    """
    from browser_use import Agent, Browser

    llm = get_browser_llm()

    # Browser instance
    if kind == "chrome":
        browser = Browser("chrome")
    else:
        browser = Browser("chromium", headless=not visible)

    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        highlight_actions=True,
    )

    try:
        history = await agent.run(max_steps=max_steps)
        final_text = history.final_result() if hasattr(history, "final_result") else "Task finished."
        is_success = history.is_successful() if hasattr(history, "is_successful") else True
        num_steps = history.number_of_steps() if hasattr(history, "number_of_steps") else len(history.history)

        return {
            "success": is_success,
            "result": final_text,
            "steps_taken": num_steps,
            "task": task,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "result": f"Browser agent encountered an error: {str(e)}",
            "task": task,
        }


def execute_autonomous_browser(task: str, visible: bool = True, max_steps: int = 15) -> Dict[str, Any]:
    """
    Synchronous entrypoint for JARVIS tool registry.
    Handles running inside an existing asyncio loop or creating a new one.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(run_autonomous_browser_async(task, visible, max_steps)))
                return future.result(timeout=180)
        else:
            return asyncio.run(run_autonomous_browser_async(task, visible, max_steps))
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "result": f"Execution failed: {str(e)}",
            "task": task,
        }
