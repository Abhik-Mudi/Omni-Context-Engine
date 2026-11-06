from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import json
import requests

from backend.database import get_db_connection, init_db
from backend.prompts import OLLAMA_URL, MODEL, PROMPT_TEMPLATE

# Starting the app and sqlite database
app = FastAPI(title="Omni-Context Nerve Center")
init_db()

class WorkEventModel(BaseModel):
    source: str
    payload: dict


# Log the event in the database if any command is run
@app.post("/api/event")
async def log_event(event: WorkEventModel, background_tasks: BackgroundTasks):
    # Get the database connection
    con = get_db_connection()
    cursor = con.cursor()

    now = datetime.now().replace(microsecond=0)

    # Insert a new row in the database
    cursor.execute(
        "INSERT INTO timeline_events (timestamp, source, payload) VALUES (?, ?, ?)",
        (now, event.source, json.dumps(event.payload)),
    )
    
    con.commit()
    event_id = cursor.lastrowid
    con.close()

    # Analyze if any error is there. Set the task in the background.
    if event.payload["exit_code"] != 0:
        background_tasks.add_task(analyze_error, event.payload["command"], event.payload["logs"], now, event_id)

    print(f"[{event.source.upper()}] Logged: {event.payload}")
    return {"status": "success", "event_id": event_id}


# Analyze the error with local llm and set the ai_analyze field with the result
def analyze_error(command, error_logs, now, event_id):
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
        # Get the ai response
        response = requests.post(OLLAMA_URL, json=data)

        with get_db_connection() as con:
            cursor = con.cursor()

            result = response.json()["response"]

            # Update the row with ai_analysis field
            cursor.execute(
                "UPDATE timeline_events set ai_analysis = ? where id = ?",
                (result, event_id )
            )

        print(response.json()["response"])

    except requests.exceptions.RequestException as e:
        print("Some error occurred", e)
        