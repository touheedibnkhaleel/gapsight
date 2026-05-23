"""
GapSight — main.py
App entry point only. Creates app, registers middleware, includes router.
All logic lives in api/, services/, models/, core/.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="GapSight API",
    description="Find what your users aren't telling you.",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
