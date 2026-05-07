from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.routes import ingest, patients, alerts, location, chat
from app import ml


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load ML models at startup so first request isn't slow
    ml._load_models()
    settings = get_settings()
    print("[OK] ML models loaded")
    print(f"[OK] Supabase: {'connected' if settings.supabase_enabled else 'not configured (in-memory mode)'}")
    print(f"[OK] Chatbot:  {'enabled' if settings.chatbot_enabled else 'disabled (set OPENAI_API_KEY)'}")
    yield


settings = get_settings()

app = FastAPI(
    title="Vivre API",
    description="AI-powered health monitoring backend for elderly care",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router,   prefix="/api/v1", tags=["Ingest"])
app.include_router(patients.router, prefix="/api/v1", tags=["Patients"])
app.include_router(alerts.router,   prefix="/api/v1", tags=["Alerts"])
app.include_router(location.router, prefix="/api/v1", tags=["Location"])
app.include_router(chat.router,     prefix="/api/v1", tags=["Chat"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Vivre API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "supabase": settings.supabase_enabled,
        "chatbot": settings.chatbot_enabled,
    }
