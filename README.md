# OpsPilot - AI Document Intelligence Assistant

OpsPilot is a Retrieval-Augmented Generation (RAG) based document intelligence assistant that allows users to upload one or more PDF documents and ask natural language questions about their content. The application extracts text from PDFs, creates semantic embeddings, stores them in a FAISS vector database, retrieves the most relevant chunks, and generates context-aware responses using Groq's Llama model.

---

# Features

- Upload one or multiple PDF documents
- Semantic search using vector embeddings
- Retrieval-Augmented Generation (RAG)
- Multi-document question answering
- Conversation memory
- Fast document retrieval with FAISS
- Modern React-based chat interface

---

# Tech Stack

### Frontend
- React
- Vite
- Axios

### Backend
- FastAPI
- LangChain
- PyMuPDF

### AI Stack
- HuggingFace Embeddings
- sentence-transformers/all-MiniLM-L6-v2
- FAISS Vector Store
- Groq API (Llama 3.3 70B Versatile)

---

# Project Structure

```
OpsPilot
│
├── backend
│   ├── app
│   │   ├── routes
│   │   ├── services
│   │   ├── schemas
│   │   ├── models
│   │   └── main.py
│   └── requirements.txt
│
├── frontend
│   ├── src
│   ├── public
│   └── package.json
│
├── uploads
├── vector_db
└── README.md
```

---

# Setup Instructions

## Backend

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs at

```
http://localhost:8000
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs at

```
http://localhost:5173
```

---

# Architecture

```text
                User
                  │
                  ▼
          React Frontend
                  │
             Axios Requests
                  │
                  ▼
          FastAPI Backend
                  │
          PDF Upload Endpoint
                  │
                  ▼
              PyMuPDF
                  │
          Text Extraction
                  │
                  ▼
      Recursive Text Chunking
                  │
                  ▼
 HuggingFace Embeddings
(all-MiniLM-L6-v2)
                  │
                  ▼
        FAISS Vector Store
                  │
                  ▼
        Similarity Retrieval
                  │
                  ▼
 Groq Llama 3.3 70B
                  │
                  ▼
           Generated Answer
```

---

# Chunking Strategy

The application uses RecursiveCharacterTextSplitter to divide documents into overlapping chunks.

Configuration:

- Chunk Size: 800 characters
- Chunk Overlap: 150 characters

### Why?

- Preserves context between chunks.
- Improves retrieval quality.
- Reduces chances of losing information near chunk boundaries.
- Suitable for technical PDF documents.

---

# Retrieval Strategy

The application uses semantic retrieval.

Pipeline:

1. User uploads PDF.
2. Text is extracted using PyMuPDF.
3. Text is split into chunks.
4. Chunks are converted into embeddings.
5. Embeddings are stored in FAISS.
6. User question is embedded.
7. Similar chunks are retrieved.
8. Retrieved context is passed to the LLM.
9. Groq Llama generates the final answer.

---

# API Endpoints

### Upload PDF

```
POST /api/upload
```

### Chat

```
POST /api/chat
```

---

# Known Limitations

- Supports only PDF documents.
- FAISS index is stored locally.
- No authentication system.
- Large documents may increase embedding time.
- Does not support OCR for scanned PDFs.

---

# Future Improvements (One More Week)

With one additional week, the following improvements would be implemented:

- User authentication
- Cloud vector database (Pinecone/Qdrant)
- OCR support for scanned PDFs
- Streaming responses
- Citation highlighting
- Document management dashboard
- Conversation history persistence
- Docker deployment
- Production logging and monitoring

---

# Screenshots

(Add screenshots after deployment.)

- Home Page
- PDF Upload
- Chat Interface
- Multi-document Query