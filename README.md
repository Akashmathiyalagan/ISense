# ISense — SIH 2026 Project

**An AI-assisted BIS standards and certification guidance platform.**

ISense is a Smart India Hackathon (SIH) project exploring how AI and Retrieval-Augmented Generation (RAG) can make Bureau of Indian Standards (BIS) information easier to discover and understand. It is designed to help users investigate potentially relevant Indian Standards, certification procedures, testing requirements, and related compliance guidance through a conversational interface.

> **SIH prototype status:** The web application and RAG backend are under development. A conversational WhatsApp product questionnaire using interactive list messages is now implemented in the repository, but it still needs local test execution and live WhatsApp end-to-end verification. Native WhatsApp Flow publication remains blocked by a Meta integrity restriction; the conversational questionnaire does not require native Flow publication.

## Problem

Finding and interpreting BIS-related information can be difficult for small manufacturers, entrepreneurs, importers, and first-time applicants. Users may not know which product details matter, which standard to investigate, or where to find applicable official guidance.

## Proposed SIH Solution

ISense aims to provide a guided interface that:

1. Collects a user's question and, when relevant, product details.
2. Retrieves related passages from the regulatory documents indexed by the project.
3. Generates an answer grounded in retrieved evidence.
4. Presents available source information so users can investigate the original material.
5. Supports access through a web interface, with WhatsApp interaction being developed.

ISense is an independent assistance prototype, not an official BIS government service. It does not grant certification, issue licences, or guarantee that a product complies with a standard.

## Main Features

- **RAG-based question answering:** Uses retrieved regulatory passages to ground responses.
- **Hybrid retrieval:** Combines dense semantic search, BM25 keyword search, exact BIS standard-number matching, and a TF-IDF fallback.
- **Regulatory document ingestion:** Extracts text and metadata from supported files and divides documents into searchable chunks.
- **Standards-aware assistance:** Detects and handles references to Indian Standard numbers.
- **Source-oriented answers:** Carries document, clause, page, and source metadata through the retrieval pipeline where available.
- **Web application:** Provides the main user interface for interacting with the project.
- **Conversational WhatsApp questionnaire:** Asks product-specific questions one at a time using interactive WhatsApp lists, stores progress by sender, supports cancellation, and passes completed product details to the RAG assistant. Live WhatsApp delivery and the full flow still need testing.
- **Native WhatsApp Flow:** A separate form-based implementation exists, but publishing is currently blocked by Meta's integrity check and is not required for the conversational questionnaire.

## Technology Stack

| Technology | Role |
|---|---|
| Python | Backend and RAG logic |
| FastAPI | API endpoints and webhook handling |
| React, Vite | Web application frontend |
| Sentence Transformers (all-MiniLM-L6-v2) | Dense semantic retrieval when available |
| BM25 | Lexical retrieval |
| scikit-learn TF-IDF | Retrieval fallback |
| Google Gemini integration | Language-model responses when configured |
| Meta WhatsApp Cloud API | WhatsApp messaging integration |
| Pytest | Automated tests |
| Docker / Docker Compose | Optional local containerized setup |

The actual capabilities available depend on the configured environment, indexed documents, and successfully connected services.

## Architecture

~~~mermaid
flowchart TD
    U[User] --> UI[ISense Web Interface]
    U --> WA[WhatsApp integration in progress]
    UI --> API[FastAPI Backend]
    WA --> API
    API --> Q[Query and standard detection]
    Q --> R[Hybrid retrieval]
    R --> KB[Indexed BIS-related documents]
    KB --> R
    R --> G[Grounded answer generation]
    G --> C[Answer and available source metadata]
    C --> UI
    C --> WA
~~~

## WhatsApp Questionnaire Screenshots

The following screenshots are from a development test of the conversational product questionnaire. The user selected product details in WhatsApp, and ISense passed the collected answers to its RAG assistant.

### 1. Selectable product questions

![ISense WhatsApp questionnaire showing selectable answers](Bis_model3/docs/screenshots/whatsapp-question-options.jpg)

### 2. Multi-step questionnaire in progress

![ISense WhatsApp questionnaire progressing through product questions](Bis_model3/docs/screenshots/whatsapp-questionnaire-progress.jpg)

### 3. RAG response after questionnaire completion

