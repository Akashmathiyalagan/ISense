"""Encrypted WhatsApp Flows data-exchange endpoint for ISense.

Meta sends encrypted_flow_data, encrypted_aes_key and initial_vector. The
handler decrypts requests with the configured RSA private key, returns an
encrypted data-exchange response, and chooses a pre-defined product-specific
screen based on the product name. Keep the private key secret.
"""
import base64
import json
import logging
import os
from typing import Any, Dict

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("isense_flow_endpoint")


def _load_private_key():
    pem_text = os.getenv("WHATSAPP_FLOW_PRIVATE_KEY", "").strip()
    key_path = os.getenv("WHATSAPP_FLOW_PRIVATE_KEY_PATH", "").strip()
    if key_path:
        with open(key_path, "rb") as key_file:
            pem = key_file.read()
    elif pem_text:
        pem = pem_text.replace("\\n", "\n").encode("utf-8")
    else:
        raise RuntimeError("Set WHATSAPP_FLOW_PRIVATE_KEY_PATH or WHATSAPP_FLOW_PRIVATE_KEY")
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048:
        raise RuntimeError("WhatsApp Flow private key must be RSA with at least 2048 bits")
    return key


def decrypt_request(payload: Dict[str, Any]):
    private_key = _load_private_key()
    aes_key = private_key.decrypt(
        base64.b64decode(payload["encrypted_aes_key"]),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    iv = base64.b64decode(payload["initial_vector"])
    encrypted_data = base64.b64decode(payload["encrypted_flow_data"])
    clear = AESGCM(aes_key).decrypt(iv, encrypted_data, None)
    return json.loads(clear.decode("utf-8")), aes_key, iv


def encrypt_response(response: Dict[str, Any], aes_key: bytes, iv: bytes) -> str:
    flipped_iv = bytes(byte ^ 0xFF for byte in iv)
    clear = json.dumps(response, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    encrypted = AESGCM(aes_key).encrypt(flipped_iv, clear, None)
    return base64.b64encode(encrypted).decode("ascii")


def choose_product_screen(product_name: str) -> str:
    name = (product_name or "").lower()
    if any(word in name for word in ("bottle", "flask", "vacuum tumbler", "thermos")):
        return "WATER_BOTTLE"
    if any(word in name for word in ("backpack", "back pack", "back bag", "school bag", "rucksack", "bag")):
        return "BACKPACK"
    if any(word in name for word in ("rc car", "remote control car", "toy car", "toy", "toy vehicle")):
        return "RC_CAR"
    return "OTHER_PRODUCT"


def _response_for_request(body: Dict[str, Any]) -> Dict[str, Any]:
    action = str(body.get("action", ""))
    if action == "ping":
        return {"data": {"status": "active"}}

    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    screen = str(body.get("screen", ""))
    # PRODUCT_ROUTER uses a data_exchange footer. Its payload includes product_name.
    if action in {"INIT", "data_exchange"} and (screen in {"", "PRODUCT_ROUTER"} or action == "INIT"):
        product_name = str(data.get("product_name", data.get("productName", "your product")))[:120]
        return {
            "screen": choose_product_screen(product_name),
            "data": {"product_name": product_name or "your product"},
        }

    # These screens use complete for submission; this is a safe fallback if Meta
    # sends an additional exchange event from a future screen version.
    if action == "data_exchange":
        return {"screen": "OTHER_PRODUCT", "data": {"product_name": str(data.get("product_name", "your product"))[:120]}}
    return {"data": {"status": "active"}}


def process_encrypted_request(payload: Dict[str, Any]) -> str:
    body, aes_key, iv = decrypt_request(payload)
    response = _response_for_request(body)
    return encrypt_response(response, aes_key, iv)
