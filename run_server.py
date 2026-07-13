#!/usr/bin/env python3
"""
NeuroSense AI — Server Launcher
Starts the FastAPI REST API Server on http://localhost:8000
"""
import uvicorn

import socket

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

if __name__ == "__main__":
    port = 8080 if is_port_open(8080) else 8000
    if not is_port_open(port):
        port = 8081
    print("=" * 80)
    print("  Starting NeuroSense AI Dual-Modality Server...")
    print(f"  Web Dashboard & REST API: http://localhost:{port}")
    print(f"  Interactive API Docs:     http://localhost:{port}/docs")
    print("=" * 80)
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=True)
