from fastapi import APIRouter
from app.db.supabase import get_supabase
from app.config import get_settings
from qdrant_client import QdrantClient

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Verifies connectivity to Supabase PostgreSQL and Qdrant.
    """
    settings = get_settings()
    results = {"status": "healthy", "db_ok": False, "vector_ok": False}

    # Check Supabase PostgreSQL
    try:
        client = get_supabase()
        client.table("documents").select("id").limit(1).execute()
        results["db_ok"] = True
    except Exception as e:
        results["db_ok"] = False
        results["db_error"] = str(e)

    # Check Qdrant
    try:
        qdrant = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        qdrant.get_collections()
        results["vector_ok"] = True
    except Exception as e:
        results["vector_ok"] = False
        results["vector_error"] = str(e)

    if not results["db_ok"] or not results["vector_ok"]:
        results["status"] = "degraded"

    return results
