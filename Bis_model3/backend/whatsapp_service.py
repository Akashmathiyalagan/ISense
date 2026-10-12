"""
ISense BIS Certification Assistance — WhatsApp Cloud API Service
Provides production-grade Meta WhatsApp Cloud API integration:
- Webhook signature verification (HMAC-SHA256 constant-time)
- Durable message deduplication (file-backed with TTL pruning)
- WhatsApp-specific message formatting & length chunking (4096-char limit)
- Grounded RAG response formatting with BIS source citations
- Asynchronous outbound WhatsApp message dispatch via Meta Graph API
"""

import os
import re
import json
import time
import hmac
import hashlib
import logging
import asyncio
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import httpx

logger = logging.getLogger("isense_whatsapp")

# Maximum characters allowed per WhatsApp text message (Meta limit is 4096)
MAX_WHATSAPP_MSG_LENGTH = 3800
DEDUPLICATION_TTL_SECONDS = 86400  # 24 hours retention for message IDs


@dataclass
class WhatsAppConfig:
    """Secure WhatsApp Cloud API Configuration loaded from environment."""
    access_token: str
    phone_number_id: str
    verify_token: str
    app_secret: str
    graph_api_version: str
    flow_id: str = ""

    @staticmethod
    def _clean(val: Optional[str]) -> str:
        if not val:
            return ""
        return val.strip().strip('"').strip("'").strip()

    @classmethod
    def from_env(cls) -> "WhatsAppConfig":
        return cls(
            access_token=cls._clean(os.getenv("WHATSAPP_ACCESS_TOKEN")),
            phone_number_id=cls._clean(os.getenv("WHATSAPP_PHONE_NUMBER_ID")),
            verify_token=cls._clean(os.getenv("WHATSAPP_VERIFY_TOKEN")),
            app_secret=cls._clean(os.getenv("WHATSAPP_APP_SECRET")),
            graph_api_version=cls._clean(os.getenv("WHATSAPP_GRAPH_API_VERSION")) or "v22.0",
            flow_id=cls._clean(os.getenv("WHATSAPP_PRODUCT_INTAKE_FLOW_ID")),
        )

    def is_configured(self) -> bool:
        """Checks if all required outbound messaging credentials exist."""
        return bool(self.access_token and self.phone_number_id)

    def is_fully_configured(self) -> bool:
        """Checks if both webhook security and outbound messaging are configured."""
        return bool(
            self.access_token
            and self.phone_number_id
            and self.verify_token
            and self.app_secret
        )

    def get_readiness_report(self) -> Dict[str, Any]:
        """Safe readiness status report that strictly conceals all secret values."""
        return {
            "configured": self.is_configured(),
            "fullyConfigured": self.is_fully_configured(),
            "accessTokenConfigured": bool(self.access_token),
            "phoneNumberIdConfigured": bool(self.phone_number_id),
            "verifyTokenConfigured": bool(self.verify_token),
            "appSecretConfigured": bool(self.app_secret),
            "graphApiVersion": self.graph_api_version,
            "productIntakeFlowConfigured": bool(self.flow_id),
        }


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: Optional[str],
    app_secret: str
) -> bool:
    """
    Verifies X-Hub-Signature-256 header sent by Meta using constant-time HMAC-SHA256 comparison.
    Header format: 'sha256=<hex_digest>'
    """
    if not app_secret:
        # If no app secret is configured in the environment, log a security warning
        logger.warning("WHATSAPP_APP_SECRET is not configured; cannot verify signature.")
        return False

    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header on incoming webhook.")
        return False

    prefix = "sha256="
    if not signature_header.startswith(prefix):
        logger.warning("Malformed X-Hub-Signature-256 format (expected sha256= prefix).")
        return False

    received_sig = signature_header[len(prefix):].strip()
    expected_sig = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_sig, received_sig)


