from fastapi import FastAPI
from pydantic import BaseModel
from database import get_db_connection
import sqlite3

app = FastAPI(title="Omni-Context Nerve Center")

class WorkEventModel(BaseModel):
    source: str
    payload: str

@app.post("/api/event")
async def log_event(event: WorkEventModel):
    con=get_db_connection()
    cursor=con.cursor()

    cursor.execute(
        "INSERT INTO timeline_events (source, payload) VALUES (?, ?)",
        (event.source, event.payload)
    )

    con.commit()
    event_id = cursor.lastrowid
    con.close()

    print(f"[{event.source.upper()}] Logged: {event.payload}")
    return { "status": "success", "event_id": event_id }