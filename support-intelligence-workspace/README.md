# Support Intelligence Workspace

AI-powered internal platform that helps support engineers answer customer questions with grounded, citation-backed responses — and continuously improve the knowledge base.

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Anthropic](https://img.shields.io/badge/LLM-Claude-191919?logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas%20%2F%20Local-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

**Support Intelligence Workspace** is an internal Support Intelligence platform built for support engineers. It uses **Retrieval-Augmented Generation (RAG)** to turn customer questions into grounded answer suggestions — complete with source citations, confidence and coverage scores, recommended actions, and knowledge-gap signals.

This is **not** a customer-facing chatbot. Engineers paste a customer question, review evidence from the knowledge base, decide whether to send, verify, escalate, or flag a documentation gap, and feed those outcomes back into analytics.

The goal is operational: faster, safer answers for support — and a clearer map of where documentation is missing, outdated, or confusing.

---

## Features

| Capability | Description |
|------------|-------------|
| **AI-powered support assistant** | Claude-backed suggested responses for support engineers |
| **RAG pipeline** | Retrieve → rerank → evidence score → generate → evaluate |
| **Semantic search** | Local MiniLM embeddings + ChromaDB vector retrieval |
| **Confidence scoring** | Heuristic confidence based on evidence quality (not LLM self-rating) |
| **Coverage scoring** | Measures how well retrieved docs cover the question |
| **Source citations** | Traceable excerpts tied to supporting documents |
| **Unsupported topic detection** | Suppresses grounded answers when evidence is insufficient |
| **Knowledge gap detection** | Flag missing / outdated / incorrect / confusing docs |
| **Dashboard analytics** | Volume, confidence, actions, gaps, and doc health at a glance |
| **Document health monitoring** | Registry with retrieval counts, gaps, and health labels |
| **Retrieval diagnostics** | Embedding, retrieval, rerank, and LLM timings per Ask |
| **Modern responsive UI** | Dense, enterprise-ready React workspace (desktop → mobile) |

---

## Tech Stack

| Layer | Technologies |
|-------|----------------|
| **Frontend** | React, TypeScript, Tailwind CSS, Vite, TanStack Query, Recharts |
| **Backend** | FastAPI, Python 3.11+, Pydantic, Motor |
| **AI** | Anthropic Claude (chat), Sentence Transformers MiniLM (embeddings), ChromaDB |
| **Database** | MongoDB (questions, gaps, feedback, document stats) |
| **Vector store** | ChromaDB (local persistence) |

---

## Architecture

End-to-end Ask pipeline:

```text
User Question
      │
      ▼
 Embedding  (MiniLM)
      │
      ▼
 Vector Search  (ChromaDB + heuristic rerank)
      │
      ▼
 Evidence Scoring
      │
      ▼
 Unsupported Topic Detection
      │
      ├─ insufficient evidence → refuse / escalate path (no fake citations)
      │
      ▼
 LLM  (Anthropic Claude)
      │
      ▼
 Grounded Response  (+ citations, quality, recommended action)
      │
      ▼
 Confidence & Coverage
      │
      ▼
 Analytics  (Mongo persistence + event handlers + dashboard APIs)
```

### Layering

```text
React UI  →  FastAPI routes  →  Services  →  RAG / Repositories  →  Chroma + MongoDB
```

| Concern | Implementation |
|---------|----------------|
| HTTP | Thin FastAPI routes |
| Business logic | `AskService`, analytics, gap, feedback services |
| Retrieval | Embedding → Chroma top‑k → heuristic rerank |
| Grounding | Evidence scoring + unsupported-topic gate before LLM |
| Persistence | MongoDB for questions, gaps, feedback, document registry |
| Events | In-process event bus for stats / analytics updates |

---

## Screens

| Screen | Purpose |
|--------|---------|
| **Dashboard** | Operational overview — questions, confidence, gaps, health, volume |
| **Ask Workspace** | Paste a customer question; review answer, scores, citations, actions |
| **Knowledge Gaps** | Filterable registry of documentation issues flagged by engineers |
| **Documents** | Knowledge-base explorer with health, retrievals, and detail drawer |
| **Analytics** | BI-style distributions (confidence, coverage, actions, topics) |
| **Settings** | Theme, runtime health, and provider configuration |

---

## Project Structure

```text
support-intelligence-workspace/
├── frontend/                 # React + TypeScript + Tailwind (Vite)
│   └── src/
│       ├── components/       # Layout, UI primitives, charts, badges
│       ├── features/         # Page modules (dashboard, ask, gaps, …)
│       ├── api/              # Typed API client
│       └── types/            # Shared DTO types
├── backend/                  # FastAPI application
│   └── app/
│       ├── routes/           # HTTP adapters
│       ├── services/         # Ask, analytics, gaps, feedback
│       ├── rag/              # Retrieve, evidence, confidence, LLM
│       ├── repositories/     # Mongo access
│       ├── schemas/          # Request / response DTOs
│       ├── events/           # Domain event bus + handlers
│       └── database/         # Mongo client + indexes
├── docs/                     # Sample knowledge base (ingestion source)
├── ingestion/                # Ingestion notes / helpers
├── scripts/                  # Dev utilities (e.g. ingest_docs.py)
├── vectorstore/              # Chroma persistence (gitignored)
└── README.md
```

---

## Installation

### Prerequisites

- **Node.js** 18+
- **Python** 3.11+
- **MongoDB** running locally (or a MongoDB Atlas URI)
- **Anthropic API key** for Claude
- Disk space for the local MiniLM embedding model (downloaded on first use)

### 1. Clone

```bash
git clone https://github.com/Aman6917-ctrl/price_labs.git
cd price_labs/support-intelligence-workspace
```

### 2. Install backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional — tests
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and MONGODB_URI
```

### 3. Install frontend

```bash
cd ../frontend
npm install
cp .env.example .env               # leave VITE_API_URL empty for local proxy
```

### 4. Environment variables

Configure `backend/.env` (see [Environment Variables](#environment-variables)).  
Frontend can rely on the Vite proxy to `http://localhost:8000` when `VITE_API_URL` is empty.

### 5. Ingest the knowledge base

From the `backend` virtualenv (with embeddings available):

```bash
cd ../backend
source .venv/bin/activate
# Optional offline flags if the model is already cached:
# HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
python ../scripts/ingest_docs.py
```

This chunks docs under `docs/`, embeds with MiniLM, and persists vectors to Chroma (`vectorstore/`).

### 6. Run backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Health check: [http://localhost:8000/health](http://localhost:8000/health)  
OpenAPI: [http://localhost:8000/docs](http://localhost:8000/docs)

### 7. Run frontend

```bash
cd frontend
npm run dev
```

App: [http://localhost:5173](http://localhost:5173)

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `ANTHROPIC_MODEL` | No | Default: `claude-sonnet-5` |
| `LLM_PROVIDER` | No | Default: `anthropic` |
| `MONGODB_URI` | Yes | e.g. `mongodb://localhost:27017` |
| `MONGODB_DB` | No | Default: `support_intelligence` |
| `EMBEDDING_MODEL` | No | Default: `sentence-transformers/all-MiniLM-L6-v2` |
| `CHROMA_PERSIST_DIR` | No | Default: `../vectorstore` |
| `CHROMA_COLLECTION` | No | Default: `pricelabs_docs_minilm` |
| `DOCS_PATH` | No | Knowledge base path (default: `../docs`) |
| `RAG_TOP_K` | No | Retrieval depth (default: `5`) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | No | Ingestion chunking knobs |
| `CORS_ORIGINS` | No | Comma-separated origins (default: `http://localhost:5173`) |
| `APP_ENV` | No | `development` / `production` |

Example:

```bash
APP_ENV=development
CORS_ORIGINS=http://localhost:5173

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=support_intelligence

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-5

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

DOCS_PATH=../docs
CHROMA_PERSIST_DIR=../vectorstore
CHROMA_COLLECTION=pricelabs_docs_minilm
RAG_TOP_K=5
CHUNK_SIZE=900
CHUNK_OVERLAP=150
```

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | No | Leave empty locally to use Vite proxy → `:8000` |

---

## API Surface

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness / Mongo status |
| `POST` | `/api/ask` | RAG answer + confidence + citations |
| `POST` | `/api/ingest` | Ingest docs → Chroma |
| `POST` | `/api/flag-gap` | Flag a knowledge gap |
| `POST` | `/api/feedback` | Thumbs up / down |
| `GET` | `/api/gaps` | List knowledge gaps |
| `GET` | `/api/analytics` | Dashboard / BI metrics |
| `GET` | `/api/documents` | Document registry |
| `GET` | `/api/documents/{id}/stats` | Per-document stats |

---

## Design Decisions

### Why RAG?

Support answers must be grounded in **PriceLabs documentation**, not free-form model knowledge. RAG retrieves relevant chunks first, then constrains generation to that evidence — reducing hallucinations and making answers auditable.

### Why confidence scoring?

Engineers need a signal for **how safe it is to send** a suggestion. Confidence is computed from retrieval and evidence quality (similarity, support strength, coverage interactions) rather than asking the LLM to rate itself.

### Why unsupported topic detection?

When the knowledge base does not contain supporting evidence, inventing an answer is worse than refusing. The pipeline detects weak / off-topic retrieval and **suppresses grounded citations**, steering the engineer toward escalate or flag-gap flows.

### Why citations?

Every suggestion should be **traceable**. Citations (title, category, similarity, excerpt) let engineers verify claims against source docs before responding to customers.

### Why knowledge gap tracking?

Wrong or missing docs are a product problem, not only a chat problem. Flagging gaps (missing, outdated, incorrect, confusing) turns day-to-day support work into a **feedback loop for documentation owners**, surfaced on the Dashboard and Analytics screens.

---

## Future Improvements

| Area | Direction |
|------|-----------|
| **Authentication** | SSO / RBAC for multi-workspace support teams |
| **CI/CD** | Automated lint, unit tests, and deploy pipelines |
| **E2E tests** | Browser-level coverage for Ask → gap → analytics flows |
| **Monitoring** | Structured logs, latency / error SLOs, LLM cost alerts |
| **Better analytics** | True date-range filters, cohort views, doc freshness SLAs |
| **Integrations** | Zendesk / Intercom / Slack notifications for critical gaps |

---

## License

This project is licensed under the [MIT License](LICENSE).

```text
MIT License — free to use, modify, and distribute with attribution.
```

---

<p align="center">
  <sub>Built for support engineering teams who need grounded answers — and better docs over time.</sub>
</p>
