from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from memory.store import init_db
from memory.context import make_context
from server.routers import chat, knowledge, learning

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the FastAPI app."""
    # Startup
    init_db()

    # Make app state available
    app.state.context = make_context()

    yield

    # Shutdown (cleanup if needed)
    pass


app = FastAPI(
    title="E.D.I.T.H.",
    description="Extended Distributed Intelligence Through Humanistic Interaction",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(learning.router)


@app.get("/")
def root():
    return {"message": "E.D.I.T.H. is online"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "edith"}
