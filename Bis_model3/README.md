# ISense — SIH 2026 Development Guide

ISense is a **Smart India Hackathon (SIH) prototype** exploring the use of AI and Retrieval-Augmented Generation (RAG) to help users find and understand Bureau of Indian Standards (BIS) requirements. This document explains the current repository structure, local development setup, and integration status.

ISense is an independent prototype, not an official BIS service. It cannot grant licences, issue Standard Marks, or guarantee product compliance.

> **SIH prototype status:** The web application and FastAPI/RAG backend are under development. A conversational WhatsApp product questionnaire now uses interactive list messages and does not require native Flow publication. Its automated tests have been added but must be run in your local checkout, and real WhatsApp end-to-end behaviour still needs verification. The separate native WhatsApp Flow JSON passed Meta validation, but native Flow publishing is blocked by a Meta integrity restriction.

## Project Components

### Web application
The React/Vite frontend provides the user interface for interacting with ISense and the backend.

### RAG backend
The FastAPI backend contains the regulatory-document ingestion pipeline, standard detection, hybrid retrieval, and LLM-provider integration.

The current retrieval implementation includes:
- Dense semantic retrieval using Sentence Transformers with all-MiniLM-L6-v2 when available.
- BM25 lexical retrieval.
- Exact BIS standard-number matching boosts.
- TF-IDF fallback if dense embeddings are unavailable.
- Document metadata and chunk-level source information.
- Grounded response instructions and insufficient-evidence handling.

This is the current baseline. Query-aware routing, hierarchical retrieval, and reranking are possible future improvements and should not be described as implemented until they are added and tested.

### WhatsApp integration
The project includes WhatsApp Cloud API webhook/message integration.

**Conversational questionnaire (Option 1):** Product-only messages such as water bottle, backpack, or RC car start a product-specific sequence of WhatsApp interactive list messages. The backend persists progress per sender, advances on the user's selected answer, supports cancellation, and sends the completed product details to the existing RAG assistant. This approach does not depend on publishing a native WhatsApp Flow.

The conversational path is committed but still needs test execution in the local checkout and live end-to-end verification with Meta. Users should test within the customer-service messaging window and use a recipient who has initiated or consented to the conversation.

**Native WhatsApp Flow (optional alternative):** The custom Flow JSON passed Meta's validator, but publishing returned an integrity restriction. Native Flow support needs a published Flow, a reachable HTTPS data-exchange endpoint, correctly configured encryption keys, and successful live testing. It is not required for the conversational questionnaire.

## Technology Stack

| Technology | Purpose |
|---|---|
| React and Vite | Frontend |
| Python and FastAPI | Backend APIs |
| Sentence Transformers | Dense semantic search |
| BM25 | Keyword retrieval |
| scikit-learn TF-IDF | Fallback retrieval |
| Google Gemini | LLM responses when configured |
| OpenAI API | Optional LLM fallback when configured |
| Meta WhatsApp Cloud API | WhatsApp integration |
| Pytest | Automated tests |
| Docker Compose | Optional containerized setup |

## Repository Layout

~~~text
ISense/
├── README.md
└── Bis_model3/
    ├── README.md
    ├── .env.example
    ├── package.json
    ├── src/
    ├── public/
    ├── docker-compose.yml
    ├── Dockerfile
    └── backend/
        ├── main.py
        ├── rag_engine.py
        ├── whatsapp_service.py
        ├── whatsapp_questionnaire.py
        ├── whatsapp_flow_endpoint.py
        ├── rag/
        ├── storage/
        ├── tests/
        │   └── test_whatsapp_questionnaire.py
        └── requirements.txt
~~~

## Quick Start — Local Development

### Prerequisites

- Python installed and compatible with backend dependencies.
- Node.js and npm.
- Git.
- A Gemini API key or another supported provider key if live LLM generation is required.
- Meta WhatsApp Cloud API credentials only when testing WhatsApp features.

### 1. Clone the repository

~~~bash
git clone https://github.com/Akashmathiyalagan/ISense.git
cd ISense/Bis_model3
~~~

### 2. Configure environment variables

Create a local .env from the example file:

**Windows PowerShell**
~~~powershell
Copy-Item .env.example .env
~~~

Edit .env locally and enter the values you need. The example file documents the main variables:

~~~dotenv
VITE_API_BASE_URL=http://localhost:8000
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=
WHATSAPP_GRAPH_API_VERSION=v22.0
~~~

