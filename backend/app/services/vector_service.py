"""
Qdrant vector database service.
Provides singleton client, collection management, upserting chunks with metadata,
scoped deletion by document_id, and similarity search.
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    FilterSelector,
    PayloadSchemaType,
)

from app.config import get_settings
from app.core.exceptions import AppError

logger = logging.getLogger("opspilot.vector")

_qdrant_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Return the singleton Qdrant client, creating it on first call."""
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=5.0,
        )
        logger.info("Qdrant client created")
    return _qdrant_client


def ensure_collection_exists() -> None:
    """
    Create the Qdrant collection if it doesn't already exist,
    and ensure the required payload index on 'document_id' is present.
    Safe and idempotent to call on every startup.
    """
    settings = get_settings()
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection_name

    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created Qdrant collection: {collection_name} (dim={settings.embedding_dimensions})")
    else:
        logger.info(f"Qdrant collection already exists: {collection_name}")

    # Ensure document_id keyword index exists for filtered searches and deletions
    try:
        col_info = client.get_collection(collection_name)
        payload_schema = getattr(col_info, "payload_schema", {}) or {}
        if "document_id" not in payload_schema:
            client.create_payload_index(
                collection_name=collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info(f"Created keyword payload index on 'document_id' in {collection_name}")
        else:
            logger.info(f"Payload index on 'document_id' already present in {collection_name}")
    except Exception as e:
        logger.warning(f"Could not verify/create payload index on 'document_id': {e}")


class VectorService:
    def __init__(self):
        self.settings = get_settings()
        self.client = get_qdrant_client()
        self.collection_name = self.settings.qdrant_collection_name

    def upsert_chunks(
        self,
        document_id: str,
        document_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        batch_size: int = 250,
    ) -> int:
        """
        Upsert chunk points with embeddings and metadata payloads into Qdrant in efficient batches.
        Default batch size 250 minimizes HTTP round-trips while maintaining reliability.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) does not match embedding count ({len(embeddings)})")

        if not chunks:
            return 0

        points: List[PointStruct] = []
        for chunk, embedding in zip(chunks, embeddings):
            point_id = str(uuid.uuid4())
            payload = {
                "document_id": str(document_id),
                "document_name": document_name,
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "chunk_text": chunk["chunk_text"],
                "char_count": chunk["char_count"],
            }
            points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

        total_upserted = 0
        total_batches = (len(points) + batch_size - 1) // batch_size
        for batch_num, i in enumerate(range(0, len(points), batch_size), start=1):
            batch = points[i : i + batch_size]
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                )
                total_upserted += len(batch)
                logger.info(
                    "Indexed Qdrant batch %d/%d (%d/%d points) for doc %s",
                    batch_num, total_batches, total_upserted, len(points), document_id,
                )
            except Exception as e:
                logger.error(f"Failed to upsert points batch {i}..{i+len(batch)}: {e}")
                raise AppError(
                    message=f"Failed to store vectors in database: {str(e)}",
                    status_code=500,
                    error_code="VECTOR_UPSERT_FAILED",
                )

        logger.info(f"Upserted {total_upserted} chunks into Qdrant for document {document_id}")
        return total_upserted

    def delete_document_chunks(self, document_id: str) -> None:
        """
        Delete all points associated with a specific document_id.
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="document_id",
                                match=MatchValue(value=str(document_id)),
                            )
                        ]
                    )
                ),
            )
            logger.info(f"Deleted vector chunks for document_id={document_id}")
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
            # Non-blocking for deletions
            pass

    def search_chunks(
        self,
        query_vector: List[float],
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search in Qdrant.
        Optionally scopes to a list of document_ids.
        """
        query_filter: Optional[Filter] = None
        if document_ids:
            clean_ids = [str(d) for d in document_ids if d]
            if len(clean_ids) == 1:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=clean_ids[0]),
                        )
                    ]
                )
            elif len(clean_ids) > 1:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchAny(any=clean_ids),
                        )
                    ]
                )

        try:
            # Note: in modern qdrant-client, search or query_points is used
            if hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                )
            else:
                query_res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                )
                results = query_res.points

            matched_chunks = []
            for hit in results:
                payload = hit.payload or {}
                matched_chunks.append({
                    "score": getattr(hit, "score", 0.0),
                    "document_id": payload.get("document_id"),
                    "document_name": payload.get("document_name"),
                    "page_number": payload.get("page_number"),
                    "chunk_text": payload.get("chunk_text"),
                    "chunk_index": payload.get("chunk_index"),
                })
            return matched_chunks
        except Exception as e:
            logger.error(f"Qdrant vector search failed: {e}")
            raise AppError(
                message=f"Vector search failed: {str(e)}",
                status_code=500,
                error_code="VECTOR_SEARCH_FAILED",
            )


_vector_service: VectorService | None = None


def get_vector_service() -> VectorService:
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
