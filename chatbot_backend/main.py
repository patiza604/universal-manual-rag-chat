# main.py
from app.startup import app
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Starting FastAPI on port {port}...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)

