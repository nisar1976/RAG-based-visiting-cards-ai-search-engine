import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.models import Base
from backend.db.session import engine
from backend.rag import embeddings
from backend.api import routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager: startup and shutdown.
    Validates OpenAI embedder API key at startup.
    Triggers auto-indexing in background if needed.
    """
    # Startup
    logger.info("Starting up...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Load OpenAI embedder client
    try:
        app.state.embedder = embeddings.load_model()
        logger.info("OpenAI embedder client initialized")
    except Exception as e:
        logger.warning(f"Failed to load embedder: {e}")
        app.state.embedder = None

    # Initialize indexing state
    app.state.indexing_status = "idle"  # "idle" | "running" | "done" | "error"
    app.state.cards_indexed = 0
    app.state.total_cards = 0
    app.state.indexing_error = None

    # Check if re-indexing is needed
    try:
        from backend.db.session import AsyncSessionLocal
        from backend.db import crud as _crud
        async with AsyncSessionLocal() as _db:
            _all = await _crud.get_all_cards(_db)
            _db_empty = len(_all) == 0
    except Exception as e:
        logger.error(f"Failed to check database: {e}")
        _db_empty = True

    needs_index = _db_empty

    if needs_index:
        async def _auto_index():
            app.state.indexing_status = "running"
            app.state.indexing_error = None
            try:
                from backend.utils.image_loader import run_pipeline
                result = await run_pipeline(app)
                if result.get("status") == "ok" and result.get("cards_indexed", 0) > 0:
                    app.state.indexing_status = "done"
                    logger.info(f"Auto-indexing complete: {result}")
                else:
                    app.state.indexing_status = "error"
                    app.state.indexing_error = result.get("message", "No cards indexed")
                    logger.warning(f"Auto-indexing completed but no cards indexed: {result}")
            except Exception as e:
                logger.error(f"Auto-indexing failed: {e}", exc_info=True)
                app.state.indexing_status = "error"
                app.state.indexing_error = str(e)

        asyncio.create_task(_auto_index())
        logger.info(f"Auto-indexing needed (DB empty: {_db_empty}). Starting in background...")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title="Visiting Card AI",
    description="Offline RAG-based visiting card search system",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "embedder_ready": hasattr(app.state, 'embedder') and app.state.embedder is not None,
        "indexing_status": getattr(app.state, 'indexing_status', 'idle'),
        "cards_indexed": getattr(app.state, 'cards_indexed', 0),
        "total_cards": getattr(app.state, 'total_cards', 0),
        "indexing_error": getattr(app.state, 'indexing_error', None),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
