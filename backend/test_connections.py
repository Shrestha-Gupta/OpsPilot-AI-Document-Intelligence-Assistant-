r"""
Phase 1 connectivity test script.
Run this after setting up your .env to verify all external services connect correctly.

Usage:
  cd backend
  venv\Scripts\activate
  python test_connections.py
"""
import os
import sys

# Ensure UTF-8 output encoding for emojis on Windows PowerShell
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Load .env
from dotenv import load_dotenv
load_dotenv()

def check_env():
    required = [
        "SUPABASE_URL", "SUPABASE_SERVICE_KEY",
        "QDRANT_URL", "QDRANT_API_KEY",
        "GEMINI_API_KEY", "GROQ_API_KEY",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("   Create backend/.env from backend/.env.example and fill in the values.")
        sys.exit(1)
    print("✅ All required environment variables present")


def test_supabase():
    print("\n─── Testing Supabase ───────────────────────────")
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        client = create_client(url, key)
        result = client.table("documents").select("id").limit(1).execute()
        print(f"✅ Supabase PostgreSQL connected | documents table exists")
    except Exception as e:
        print(f"❌ Supabase failed: {e}")
        print("   Make sure you ran the SQL migration in your Supabase project.")


def test_supabase_storage():
    print("\n─── Testing Supabase Storage ───────────────────")
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        bucket = os.getenv("SUPABASE_BUCKET_NAME", "pdfs")
        client = create_client(url, key)
        buckets = client.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        if bucket in bucket_names:
            print(f"✅ Supabase Storage bucket '{bucket}' exists")
        else:
            print(f"⚠️  Bucket '{bucket}' not found. Available: {bucket_names}")
            print("   Create the bucket in Supabase Dashboard → Storage → New bucket")
    except Exception as e:
        print(f"❌ Supabase Storage failed: {e}")


def test_qdrant():
    print("\n─── Testing Qdrant ─────────────────────────────", flush=True)
    try:
        from qdrant_client import QdrantClient
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        collection = os.getenv("QDRANT_COLLECTION_NAME", "opspilot_chunks")
        client = QdrantClient(url=url, api_key=api_key, timeout=5.0)
        collections = [c.name for c in client.get_collections().collections]
        print(f"✅ Qdrant connected | Collections: {collections or '(none yet)'}", flush=True)
        if collection not in collections:
            print(f"   Collection '{collection}' will be created on first server startup.", flush=True)
    except Exception as e:
        print(f"❌ Qdrant failed: {e}", flush=True)
        print("   Check your QDRANT_URL and QDRANT_API_KEY.", flush=True)


def test_gemini():
    print("\n─── Testing Gemini Embeddings ──────────────────", flush=True)
    try:
        from google import genai
        from google.genai import types
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        dims = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
        client = genai.Client(api_key=api_key)
        res = client.models.embed_content(
            model=model,
            contents="test connection",
            config=types.EmbedContentConfig(
                task_type="retrieval_query",
                output_dimensionality=dims,
            ),
        )
        embedding = res.embeddings[0].values
        print(f"✅ Gemini Embeddings connected | dimensions={len(embedding)}", flush=True)
    except Exception as e:
        print(f"❌ Gemini failed: {e}", flush=True)


def test_groq():
    print("\n─── Testing Groq LLM ───────────────────────────")
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        result = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'OK' in one word."}],
            max_tokens=64,
        )
        answer = result.choices[0].message.content
        print(f"✅ Groq LLM connected | response='{answer.strip()}'")
    except Exception as e:
        print(f"❌ Groq failed: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("  OpsPilot V2 — Phase 1 Connectivity Test")
    print("=" * 50)
    check_env()
    test_supabase()
    test_supabase_storage()
    test_qdrant()
    test_gemini()
    test_groq()
    print("\n" + "=" * 50)
    print("  Done. Fix any ❌ above before proceeding.")
    print("=" * 50)
