#!/usr/bin/env python3
"""
Run the E.D.I.T.H. FastAPI server.

Usage:
    python run_server.py                 # Run on default (127.0.0.1:8000)
    python run_server.py --host 0.0.0.0  # Run on all interfaces
    python run_server.py --port 8080     # Run on custom port
"""

import sys
import uvicorn

if __name__ == "__main__":
    # Run the server with uvicorn
    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on file changes during development
        log_level="info"
    )
