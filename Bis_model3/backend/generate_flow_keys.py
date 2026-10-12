"""Generate RSA-2048 keys for WhatsApp Flow endpoint encryption.
Run: python generate_flow_keys.py [output_directory]
Keep whatsapp_flow_private.pem secret and never commit it.
"""
import sys
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

out = Path(sys.argv[1] if len(sys.argv) > 1 else "secrets")
out.mkdir(parents=True, exist_ok=True)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
private_pem = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
public_pem = private_key.public_key().public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
private_path = out / "whatsapp_flow_private.pem"
public_path = out / "whatsapp_flow_public.pem"
private_path.write_bytes(private_pem)
public_path.write_bytes(public_pem)
print(f"Private key: {private_path.resolve()} (keep secret; do not commit)")
print(f"Public key:  {public_path.resolve()} (register this with Meta)")
