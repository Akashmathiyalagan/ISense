# ISense — RAG-Based BIS Certification Assistance Platform
### *Production-Grade Enterprise Architecture*

**ISense** is an AI-powered Bureau of Indian Standards (BIS) certification assistance platform designed to guide manufacturers, importers, MSMEs, and brand owners through the statutory certification lifecycle.

---

## 🌟 Architecture Highlights

### 1. Dual Entry-Point Philosophy
- **WhatsApp Interface**: Targeted at first-time applicants who find statutory portals daunting. Natural step-by-step guidance, conversational photo/spec upload, and 24/7 AI assistance.
- **Web SaaS Platform**: Built for enterprise multi-product management, document repositories, and live milestone tracking.
- **Unified Backend Sync**: Both interfaces connect to the **same central FastAPI database, document repository, and grounded RAG model**.

### 2. Grounded RAG Knowledge Base Model
- **Knowledge Base**: Curated Indian Standards (**IS 16102**, **IS 13252**, **IS 1293**, **IS 374**, **IS 616**, **MeitY CRS Procedural Orders**, **Scheme of Inspection & Testing (SIT)**).
- **Retrieval Engine**: Pure-Python TF-IDF vector cosine similarity + BM25 keyword boosting for zero-dependency portability and immunity to Windows DLL Application Control blocks.
- **Real-Time Citations**: Every response quotes verbatim clauses, section numbers, and page numbers from official statutory schedules.

### 3. Real-Time Synchronization Pipeline
- **Server-Sent Events (SSE)**: Streams events (`GET /api/events`) directly to all open browser windows when applications are created, documents uploaded, or readiness recalculated.
- **Full-Duplex WebSockets**: Persistent duplex channel at `ws://localhost:8000/ws/live`.
- **Floating Real-Time Toasts**: Instant visual feedback in the UI for state changes.
- **Automatic Readiness Recalculation**: Uploading documents immediately updates application progress scores and advances milestones.

---

## 🚀 Quick Start (Development)

### 1. Frontend
```bash
cd Bis_model3
npm install
npm run dev
```
Open **[http://localhost:5174/](http://localhost:5174/)** in your browser.

### 2. RAG Backend
```bash
cd Bis_model3/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
API Documentation available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 🏭 Production Deployment

### Option A: Docker Compose (Recommended for Cloud / Linux / Servers)
Builds multi-stage Nginx frontend + Python production backend with Gzip compression and security headers:
```bash
docker compose up --build -d
```
- Web Application: `http://localhost/` (Port 80)
- Backend API: `http://localhost:8000/` (Port 8000)

### Option B: Native Windows Production Script
Double-click or run:
```powershell
.\start-production.bat
```

### Option C: Production Manual Preview
```bash
# 1. Build frontend bundle
npm run build

# 2. Preview production build
npm run preview -- --port 5174 --host
```

---

## 🔒 Production Security & Reliability Features

- **Persistent Database**: File-backed storage in `backend/storage/isense_db.json` ensures state survives server restarts.
- **GZip Compression**: Fast compressed response delivery with `GZipMiddleware(minimum_size=1000)`.
- **Global ErrorBoundary**: Client-side runtime crashes are caught with a clean recovery screen and reload action.
- **Security Headers**: `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`.
- **Production SEO & Meta**: OpenGraph, Twitter card, robots.txt, and web app manifest included.
