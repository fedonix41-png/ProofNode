import pytest
from backend.app.services.kms import LocalKMSProvider, AWSKMSProvider, VaultKMSProvider
import os

def test_local_kms_provider():
    provider = LocalKMSProvider()
    plaintext = "super_secret_private_key_123"
    encrypted = provider.encrypt_key(plaintext)
    assert encrypted != plaintext
    decrypted = provider.decrypt_key(encrypted)
    assert decrypted == plaintext