These are placeholders; do not paste actual credentials into this README. Do not commit .env, real tokens, API keys, or private encryption keys.

### 3. Start the frontend

From the Bis_model3 directory:

~~~bash
npm install
npm run dev
~~~

Open the local address printed by Vite. The configured backend URL is controlled by VITE_API_BASE_URL.

### 4. Install and start the backend

Open a second terminal:

~~~powershell
cd ISense/Bis_model3/backend
python -m venv venv
venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
~~~

Start the API:

~~~powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
~~~

Open http://127.0.0.1:8000/docs for interactive API documentation.

If port 8000 is already occupied, use another port and update VITE_API_BASE_URL and any relevant webhook configuration so they match.

### 5. Optional: run with Docker Compose

From Bis_model3, review the provided compose configuration and environment requirements, then run:

~~~bash
docker compose up --build
~~~

For SIH demonstration and local debugging, native frontend/backend startup is usually easier because it exposes logs directly.

## WhatsApp Cloud API

The project documents these development endpoints:

- Webhook verification: GET /api/webhook/whatsapp
- Incoming WhatsApp webhook: POST /api/webhook/whatsapp
- Status and diagnostics: GET /api/whatsapp/status

When testing webhooks locally, expose the backend through an HTTPS tunnel such as ngrok, then set the callback URL in the Meta Developer dashboard. A temporary tunnel URL can change and is not a production endpoint.

### Conversational questionnaire screenshots

The screenshot files previously referenced here are not present in the `main` branch, so the broken image links have been removed. Add the screenshot files to `Bis_model3/docs/screenshots/` and restore the Markdown image links once those files have been committed.

### Dynamic WhatsApp Flow status

The custom Flow JSON passed Meta's JSON validation, but publishing returned:

- Error code: 139000
- Error subcode: 4233020
- Message: “Blocked by Integrity — Integrity requirements not met.”

This is a Meta-side publication restriction. It does not by itself prove that the code or JSON is invalid. Avoid claiming the interactive Flow works end to end until Meta allows publishing and live encrypted data exchange and form submission are tested.

## Testing

Run backend tests from the backend directory:

~~~bash
python -m pytest
~~~

The conversational questionnaire includes focused tests for product classification, question progression, saved state, and cancellation in `tests/test_whatsapp_questionnaire.py`.

Run a focused group of tests when those files exist in your current checkout:

~~~bash
python -m pytest tests/test_dynamic_flow_endpoint.py tests/test_whatsapp_flows.py -q
~~~

Tests passing locally do not guarantee that Meta's hosted Flow, webhook delivery, encryption exchange, or external LLM provider will work in production.

## RAG Pipeline

The current request path is broadly:

1. Ingest and clean supported regulatory documents.
2. Extract metadata and divide the documents into searchable chunks.
3. Build dense and lexical retrieval indexes.
4. Detect standard-number references and retrieve candidate evidence.
5. Generate a response using the configured LLM provider and retrieved passages.
6. Return available source and citation metadata.

The evidence base is limited to the documents actually indexed and correctly parsed by the application. Always validate legal and certification requirements against current official BIS publications.

## SIH Scope and Roadmap

- [x] Web application and FastAPI backend foundation
- [x] Initial RAG pipeline with hybrid retrieval
- [x] BIS standard detection and source metadata
- [x] WhatsApp webhook/message integration in development
- [x] Implement conversational product questionnaire using interactive lists
- [x] Add questionnaire unit tests
- [x] Custom native Flow JSON accepted by Meta's validator
- [ ] Run local questionnaire tests and validate live WhatsApp interactions
- [ ] Resolve native Flow publishing restriction (optional path)
- [ ] Validate complete encrypted native Flow data exchange if pursued
- [ ] Improve query-aware retrieval and add evaluation metrics
- [ ] Evaluate hierarchical retrieval and reranking
- [ ] Document reproducible demo and test results

## Responsible Use

ISense provides assistance to navigate information. It is not a substitute for official BIS decisions. Users should verify current standards, applicability, orders, fees, testing obligations, and exemptions against official BIS or relevant government sources. Responses should not claim certification or compliance without documentary evidence.

## SIH Submission Details

Add these details if required for your submission:

- SIH problem-statement ID: [add official ID]
- Team name: [add team name]
- Institution: [add institution]
- Team members: [add names]

## License

Check the repository's licensing requirements with your team before adding a licence. No licence is asserted by this document.
