"""
Autonomous Startup OS ("Founder-in-a-Box") Server Launcher
Runs the FastAPI server and serves the Master Control Dashboard.

Usage:
    .venv/bin/python run.py
    or
    python run.py (with active venv)
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"\n🚀 Launching Autonomous Startup OS ('Founder-in-a-Box') on http://localhost:{port}")
    print(f"📊 Master Control Dashboard available at: http://localhost:{port}")
    print(f"📡 API Documentation available at: http://localhost:{port}/docs\n")
    uvicorn.run("backend.app:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()
