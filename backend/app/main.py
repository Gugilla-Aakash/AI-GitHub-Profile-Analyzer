from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analyze, chat, report, search

app = FastAPI(
    title="GitHub Profile Analyzer API",
    version="1.0.0",
    description="Backend API for analyzing Github profiles.",
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js dev server
    "http://127.0.0.1:3000",
]

# Cors configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers with clean /api/v1 prefixes
app.include_router(
    search.router,
    prefix="/api/v1/search",
    tags=["Search"],
)
app.include_router(
    analyze.router,
    prefix="/api/v1/analyze",
    tags=["Analyzer"],
)
app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["Chat"],
)
app.include_router(
    report.router,
    prefix="/api/v1/report",
)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "service": "github-analyzer Backend",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": "github-analyzer Backend",
    }
