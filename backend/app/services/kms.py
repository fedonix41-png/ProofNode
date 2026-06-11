import base64
import hashlib
from cryptography.fernet import Fernet
from backend.app.config import settings

def _get_fernet_key() -> bytes:
    # Derive a valid 32-byte key using SHA-256 to ensure any string config is compatible
    raw_key = settings.kms_master_key.encode("utf-8")
    hash_bytes = hashlib.sha256(raw_key).digest()
    return base64.urlsafe_b64encode(hash_bytes)

class KMSService:
    def __init__(self):
        self._fernet = Fernet(_get_fernet_key())

    def encrypt_key(self, private_key_hex: str) -> str:
        """Encrypts a private key using the derived KMS master key."""
        encrypted_bytes = self._fernet.encrypt(private_key_hex.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def decrypt_key(self, encrypted_str: str) -> str:
        """Decrypts a private key using the derived KMS master key."""
        decrypted_bytes = self._fernet.decrypt(encrypted_str.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")

kms_service = KMSService()
