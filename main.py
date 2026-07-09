import os
import sys
from pathlib import Path

# Ensure project root is in Python path
sys.path.append(str(Path(__file__).resolve().parent))

# Export the FastAPI instance as 'app' for Vercel / Uvicorn serverless discovery
from backend.app import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