![ISense WhatsApp assistant response after product details were submitted](Bis_model3/docs/screenshots/whatsapp-rag-response.jpg)

**Evidence limitation shown in this test:** The assistant reported that its currently indexed BIS knowledge base did not contain the mandatory conformity-assessment or testing records specifically covering water bottles. It therefore asked for clarification and directed the user to verify official BIS sources instead of asserting an unsupported requirement. This is a development test, not proof of a complete or production-ready compliance determination.

> The screenshot assets are stored in `Bis_model3/docs/screenshots/`. The native WhatsApp Flow remains a separate feature and is still blocked at Meta's publishing step; these screenshots demonstrate the alternative conversational questionnaire using WhatsApp interactive lists.

## Repository Structure

~~~text
ISense/
├── README.md
└── Bis_model3/
    ├── README.md
    ├── src/                  # Web frontend source
    ├── public/               # Static web assets
    ├── package.json
    ├── Dockerfile
    ├── docker-compose.yml
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

See [the application README](Bis_model3/README.md) for detailed development instructions.

## Run Locally

### Prerequisites

- Python version compatible with the backend dependencies
- Node.js and npm
- Git
- An API key for the configured LLM provider if using live generation
- Meta WhatsApp Cloud API credentials only if testing WhatsApp integration

### 1. Clone the repository

~~~bash
git clone https://github.com/Akashmathiyalagan/ISense.git
cd ISense/Bis_model3
~~~

### 2. Start the frontend

~~~bash
npm install
npm run dev
~~~

Use the local URL printed by Vite in the terminal.

### 3. Set up and start the backend

In another terminal:

~~~powershell
cd ISense/Bis_model3/backend
python -m venv venv
venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
~~~

Create a local .env file based on the provided .env.example, then add the credentials required by the application. Do not commit secrets.

Start FastAPI:

~~~powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
~~~

Open http://127.0.0.1:8000/docs for API documentation if the backend is running on port 8000. If that port is occupied, select another port and update related local configuration.

### 4. Run backend tests

From Bis_model3/backend, run the tests present in the checked-out version:

~~~bash
python -m pytest
~~~

Test coverage and results may differ between local working copies and the files committed to GitHub.

## WhatsApp Development Status

The WhatsApp integration is being developed separately from the core RAG workflow. Meta has accepted the custom Flow JSON without validation errors, but publishing has returned an integrity restriction. Until Meta clears that restriction and a live submission is tested, the dynamic WhatsApp Flow should be treated as **in progress**, not as a working production feature.

Development testing may use an HTTPS tunnel such as ngrok. Tunnel URLs can change and should not be treated as permanent production endpoints.

## Responsible Use

ISense is intended to help users find and understand information. It is not an official BIS portal and should not be treated as a final legal or certification decision. Users must verify applicable requirements against current official BIS publications and relevant government sources. Product scope, applicable standards, compulsory certification requirements, and exemptions depend on the specific product and applicable rules.

Do not claim that a product is certified or compliant without appropriate evidence.

## SIH Development Roadmap

- [x] Establish FastAPI backend and web application structure
- [x] Implement an initial RAG pipeline with hybrid retrieval
- [x] Add BIS standard detection and regulatory-document metadata
- [x] Add WhatsApp webhook/message integration in the development project
- [x] Implement conversational product questionnaire logic with product-specific question sets
- [x] Add WhatsApp interactive-list sending method and webhook routing
- [x] Add unit tests for questionnaire classification, state progression, persistence, and cancellation
- [x] Validate custom native WhatsApp Flow JSON with Meta
- [ ] Run questionnaire tests in the project environment and verify live WhatsApp replies
- [ ] Improve product-aware query routing and hierarchical retrieval
- [ ] Add and evaluate a reranking stage
- [ ] Resolve the separate native Flow publishing restriction
- [ ] Verify native Flow encrypted exchange if the native Flow is pursued
- [ ] Evaluate retrieval quality, citation correctness, and insufficient-evidence handling
- [ ] Document deployment and operational testing results

## SIH Information

This repository contains the ISense prototype prepared for Smart India Hackathon (SIH). Add your official SIH problem-statement ID, team name, institution, and member details here if required by your submission.

## License

No license is specified by this README. Add a license only when your team has decided how the project may be reused and distributed.
