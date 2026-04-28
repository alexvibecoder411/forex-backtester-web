"""
backend/main.py
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import database as db
from config import CORS_ORIGINS, HOST, PORT
from routers import auth, channels, backtest, results, live


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.get_db()
    print(f"✅ Database ready")
    yield
    # Shutdown
    await db.close_db()
    print("Database closed")


app = FastAPI(
    title="Forex Signal Backtester API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(channels.router)
app.include_router(backtest.router)
app.include_router(results.router)
app.include_router(live.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
