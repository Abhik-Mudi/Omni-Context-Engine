from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import json
import requests

from backend.database import get_db_connection

app = FastAPI(title="Omni-Context Nerve Center")

class WorkEventModel(BaseModel):
    source: str
    payload: dict


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen-coder:latest"

PROMPT_TEMPLATE = """You are an expert developer assistant.

You are provided with:
1. The developer's recent timeline
2. The command they executed
3. The resulting terminal error

Your job is to determine whether the error was caused by something in the
recent timeline.

IMPORTANT RULES:
- Do NOT invent timeline events, code changes, or developer actions.
- Only claim that a timeline event caused the error when there is clear
  evidence connecting them.
- If the timeline does not explain the error, explicitly say that there is
  no established connection.
- A malformed command can itself be the root cause. Diagnose the command
  directly when appropriate.
- Do not force a timeline-based explanation when none exists.
- Distinguish between "the developer intended to..." and what can actually
  be inferred from the command.
- Do not hallucinate missing context.

=== WORKFLOW TIMELINE (most recent last) ===
{timeline}

=== RELEVANT COMMAND ===
{command}

=== ERROR ===
{error_logs}

Based on the available evidence, explain:

1. What the developer was most likely trying to do.
2. Whether the timeline caused the error. If yes, identify the specific
   timeline event and explain the causal connection. If no, explicitly state
   that there is no established timeline cause.
3. The most probable root cause of the error.
4. A concrete fix.

Keep it under 200 words.
Do not restate the error message unnecessarily.
"""


@app.post("/api/event")
async def log_event(event: WorkEventModel, background_tasks: BackgroundTasks):
    con = get_db_connection()
    cursor = con.cursor()

    now = datetime.now().replace(microsecond=0)
    if event.payload["exit_code"] != 0:
        background_tasks.add_task(analyze_error, event.payload["command"], event.payload["logs"], now)
    
    cursor.execute(
        "INSERT INTO timeline_events (timestamp, source, payload) VALUES (?, ?, ?)",
        (now, event.source, json.dumps(event.payload)),
    )
    
    con.commit()
    event_id = cursor.lastrowid
    con.close()

    print(f"[{event.source.upper()}] Logged: {event.payload}")
    return {"status": "success", "event_id": event_id}


def analyze_error(command, error_logs, now):
    prompt = PROMPT_TEMPLATE.format(
        timeline = now,
        command = command,
        error_logs = error_logs
    )
    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=data)

        print(response.json()["response"])

    except requests.exceptions.RequestException as e:
        print("Some error occurred", e)
        