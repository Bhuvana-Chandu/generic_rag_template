# Property & Home Insurance AI Copilot
## Comprehensive System Summary & Architecture

This document provides a complete top-to-bottom overview of the AI Copilot project, detailing the application flow, tool ecosystem, memory management, and logging architecture.

---

### 1. Application Flow & Architecture
The system operates on a dual-engine architecture designed to provide a rich UI while maintaining a robust AI backend.

*   **Frontend (Streamlit):** Runs on Port `8501`. Provides the chat interface, session sidebar, and live typing effects.
*   **Backend (FastAPI):** Runs on Port `8000`. Acts as the central brain.
*   **Proxy Middleware:** To avoid dealing with multiple ports during deployment, the FastAPI server runs a `StreamlitProxyMiddleware`. All UI web traffic hitting Port 8000 is automatically routed to Streamlit behind the scenes.
*   **Server-Sent Events (SSE):** When a user asks a question, the frontend sends a request to the backend's `/chat/stream` endpoint. The backend uses SSE to stream the AI's internal thoughts (Agent Steps) and final answer back to the UI in real-time.

---

### 2. The LangGraph Orchestration Flow
When a user submits a query, it travels through a specialized **LangGraph** workflow in `orchestrator.py`:

1.  **Memory Extraction:** A lightweight LLM extracts structured details (e.g., postcode, damage type) and saves unstructured facts to long-term memory.
2.  **Intent Classification:** The query is bucketed into `POLICY_Q_A`, `COST_ESTIMATION`, `CONTRACTOR_LOOKUP`, or `CLAIM_STATUS`.
3.  **Universal Baseline Pre-fetch:** Regardless of intent, the AI searches the PDF databases (FAISS) to build a baseline knowledge context.
4.  **Tool Dispatch:** If the query contains specific keywords (like "plumber" or "electrician"), it forcefully activates the corresponding database tools (CSVs) and appends the data to the context.
5.  **Synthesis:** The powerful `gpt-4o` LLM reads the combined context (PDF rules + CSV data + Memory) and generates a natural, human-friendly response.
6.  **Guardrail Check:** A final safety LLM reviews the answer to ensure no claim decisions are made and costs are labeled as estimates.

---

### 3. Tools and Data Sources
The AI relies on a hybrid data retrieval system, loading data during the `startup_event` in `main.py`:

*   **Unstructured Data (PDFs):** Handled by `policy_rag_retriever`. The text is chunked, embedded using OpenAI, and stored in a local **FAISS Vector Database** (`storage/faiss_index/`). Perfect for semantic searches like *"what are the exclusions for water damage?"*
*   **Structured Data (CSVs):** Handled by Python/Pandas. The files `PropertyDamage_RepairCostTable.csv` and `ApprovedContractor_Network.csv` are loaded directly into server RAM as DataFrames. This allows for lightning-fast, exact-match filtering (e.g., finding plumbers specifically in SW1).

---

### 4. Memory Management
The system uses a dual-memory architecture to provide a personalized experience:

*   **Short-Term Structured Memory (`session_manager.py` & Pydantic):** 
    During a conversation, the AI populates a `MemoryContext` object containing strictly defined fields (`property_type`, `postcode`, `policy_tier`, `damage_type`). This lives in the server's RAM and is attached to your specific `session_id`.
*   **Long-Term Unstructured Memory (`Mem0`):** 
    Integrated directly into the graph, `Mem0` saves personal facts (e.g., *"I am a landlord"*) to a local embedded database (SQLite/Vector). If you clear your current session and start a new one, Mem0 ensures the AI still remembers your historical preferences.

---

### 5. Logging & Monitoring
The application features enterprise-grade observability:

*   **Backend Logs (`loguru`):** 
    All server events, proxy errors, and startup routines are logged asynchronously by Loguru to the `logs/backend.log` file. This file automatically rotates when it reaches 500MB to prevent disk bloat.
*   **Step-by-Step AI Logs (`steps_log`):** 
    Inside the LangGraph workflow, every agent (Memory, Intent, Tools, Synthesis) appends its status to a `steps_log` list. This list is streamed directly to the frontend, resulting in the expandable *"AI Thought Process"* dropdowns you see in the chat UI.

---

### 6. Directory Structure Placement
*   `/backend/` - Contains `main.py` (FastAPI), `models.py` (Pydantic schemas), and `session_manager.py`.
*   `/frontend/` - Contains `app.py` (Streamlit UI), custom CSS, and the Dev Console HTML.
*   `/orchestration/` - The AI Brain. Contains `orchestrator.py` (LangGraph flow) and `tools.py` (FAISS and Pandas data connections).
*   `/data/` - Raw storage for the Pandas CSV databases.
*   `/storage/` - Raw storage for the FAISS Vector Database binaries.
*   `/logs/` - Destination for the `backend.log` file.
