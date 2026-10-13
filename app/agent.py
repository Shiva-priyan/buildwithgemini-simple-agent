# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import preload_memory, load_memory
from google.genai import types

from .tools import list_meals, get_meal_by_id, add_meal, lookup_barcode


MODEL = "gemini-3.8-flash"


def _create_code_executor() -> AgentEngineSandboxCodeExecutor:
    """Initializes AgentEngineSandboxCodeExecutor from deployment_metadata.json if available."""
    metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
    agent_engine_resource_name = None
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                agent_engine_resource_name = data.get("agent_engine_resource_name")
        except Exception:
            pass

    return AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=agent_engine_resource_name
    )


code_executor = _create_code_executor()


import logging
import re
from google.adk.memory.memory_entry import MemoryEntry

logger = logging.getLogger("fitfuel.agent")

_ALLERGY_REGEX = re.compile(
    r"\b(?:allerg(?:y|ies|ic)|intoleran(?:t|ce)|celiac|anaphylax(?:is|tic))\b",
    re.IGNORECASE,
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends the session events to the Memory Bank service for persistent memory generation,

    ensuring all user allergies and dietary restrictions are immediately committed to memory.
    """
    try:
        # Check if recent user events mention allergies or intolerances
        session = getattr(callback_context._invocation_context, "session", None)
        if session and session.events:
            for event in reversed(session.events[-4:]):
                if event.content and event.content.role == "user":
                    for part in event.content.parts:
                        text = part.text or ""
                        if _ALLERGY_REGEX.search(text):
                            allergy_fact = f"User Dietary/Allergy Profile: {text.strip()}"
                            try:
                                await callback_context.add_memory(
                                    memories=[
                                        MemoryEntry(
                                            content=types.Content(
                                                role="user",
                                                parts=[types.Part.from_text(text=allergy_fact)],
                                            )
                                        )
                                    ]
                                )
                                logger.info("Committed user allergy directly to memory bank: %s", allergy_fact)
                            except Exception as mem_err:
                                logger.warning("Could not add explicit allergy memory: %s", mem_err)

        await callback_context.add_session_to_memory()
    except Exception as exc:
        # Memory addition is best-effort and should not break active conversation flow
        logger.warning("generate_memories_callback encountered error: %s", exc)
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are FitFuel Coach, an intelligent wellness, nutrition, and fitness AI assistant.\n"
        "CORE ALLERGY MEMORY RULE:\n"
        "- ALWAYS identify, confirm, and remember all user food allergies, intolerances, and dietary restrictions "
        "(e.g., peanuts, tree nuts, shellfish, dairy, lactose, gluten/celiac, eggs, soy, wheat, sesame).\n"
        "- Whenever the user discloses an allergy or intolerance, explicitly acknowledge and confirm that you have "
        "committed it to their long-term memory profile.\n"
        "- Check preloaded memory and past context for recorded allergies before recommending any meal, recipe, or food item. "
        "NEVER recommend meals or ingredients that conflict with known user allergies.\n"
        "- If you need to recall or verify stored dietary restrictions and allergy information, call `load_memory`.\n\n"
        "You also have access to:\n"
        "1. A persistent Memory Bank that stores user fitness goals, dietary preferences, past check-ins, and health logs.\n"
        "2. A Firestore backend containing a catalog of curated meals and recipes via `list_meals`, `get_meal_by_id`, and `add_meal`.\n"
        "3. A real-time public food database via `lookup_barcode` (Open Food Facts) to fetch verified nutrition data.\n"
        "4. A secure Agent Platform Python sandbox via code execution to perform complex calculations, such as "
        "BMR (Basal Metabolic Rate), TDEE, macronutrient distributions, deficit/surplus projections, or statistical modeling.\n"
        "When performing non-trivial math or health calculations, write and execute Python code in the sandbox to ensure exact accuracy."
    ),
    tools=[preload_memory, load_memory, get_weather, get_current_time, list_meals, get_meal_by_id, add_meal, lookup_barcode],
    after_agent_callback=generate_memories_callback,
    code_executor=code_executor,
)

app = App(
    root_agent=root_agent,
    name="app",
)