class DurableMessageStore:
    """
    Thread-safe, persistent deduplication store for Meta WhatsApp message IDs.
    Persists processed message IDs to disk with timestamps and automatic TTL cleanup.
    """
    def __init__(self, filepath: Optional[str] = None):
        if filepath is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_dir = os.path.join(base_dir, "storage")
            os.makedirs(storage_dir, exist_ok=True)
            self.filepath = os.path.join(storage_dir, "processed_whatsapp_messages.json")
        else:
            self.filepath = filepath
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        self._lock = asyncio.Lock()
        self._cache: Dict[str, float] = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._cache = {k: float(v) for k, v in data.items()}
                    elif isinstance(data, list):
                        self._cache = {k: time.time() for k in data}
            self._prune_expired()
        except Exception as e:
            logger.error(f"Error loading message deduplication store: {e}")
            self._cache = {}

    def _prune_expired(self):
        cutoff = time.time() - DEDUPLICATION_TTL_SECONDS
        initial_len = len(self._cache)
        self._cache = {k: v for k, v in self._cache.items() if v >= cutoff}
        if len(self._cache) < initial_len:
            self._save()

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except Exception as e:
            logger.error(f"Error writing deduplication store to disk: {e}")

    async def is_processed(self, message_id: str) -> bool:
        async with self._lock:
            self._prune_expired()
            return message_id in self._cache

    async def mark_processed(self, message_id: str):
        async with self._lock:
            self._cache[message_id] = time.time()
            self._save()

    def is_processed_sync(self, message_id: str) -> bool:
        self._prune_expired()
        return message_id in self._cache

    def mark_processed_sync(self, message_id: str):
        self._cache[message_id] = time.time()
        self._save()


def format_whatsapp_message(
    rag_content: str,
    sources: Optional[List[Dict[str, Any]]] = None,
    insufficient_evidence: bool = False
) -> str:
    """
    Formats grounded RAG response for optimal readability on WhatsApp:
    - Replaces Markdown bold '**text**' with WhatsApp '*text*'
    - Replaces markdown headers '### title' with '*title*'
    - Formats verified official BIS citations with clickable links
    - Appends statutory disclaimer
    """
    text = rag_content or ""

    # Convert Markdown headers: '### Header' -> '*Header*'
    text = re.sub(r'^(?:#{1,6})\s*(.+)$', r'*\1*', text, flags=re.MULTILINE)

    # Convert Markdown bold: '**text**' -> '*text*'
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)

    # Convert Markdown italic: '*text*' if not already converted, or preserve
    # Remove any stray HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # If insufficient evidence was flagged, ensure advisory notice and official portal guidance
    if insufficient_evidence and "manakonline.in" not in text.lower():
        text += (
            "\n\n🔍 *Verification Recommendation:* For unindexed standards or emerging product categories, "
            "please verify directly with the official BIS portal: https://www.manakonline.in or https://www.bis.gov.in"
        )

    # Format official BIS sources if available
    if sources and len(sources) > 0:
        sources_block = "\n\n📚 *Official BIS Sources:*"
        seen_refs = set()
        for src in sources[:4]:  # limit to top 4 citations for brevity on mobile
            doc_ref = src.get("documentRef") or src.get("title") or "BIS Standard"
            section = src.get("section") or ""
            source_url = src.get("sourceUrl") or "https://www.bis.gov.in"

            key = (doc_ref, section)
            if key in seen_refs:
                continue
            seen_refs.add(key)

            if section:
                sources_block += f"\n• *{doc_ref}* ({section})\n  🔗 {source_url}"
            else:
                sources_block += f"\n• *{doc_ref}*\n  🔗 {source_url}"

        text += sources_block

    # Standard Statutory Disclaimer for BIS Compliance
    disclaimer_text = (
        "\n\n⚖️ *Statutory Notice:* ISense provides independent regulatory guidance. "
        "Final certification licenses are granted solely by the Bureau of Indian Standards (BIS)."
    )
    if "*Statutory Notice:*" not in text and "*Statutory Boundary Notice:*" not in text:
        text += disclaimer_text

    return text.strip()


