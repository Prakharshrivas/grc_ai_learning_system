"""FastAPI application entry point for the GRC AI Learning System."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from database.db import init_db

app = FastAPI(
    title="GRC AI Learning System",
    description="AI-guided video learning platform for GRC compliance workflows",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()
    from database.db import get_connection
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM workflows").fetchone()["c"]
    conn.close()
    if count == 0:
        from database.seed import seed_all
        seed_all()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "grc-ai-learning-system"}
