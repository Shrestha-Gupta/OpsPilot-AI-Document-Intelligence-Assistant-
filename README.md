# OpsPilot – AI Document Intelligence Assistant

> A production-oriented RAG assistant for asking questions across organizational PDFs, comparing information between documents, and tracing answers back to source pages.

[Live Demo](https://frontend-rho-indol-98.vercel.app) 

---

## 1. What is OpsPilot?

OpsPilot turns a collection of internal PDF documents into a searchable, conversational knowledge base.

Instead of manually searching through SOPs, reports, policies, manuals, or other operational documents, a user can upload PDFs and ask questions in natural language. OpsPilot retrieves relevant document passages, sends only grounded context to the LLM, and returns an answer with source-document and page-level citations.

### Core workflows

- **Ask Documents** — ask questions across one or multiple PDFs.
- **Compare Information** — analyze similarities, differences, and relationships across documents.
- **Verify Evidence** — trace generated answers back to retrieved source passages and page references.
- **Conversational Follow-ups** — continue a conversation without repeating the full context manually.

The product is intentionally focused on **document-grounded intelligence**, rather than being a general-purpose chatbot.

---

## 2. Problem Statement

Important organizational information is often distributed across multiple documents. Finding a specific answer can require opening several PDFs, locating the relevant sections, comparing statements, and manually verifying the source.

OpsPilot addresses this retrieval problem by combining:

1. Persistent PDF storage
2. Text extraction and chunking
3. Semantic embeddings
4. Vector retrieval
5. LLM-based grounded answer generation
6. Conversation persistence
7. Source/page-level evidence

The result is a workflow designed to make document-based information retrieval faster, contextual, and traceable.

---

## 3. Live Deployment

| Component | Deployment | URL |
|---|---|---|
| Frontend | Vercel | https://frontend-rho-indol-98.vercel.app |
| Backend | Render | https://opspilot-v2.onrender.com |
| Health Check | Render | https://opspilot-v2.onrender.com/health |

The application is deployed as a React/Vite frontend backed by a FastAPI service. Persistent document storage and application data are handled by Supabase, while Qdrant provides persistent vector search.

---

## 4. Architecture

```text
                         ┌────────────────────────────┐
                         │       React + Vite         │
                         │   TypeScript + Tailwind    │
                         └─────────────┬──────────────┘
                                       │ HTTPS / REST
                                       ▼
                         ┌────────────────────────────┐
                         │        FastAPI API         │
                         │   Documents / Chat /      │
                         │   Conversations / Health  │
                         └───────┬───────────┬────────┘
                                 │           │
                 ┌───────────────┘           └────────────────┐
                 ▼                                            ▼
      ┌─────────────────────┐                       ┌─────────────────────┐
      │      Supabase       │                       │     Qdrant Cloud    │
      │                     │                       │                     │
      │ PostgreSQL          │                       │ Vector collection   │
      │ Document metadata   │                       │ opspilot_chunks     │
      │ Conversations       │                       │ 768-dim vectors     │
      │ Messages            │                       │ cosine similarity   │
      │ Storage: PDFs       │                       └──────────▲──────────┘
      └─────────────────────┘                                  │
                                                               │
                                                     ┌─────────┴─────────┐
                                                     │ Gemini Embeddings │
                                                     │ gemini-embedding- │
                                                     │ 001               │
                                                     └───────────────────┘

     Ingestion: PDF → PyMuPDF → chunks → Gemini embeddings → Qdrant

     Query: question → Gemini query embedding → Qdrant retrieval
                    → grounded context → Groq LLM → answer + citations
```

---

## 5. End-to-End Data Flow

### Document ingestion

```text
PDF Upload
   ↓
Supabase Storage
   ↓
PyMuPDF text extraction
   ↓
Text validation
   ↓
Chunking
   ↓
Gemini document embeddings
   ↓
L2 normalization
   ↓
Qdrant upsert
   ↓
Document marked Ready
```

If extraction or indexing fails, the document is marked **Failed** and the original error is persisted instead of leaving the document indefinitely in `Processing`.

### Question answering

```text
User Question
      ↓
Conversation Context
      ↓
Gemini query embedding
      ↓
Qdrant similarity search
      ↓
Top relevant chunks
      ↓
Grounded prompt
      ↓
Groq — openai/gpt-oss-120b
      ↓
Answer
      ↓
Source document + page citations
```

---

## 6. Tech Stack

### Frontend

- React 19
- Vite
- TypeScript
- Tailwind CSS
- Axios
- React Markdown + GitHub Flavored Markdown
- Lucide React

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic / Pydantic Settings

### Document Processing

- PyMuPDF for PDF text extraction
- `langchain-text-splitters` for text chunking

### AI

- **Gemini `gemini-embedding-001`** — embeddings only
- **Groq `openai/gpt-oss-120b`** — answer generation only

The application does **not** use the OpenAI API.

### Data & Infrastructure

- Supabase PostgreSQL — document metadata, conversations, and messages
- Supabase Storage — persistent PDF files
- Qdrant Cloud — persistent vector database
- Vercel — frontend deployment
- Render — backend deployment

---

## 7. Chunking Strategy

The current ingestion configuration uses:

| Parameter | Value |
|---|---:|
| Chunk size | 800 |
| Chunk overlap | 150 |
| Retrieval top-k | 5 |
| Conversation history | 10 messages |
| Maximum PDF size | 20 MB |
| Maximum files per upload | 5 |

### Why overlap?

A small overlap helps preserve context when an important sentence, definition, or list crosses a chunk boundary. Without overlap, retrieval can return an incomplete fragment even when the surrounding information is relevant.

### Why 800 characters?

The chunk size is a practical compromise between retrieval precision and contextual completeness. Smaller chunks can improve specificity but may lose surrounding context; larger chunks can improve context but increase irrelevant text in the generation prompt.

The values are configuration-driven so they can be tuned without changing the application architecture.

---

## 8. Embedding & Retrieval Strategy

OpsPilot uses Gemini embeddings for semantic retrieval.

- Model: `gemini-embedding-001`
- Dimensions: 768
- Document task: `retrieval_document`
- Query task: `retrieval_query`
- Vectors are L2-normalized
- Qdrant distance metric: cosine similarity

### Why Qdrant?

Qdrant was selected instead of an in-process vector index because the deployed application needs vector data to persist independently of the backend process. This avoids rebuilding an in-memory index whenever the service restarts and provides metadata filtering for document-scoped retrieval.

The collection uses a keyword payload index on `document_id`, allowing retrieval to be scoped to selected documents.

---

## 9. Grounded Generation & Citations

Retrieval and generation are deliberately separated:

- Gemini is responsible for embeddings.
- Qdrant is responsible for semantic retrieval.
- Groq is responsible for answer generation.

The LLM receives retrieved document context rather than being treated as the source of truth. Retrieved source metadata is retained so responses can expose the document and page associated with supporting evidence.

This design improves traceability and makes it possible for users to verify where an answer came from.

---

## 10. Conversational Memory

Conversations and messages are persisted in Supabase PostgreSQL.

This enables follow-up questions such as:

```text
User: What is the penalty clause?
Assistant: ...

User: Who does it apply to?
Assistant: ...
```

The second question can be interpreted in the context of the active conversation instead of requiring the user to restate the first question.

A stale/deleted conversation ID is also handled gracefully by the frontend: the active conversation is cleared, messages are reset, and the conversation list is synchronized instead of repeatedly requesting a known-invalid resource.

---

## 11. Multi-Document Analysis

Users can select multiple indexed documents as the retrieval scope.

For comparison questions, OpsPilot retrieves relevant passages from the selected document collection and asks the LLM to synthesize the relationship between those passages.

Example:

```text
What are the similarities between both PDFs?
```

The response can summarize common themes while retaining source citations for verification.

This is semantic cross-document analysis; it is not a dedicated deterministic document-diff engine.

---

## 12. Error Handling

The application explicitly handles failures across the ingestion lifecycle.

Examples include:

- unreadable/scanned PDFs
- embedding API failures
- provider rate limits and quota exhaustion
- vector indexing failures
- invalid/deleted conversation IDs
- API/network failures

Failed document processing persists the failure reason to the database, allowing the UI to show an actionable **Failed** state instead of leaving a document stuck in **Processing**.

---

## 13. API Surface

The backend exposes structured REST endpoints under `/api/v1`.

Representative resources include:

```text
GET    /health

GET    /api/v1/documents
POST   /api/v1/documents
DELETE /api/v1/documents/{document_id}

GET    /api/v1/conversations
POST   /api/v1/conversations
GET    /api/v1/conversations/{conversation_id}
DELETE /api/v1/conversations/{conversation_id}

POST   /api/v1/chat
```

The API is implemented as a FastAPI service rather than embedding retrieval/LLM logic directly inside the frontend.

---

## 14. Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project
- Qdrant Cloud project
- Gemini API key
- Groq API key

### 14.1 Clone

```bash
git clone https://github.com/Shrestha-Gupta/OpsPilot-V2.git
cd OpsPilot-V2
```

### 14.2 Backend

Windows:

```powershell
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
```

macOS/Linux:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure `backend/.env` with real credentials.

Run the Supabase migration:

```text
backend/migrations/001_initial_schema.sql
```

Execute it from the Supabase SQL Editor before starting the application.

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

Development API docs:

```text
http://localhost:8000/docs
```

### 14.3 Frontend

Open another terminal:

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

macOS/Linux:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend:

```text
http://localhost:5173
```

Set `VITE_API_BASE_URL` in `frontend/.env` if the backend is running somewhere other than localhost.

---

## 15. Environment Variables

### Backend

```text
APP_ENV
LOG_LEVEL
FRONTEND_URL

SUPABASE_URL
SUPABASE_SERVICE_KEY
SUPABASE_BUCKET_NAME

QDRANT_URL
QDRANT_API_KEY
QDRANT_COLLECTION_NAME

GEMINI_API_KEY
EMBEDDING_MODEL
EMBEDDING_DIMENSIONS

GROQ_API_KEY
GROQ_MODEL
GROQ_MAX_TOKENS
GROQ_TEMPERATURE

MAX_FILE_SIZE_MB
MAX_FILES_PER_UPLOAD

CHUNK_SIZE
CHUNK_OVERLAP
RETRIEVAL_TOP_K
CONVERSATION_HISTORY_LIMIT
```

See `backend/.env.example` for the authoritative variable names and defaults.

### Frontend

```text
VITE_API_BASE_URL
VITE_APP_NAME
VITE_MAX_FILE_SIZE_MB
```

**Never commit real API keys or service-role credentials.** The repository contains environment-variable templates only.

---

## 16. Production Deployment

### Backend — Render

Current production configuration:

```text
Service: Web Service
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure all backend environment variables in Render.

### Frontend — Vercel

```text
Root Directory: frontend
Build Command: npm install && npm run build
Output Directory: dist
```

Set:

```text
VITE_API_BASE_URL=https://opspilot-v2.onrender.com
```

The backend allows the deployed Vercel origin through `FRONTEND_URL`.

---

## 17. Performance & Reliability Notes

The ingestion pipeline was optimized around the most expensive stage: embedding generation.

The current implementation includes:

- batched Gemini embedding requests
- adaptive handling of provider retry delays
- transient-error retry logic
- explicit daily-quota detection
- larger Qdrant upsert batches
- pipeline timing/progress logging
- persisted failure states

This reduces unnecessary retries and makes provider quota failures fail fast instead of leaving documents in ambiguous states.

### Provider quota limitation

Gemini Free Tier embedding quotas can limit how many embedding requests/items can be processed in a given period. This is an external provider constraint, not a vector database or RAG correctness failure.

For larger production workloads, the embedding provider/quota tier should be selected according to expected document volume.

---

## 18. Known Limitations

The current implementation intentionally focuses on the core RAG workflow.

### Not currently implemented

- OCR for image-only/scanned PDFs
- Hybrid BM25 + dense retrieval
- Dedicated reranking stage
- Token-by-token streaming responses
- Authentication / RBAC / multi-tenant workspaces
- Dedicated deterministic document version-diff engine
- Docker-based one-command deployment

These are product extensions rather than prerequisites for the core document intelligence workflow.

---

## 19. What I Would Build With One More Week

If another week were available, the highest-value improvements would be:

1. **OCR ingestion** — support scanned/image-only PDFs instead of rejecting them.
2. **Hybrid retrieval** — combine dense semantic search with BM25 keyword retrieval for better handling of exact terms, IDs, and policy language.
3. **Reranking** — add a lightweight reranking stage before generation to improve top-context precision.
4. **Streaming responses** — stream generated tokens to improve perceived latency.
5. **Authentication and workspaces** — isolate documents and conversations per organization/user.
6. **Evaluation harness** — maintain a small question/answer benchmark to measure retrieval recall, citation correctness, and answer faithfulness across changes.

The goal would be to improve retrieval quality and production readiness without changing the core architecture.

---

## 20. Design Decisions & Trade-offs

### Qdrant instead of an in-memory FAISS index

A persistent hosted vector database is better suited to a deployed service because the vector index survives backend restarts and supports metadata filtering.

### Gemini embeddings + Groq generation

The two providers have clear responsibilities. Embeddings are optimized for semantic retrieval, while the LLM is isolated to answer generation. This makes the pipeline easier to reason about and replace component-by-component.

### Supabase for application state

Supabase provides PostgreSQL plus object storage in one managed platform, which keeps document metadata, conversation state, messages, and PDF files under a simple deployment model.

### FastAPI backend

Retrieval and generation remain behind a structured API boundary rather than being implemented directly in the browser. This keeps provider credentials server-side and separates UI concerns from AI/data infrastructure.

---

## 21. Assignment Alignment

OpsPilot was designed to satisfy the core requirements of a production-style document intelligence assignment:

- 2–3+ PDF ingestion support
- text extraction, chunking, and embeddings
- vector retrieval
- conversational follow-ups
- structured backend API
- usable frontend with loading and error states
- public deployment
- environment-based secrets
- source-grounded answers with citations
- GitHub repository with setup and architecture documentation

The current implementation also supports multi-document comparison and persistent conversations beyond the minimum workflow.

---

## 22. Repository Structure

```text
OpsPilot-V2/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── routers/
│   │   ├── services/
│   │   └── main.py
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── .env.example
│
└── README.md
```

---

## 23. Security Notes

- API credentials are loaded from environment variables.
- Supabase service-role credentials remain backend-only.
- No secrets are required in the frontend except the backend URL/configuration.
- `.env.example` files contain placeholders rather than real credentials.
- Production CORS is restricted through `FRONTEND_URL`.

---

## 24. License

This repository is intended as a project/technical-assignment submission. Add a project-specific license here if the repository is later intended for public redistribution.

---

## Built with a simple principle

**Retrieve the evidence first. Generate the answer second.**

OpsPilot is designed so that the document collection remains the source of truth and the LLM operates over retrieved context rather than acting as an unrestricted knowledge source.
