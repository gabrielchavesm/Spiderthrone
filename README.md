# Spiderthrone Legal RAG 

**Spiderthrone** is an enterprise-grade Legal RAG (Retrieval-Augmented Generation) system built specifically for Portuguese legal professionals. It guarantees strict adherence to official legal sources (DRE/DGSI), transparent source citations, temporal validity ("Time-Travel" RAG), and generative UI components for structured data rendering.

---

## Repository Structure & Architecture

```text
Spiderthrone/
├── api.py                    # FastAPI backend with AG-UI endpoints & sliding window history[cite: 5]
├── rag_pipeline.py           # Hybrid search retriever (Semantic Qdrant + Keyword matching)[cite: 16]
├── llm_failover.py           # Resilient multi-provider LLM failover (Groq, Gemini Flash)[cite: 13]
├── redis_memory.py           # Persistent session management with Redis[cite: 4]
├── vector_db.py              # Qdrant vector database ingestion and setup[cite: 13]
├── schemas.py                # Pydantic data models for legal chunks[cite: 12]
├── dgsi_scraper.py           # Scraper for Portuguese Superior Courts rulings (DGSI)[cite: 8]
├── dre_scraper.py            # Playwright-powered scraper for Diário da República (DRE)[cite: 9]
├── parser.py                 # Rhetorical role parser and text chunking engine[cite: 10]
├── mass_ingestion.py         # Batch ingestion runner for massive datasets[cite: 1]
├── run_sync_ingestion.py     # Synchronous resilient ingestion script for WSL/local[cite: 2]
├── main.tsx                  # React root entry point
├── App.tsx                   # Frontend chat interface & AG-UI generative widgets
├── index.css & App.css       # Styling and layout configurations
└── .env                      # Environment variables & API keys (git-ignored)

```

---

## Tech Stack

* **Backend:** FastAPI (Python), Uvicorn, Pydantic.


* **Frontend:** React, Vite, Lucide React, Custom CSS.
* **Vector Database:** Qdrant (Local persistent store with FastEmbed ONNX local embeddings).


* **Memory & State:** Redis (In-memory session history with sliding window protection against token limits).


* **LLM Integration:** Groq & Google Gemini APIs with automatic failover and tool calling support.



---

## Prerequisites

Before setting up the project, ensure you have installed:

* **Python** $\ge 3.10$
* **Node.js** $\ge 18$ & npm
* **Redis Server** (running locally on port `6379`)


* **uv** (recommended Python package manager) or standard `pip`

---

## Installation & Setup Guide

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Spiderthrone
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory and add your credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## How to Run the Project Locally (Platform Specific)

Choose your operating system instructions below to run the full stack across terminal windows:

### macOS Setup (Apple Silicon / Intel)

1. **Install System Dependencies (via Homebrew):**
```bash
brew install python node redis
```


2. **Start Redis:**
```bash
brew services start redis
redis-cli ping  # Should return PONG
```


3. **Run the Backend (FastAPI):**
```bash
python -m venv .venv
source .venv/bin/activate
uv sync
python -m api
```


The backend will be live at `http://localhost:8000`.


4. **Run the Frontend (React + Vite):** (Open a second terminal window in the `frontend/` directory)
```bash
cd frontend
npm install
npm run dev
```


*The frontend will be accessible at `http://localhost:5173`.*

---

### Linux Setup

1. **Start Redis:**
```bash
sudo service redis-server start
redis-cli ping  # Should return PONG
```


2. **Run the Backend (FastAPI):**
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate if running natively on Windows CMD/PowerShell
uv sync
python -m api
```


The backend will be live at `http://localhost:8000`.


3. **Run the Frontend (React + Vite):** (Open a second terminal window in the `frontend/` directory)
```bash
cd frontend
npm install
npm run dev
```


*The frontend will be accessible at `http://localhost:5173`.*

---

## Core Features & Capabilities

* **Strict Legal Grounding:** Responses are strictly derived from official legislation (DRE) and court rulings (DGSI).
* **Time-Travel RAG:** Filters retrieved chunks based on validity timestamps (`valid_from_ts`), preventing legal anachronisms.
* **AG-UI Generative Widgets:** Dynamically renders UI components like `mostrar_documento_legal` and `mostrar_tabela_valores` directly in the chat stream.

* **Redis Session Continuity:** Multi-turn chained conversations are preserved securely per session (`session_id`) using a sliding window to prevent token overflow errors.