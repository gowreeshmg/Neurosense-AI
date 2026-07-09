#!/usr/bin/env python3
"""
NeuroSense AI — Server Launcher
Starts the FastAPI REST API Server on http://localhost:8000
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 80)
    print("  Starting NeuroSense AI Dual-Modality Server...")
    print("  Web Dashboard & REST API: http://localhost:8000")
    print("  Interactive API Docs:     http://localhost:8000/docs")
    print("=" * 80)
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
