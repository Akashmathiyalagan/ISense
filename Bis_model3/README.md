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

---

## 📱 Meta WhatsApp Cloud API Integration (Windows PowerShell Guide)

ISense connects directly to the **Meta WhatsApp Cloud API (Graph v22.0)** to provide regulatory guidance via WhatsApp.

### Webhook & Status Endpoints
- **Webhook Verification (GET)**: `http://localhost:8000/api/webhook/whatsapp`
- **Incoming Messages (POST)**: `http://localhost:8000/api/webhook/whatsapp`
- **Status & Diagnostics (GET)**: `http://localhost:8000/api/whatsapp/status`

---

### Step 1: Install Dependencies
Open Windows PowerShell in the backend directory:
```powershell
cd e:\BIS\BIS_model3\Bis_model3\backend
python -m pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` if not already present:
```powershell
Copy-Item .env.example .env
```
Populate the WhatsApp configuration block in `backend/.env`:
```dotenv
# Meta WhatsApp Cloud API Credentials
WHATSAPP_ACCESS_TOKEN="<Your_Meta_System_User_or_Temporary_Access_Token>"
WHATSAPP_PHONE_NUMBER_ID="<Your_Meta_Phone_Number_ID>"
WHATSAPP_VERIFY_TOKEN="<Your_Strong_Random_Verify_Token>"
WHATSAPP_APP_SECRET="<Your_Meta_App_Secret>"
WHATSAPP_GRAPH_API_VERSION="v22.0"
```

> **Security Note:** Never commit `.env` or paste real tokens into repositories. `.gitignore` is pre-configured to exclude all `.env` files.

---

### Step 3: Meta Developer App Setup & Credentials
1. Navigate to the [Meta for Developers Portal](https://developers.facebook.com/) and open your Business App.
2. In the left sidebar, expand **WhatsApp** and click **API Setup**.
3. **Phone Number ID**: Copy the numeric ID from the **Phone number ID** field and set it as `WHATSAPP_PHONE_NUMBER_ID`.
4. **Access Token**:
   - For rapid testing, copy the 24-hour **Temporary access token**.
   - For production, create a **System User** with the `whatsapp_business_messaging` permission under Meta Business Settings to generate a permanent token. Set as `WHATSAPP_ACCESS_TOKEN`.
5. **App Secret**: Navigate to **App Settings** -> **Basic** -> click **Show** next to **App Secret**. Copy and set as `WHATSAPP_APP_SECRET`.
6. **Verify Token**: Choose any secret random string (e.g. `ISense_BIS_Verify_2026_Ak7x9pQ2`) and set it as `WHATSAPP_VERIFY_TOKEN`.

---

### Step 4: Run the Backend Locally
Start the FastAPI server:
```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
Verify status readiness:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/whatsapp/status" -Method GET
```
Expected output:
```json
{
  "status": "ready",
  "service": "Meta WhatsApp Cloud API (Graph v22.0)",
  "webhookEndpoint": "/api/webhook/whatsapp",
  "readiness": {
    "configured": true,
    "fullyConfigured": true
  }
}
```

---

### Step 5: Expose Backend via HTTPS Development Tunnel
Meta requires a public HTTPS URL for webhooks. In a new PowerShell terminal, run either `ngrok` or `cloudflared`:

**Option A (ngrok):**
```powershell
ngrok http 8000
```
*Copy the HTTPS forwarding address (e.g., `https://abc-123.ngrok-free.app`).*

**Option B (Cloudflare Tunnel - free, no account required):**
```powershell
winget install --id Cloudflare.cloudflared
cloudflared tunnel --url http://127.0.0.1:8000
```
*Copy the generated `https://*.trycloudflare.com` URL.*

---

### Step 6: Configure Callback URL & Verification in Meta
1. In Meta Developer Portal, go to **WhatsApp** -> **Configuration**.
2. Under **Webhook**, click **Edit**.
3. In **Callback URL**, enter:
   ```
   https://<your-public-tunnel-domain>/api/webhook/whatsapp
   ```
4. In **Verify token**, enter your configured `WHATSAPP_VERIFY_TOKEN`.
5. Click **Verify and save**. Meta will issue a `GET` request to your backend; the server validates the token with constant-time HMAC comparison and returns `hub.challenge` immediately.

---

### Step 7: Subscribe to WhatsApp Message Events
1. In Meta Developer Portal -> **WhatsApp** -> **Configuration** -> **Webhook fields**.
2. Locate the **messages** field and click **Manage** / **Subscribe**.
3. Ensure the subscription toggle is enabled for `messages`.

---

### Step 8: Test Integration with a Permitted WhatsApp Recipient
1. In Meta Developer Portal -> **WhatsApp** -> **API Setup**.
2. Under **Step 2: Send and receive messages**, locate the **To** dropdown.
3. If using a development test phone number, click **Manage phone number list** and add your personal WhatsApp number (+91...). Complete the verification code sent by Meta.
4. Send an inquiry from your WhatsApp phone to the Meta test number:
   - *"What standard applies to LED lamps?"*
   - *"What are the insulation resistance limits under IS 16102?"*
   - *"What Indian Standard covers ceiling fans?"*
5. The backend validates `X-Hub-Signature-256`, retrieves grounded regulatory clauses via `rag_engine`, and automatically replies with formatted WhatsApp text, official BIS citations, and statutory disclaimers!

---

### Step 9: Troubleshooting Common Errors

| Error / Code | Root Cause | Solution |
| :--- | :--- | :--- |
| **403 Verification token mismatch** | `hub.verify_token` did not match `WHATSAPP_VERIFY_TOKEN`. | Check that the token entered in Meta matches `WHATSAPP_VERIFY_TOKEN` in `.env`. |
| **401 Missing / Invalid signature** | `X-Hub-Signature-256` header missing or hash mismatch. | Verify `WHATSAPP_APP_SECRET` matches your Meta App Secret under App Settings -> Basic. |
| **190 Invalid OAuth Access Token** | Temporary token has expired (24h limit). | Generate a new token in API Setup or create a permanent System User Token. |
| **131047 Message failed to send** | Recipient is outside 24-hour customer service window. | The user must first message your WhatsApp business number before free-form answers can be dispatched. |
| **Duplicate Message Ignored** | Meta retried delivery of an already processed event. | Normal behavior; ISense automatically deduplicates via persistent store `storage/processed_whatsapp_messages.json`. |

