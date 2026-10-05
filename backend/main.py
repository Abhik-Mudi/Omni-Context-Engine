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

PROMPT_TEMPLATE = """You are an expert developer assistant. You are provided with the developer's recent timeline, command and a terminal error. Analyze if the error is a direct result of the recent timeline actions. If it is unrelated (e.g., a global test suite failure), state that explicitly, ignore the timeline, and solve the localized code error. Below is the exact sequence \
of things they did leading up to the error, followed by the relevant code.

=== WORKFLOW TIMELINE (most recent last) ===
{timeline}

=== RELEVANT COMMAND ===
{command}

=== ERROR ===
{error_logs}

Based on the timeline and command, explain:
1. What the developer was most likely trying to build/change
2. The most probable root cause of this specific error (be concrete, cite the \
timeline event that likely caused it, not just the error message)
3. A concrete fix

Keep it under 200 words. Do not restate the error message back at me."""


@app.post("/api/event")
async def log_event(event: WorkEventModel, background_tasks: BackgroundTasks):
    con = get_db_connection()
    cursor = con.cursor()

    if event.payload["exit_code"] != 0:
        now = datetime.now().replace(microsecond=0)
        background_tasks.add_task(analyze_error, event.payload["command"], event.payload["logs"], now)
    
    cursor.execute(
        "INSERT INTO timeline_events (source, payload) VALUES (?, ?)",
        (event.source, json.dumps(event.payload)),
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

    except:
        print("Some error occurred")
        