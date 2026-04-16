"""
Jerry – Powertech Analysis Tools
FastAPI backend entry point
"""

import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import merge, maxmin, avg, asr, validation, plot, cycle_viewer, fuel_systems

app = FastAPI(
    title="Jerry – Powertech Analysis Tools API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merge.router,        prefix="/api/merge",        tags=["merge"])
app.include_router(maxmin.router,       prefix="/api/maxmin",       tags=["maxmin"])
app.include_router(avg.router,          prefix="/api/avg",          tags=["avg"])
app.include_router(asr.router,          prefix="/api/asr",          tags=["asr"])
app.include_router(validation.router,   prefix="/api/validation",   tags=["validation"])
app.include_router(plot.router,         prefix="/api/plot",         tags=["plot"])
app.include_router(cycle_viewer.router, prefix="/api/cycle-viewer", tags=["cycle_viewer"])
app.include_router(fuel_systems.router, prefix="/api/fuel-systems", tags=["fuel_systems"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
