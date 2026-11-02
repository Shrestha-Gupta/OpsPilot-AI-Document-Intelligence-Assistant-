import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.exceptions import AppError, app_error_handler, generic_error_handler
from app.api.v1.health import router as health_router
from app.api.v1.documents import router as documents_router
from app.api.v1.conversations import router as conversations_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("opspilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: initialize and validate all external service connections.
    Shutdown: cleanup if needed.
    """
    settings = get_settings()
    logger.info(f"Starting OpsPilot V2 | env={settings.app_env}")

    # Validate required settings exist (will raise if missing from env)
    required = [
        ("SUPABASE_URL", settings.supabase_url),
        ("SUPABASE_SERVICE_KEY", settings.supabase_service_key),
        ("QDRANT_URL", settings.qdrant_url),
        ("QDRANT_API_KEY", settings.qdrant_api_key),
        ("GEMINI_API_KEY", settings.gemini_api_key),
        ("GROQ_API_KEY", settings.groq_api_key),
    ]
    missing = [name for name, val in required if not val]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    logger.info("All required environment variables present")

    # Initialize Supabase client (singleton — will be reused per request)
    from app.db.supabase import get_supabase
    try:
        get_supabase()
        logger.info("Supabase client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise

    # Verify Qdrant collection in background task without blocking Uvicorn's port binding
    async def init_qdrant_background():
        from app.services.vector_service import ensure_collection_exists
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, ensure_collection_exists)
            logger.info(f"Qdrant connected and verified | collection={settings.qdrant_collection_name}")
        except Exception as e:
            logger.warning(
                f"Non-fatal: Qdrant collection verification failed on startup: {e}. "
                "The server is running; requests requiring Qdrant will retry on demand."
            )

    asyncio.create_task(init_qdrant_background())

    logger.info("OpsPilot V2 startup complete — ready to serve requests")
    yield
    logger.info("OpsPilot V2 shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="OpsPilot V2 API",
        description="AI Document Intelligence Assistant",
        version="2.0.0",
        docs_url="/docs" if settings.app_env == "development" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # CORS — only allow the configured frontend URL
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Error handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # Routers
    app.include_router(health_router)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(conversations_router, prefix="/api/v1")

    return app


app = create_app()
