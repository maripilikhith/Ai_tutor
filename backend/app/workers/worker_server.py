"""
Dummy Web Server for Background Worker

This file creates a tiny FastAPI server whose ONLY job is to bind to a $PORT
so that Render's Free Tier "Web Service" doesn't crash it. 
While the server listens for traffic on the main thread, it spawns the actual 
worker queue processor on a background thread.
"""

import os
import asyncio
import threading
from fastapi import FastAPI
from app.workers.runner import run_worker
import uvicorn

app = FastAPI(title="Background Worker Service")

def start_worker_thread():
    """Runs the infinite worker loop in a dedicated thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Start the worker with a 10 second poll interval
    loop.run_until_complete(run_worker(poll_interval=10))

@app.on_event("startup")
async def on_startup():
    """Start the actual background worker thread when the dummy server boots."""
    print("[DummyServer] Starting background worker thread...")
    worker_thread = threading.Thread(target=start_worker_thread, daemon=True)
    worker_thread.start()

@app.get("/")
def health_check():
    """Dummy health check endpoint for Render/pinger websites."""
    return {"status": "worker_running", "message": "The background worker is active."}

if __name__ == "__main__":
    # Render passes the port in the $PORT env variable. Default to 8080 locally.
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