def split_whatsapp_message(text: str, max_chars: int = MAX_WHATSAPP_MSG_LENGTH) -> List[str]:
    """
    Splits long messages cleanly at paragraph or newline boundaries to respect
    WhatsApp's maximum text length without breaking URLs or citations.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    remaining = text

    while len(remaining) > max_chars:
        # Search for paragraph break before limit
        split_idx = remaining.rfind("\n\n", 0, max_chars)
        if split_idx == -1:
            # Fall back to single newline
            split_idx = remaining.rfind("\n", 0, max_chars)
        if split_idx == -1:
            # Fall back to sentence period
            split_idx = remaining.rfind(". ", 0, max_chars)
            if split_idx != -1:
                split_idx += 1  # include period
        if split_idx == -1:
            # Fall back to space
            split_idx = remaining.rfind(" ", 0, max_chars)

        if split_idx <= 0:
            # Hard break if no whitespace found
            split_idx = max_chars

        chunk = remaining[:split_idx].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_idx:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def uuid_token() -> str:
    return uuid.uuid4().hex


class WhatsAppClient:
    """
    Asynchronous Meta WhatsApp Cloud API Client.
    Dispatches outbound messages using httpx.AsyncClient with rate limiting,
    timeout handling, and strict error sanitization.
    """
    def __init__(self, config: Optional[WhatsAppConfig] = None):
        self.config = config or WhatsAppConfig.from_env()

    @property
    def messages_endpoint(self) -> str:
        return f"https://graph.facebook.com/{self.config.graph_api_version}/{self.config.phone_number_id}/messages"

    async def send_raw_text(self, recipient_wa_id: str, message_text: str) -> Dict[str, Any]:
        """
        Sends a single text message to a WhatsApp user via Meta Cloud API.
        Never leaks access token or app secret in error logs or exceptions.
        """
        if not self.config.is_configured():
            logger.warning("WhatsApp client not configured. Outbound message skipped.")
            return {
                "success": False,
                "error": "WhatsApp credentials not configured on backend."
            }

        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_wa_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.messages_endpoint,
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    resp_data = response.json()
                    logger.info(f"WhatsApp message dispatched to {recipient_wa_id}. Meta response: {resp_data}")
                    return {"success": True, "meta": resp_data}

                # Handle Meta API errors without logging authorization header
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"raw": response.text[:200]}

                logger.error(
                    f"Meta WhatsApp API returned HTTP {response.status_code}: {error_data}"
                )
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": "Failed to deliver WhatsApp message via Meta Cloud API."
                }

        except httpx.TimeoutException:
            logger.error(f"Timeout while dispatching WhatsApp message to {recipient_wa_id}")
            return {"success": False, "error": "Request to Meta Cloud API timed out."}
        except httpx.RequestError as e:
            logger.error(f"Network error while connecting to Meta WhatsApp API: {type(e).__name__}")
            return {"success": False, "error": "Network connectivity error connecting to Meta WhatsApp API."}
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {type(e).__name__}")
            return {"success": False, "error": "Internal communication error."}

    async def send_interactive_list(
        self,
        recipient_wa_id: str,
        message_text: str,
        options: List[str],
        button_title: str = "Choose option",
        section_title: str = "Answers",
    ) -> Dict[str, Any]:
        """Send a WhatsApp interactive list for the conversational questionnaire.

        List replies are received by the standard messages webhook, so this
        alternative does not require a published WhatsApp Flow.
        """
        if not self.config.is_configured():
            return {"success": False, "error": "WhatsApp credentials are not configured."}

        rows = []
        for index, option in enumerate(options[:10]):
            title = " ".join(str(option).split())[:24]
            if not title:
                continue
            rows.append({
                "id": f"option_{index + 1}",
                "title": title,
            })
        if not rows:
            return {"success": False, "error": "No valid interactive options were provided."}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_wa_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": (message_text or "Choose an option.")[:1024]},
                "action": {
                    "button": (button_title or "Choose option")[:20],
                    "sections": [{
                        "title": (section_title or "Answers")[:24],
                        "rows": rows,
                    }],
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.messages_endpoint, headers=headers, json=payload)
            if response.status_code in (200, 201):
                return {"success": True, "meta": response.json()}

            # Keep credentials out of logs and return a generic message to the caller.
            try:
                error_data = response.json().get("error", {})
                logger.error(
                    "Meta rejected interactive list (HTTP %s, code %s).",
                    response.status_code,
                    error_data.get("code", "unknown"),
                )
            except Exception:
                logger.error("Meta rejected interactive list (HTTP %s).", response.status_code)
            return {
                "success": False,
                "status_code": response.status_code,
                "error": "Failed to send WhatsApp interactive list.",
            }
        except httpx.TimeoutException:
            logger.error("Timeout while sending WhatsApp interactive list.")
            return {"success": False, "error": "Interactive list request timed out."}
        except httpx.RequestError as exc:
            logger.error("Network error while sending interactive list: %s", type(exc).__name__)
            return {"success": False, "error": "Network error sending WhatsApp interactive list."}

    async def send_product_intake_flow(
        self, recipient_wa_id: str, product_name: str
    ) -> Dict[str, Any]:
        """Send the published ISense product-intake WhatsApp Flow.

        The Flow is a static Meta-hosted form; the product name is passed as
        screen data and the completed form returns through the normal messages webhook.
        """
        if not self.config.is_configured():
            return {"success": False, "error": "WhatsApp credentials are not configured."}
        if not self.config.flow_id:
            return {"success": False, "error": "WHATSAPP_PRODUCT_INTAKE_FLOW_ID is not configured."}

        clean_product = " ".join((product_name or "").split())[:120] or "your product"
        flow_token = f"isense-intake:{recipient_wa_id}:{uuid_token()}"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_wa_id,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {"type": "text", "text": "ISense product details"},
                "body": {"text": f"Complete this short form about your {clean_product} so I can look for relevant BIS guidance."},
                "footer": {"text": "ISense provides guidance, not certification."},
                "action": {
                    "name": "flow",
                    "parameters": {
                        "flow_message_version": "3",
                        "flow_token": flow_token,
                        "flow_id": self.config.flow_id,
                        "flow_cta": "Fill details",
                        "flow_action": "navigate",
                        "flow_action_payload": {
                            "screen": "PRODUCT_DETAILS",
                            "data": {"product_name": clean_product}
                        }
                    }
                }
            }
        }
        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(self.messages_endpoint, headers=headers, json=payload)
            if response.status_code in (200, 201):
                return {"success": True, "meta": response.json()}
            try:
                err = response.json().get("error", {})
                detail = f"Meta rejected Flow message (HTTP {response.status_code}, code {err.get('code', 'unknown')})."
            except Exception:
                detail = f"Meta rejected Flow message (HTTP {response.status_code})."
            logger.error(detail)
            return {"success": False, "error": detail}
        except httpx.TimeoutException:
            logger.error("Timeout while sending WhatsApp product-intake Flow")
            return {"success": False, "error": "WhatsApp Flow send timed out."}
        except httpx.RequestError as exc:
            logger.error("Network error while sending WhatsApp product-intake Flow: %s", type(exc).__name__)
            return {"success": False, "error": "Network error while sending WhatsApp Flow."}

    async def send_rag_response(
        self,
        recipient_wa_id: str,
        rag_content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        insufficient_evidence: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Formats and sends a grounded RAG response to a WhatsApp recipient.
        Splits long responses cleanly across multiple messages if necessary.
        """
        formatted_text = format_whatsapp_message(
            rag_content=rag_content,
            sources=sources,
            insufficient_evidence=insufficient_evidence
        )

        message_chunks = split_whatsapp_message(formatted_text)
        results = []

        for chunk in message_chunks:
            res = await self.send_raw_text(recipient_wa_id, chunk)
            results.append(res)
            # Brief pause between multi-part chunks for sequential delivery
            if len(message_chunks) > 1:
                await asyncio.sleep(0.4)

        return results


# Global instances
durable_message_store = DurableMessageStore()
whatsapp_client = WhatsAppClient()
