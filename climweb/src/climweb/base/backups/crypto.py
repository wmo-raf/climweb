"""
Symmetric encryption for secrets stored in the database (OAuth refresh tokens).

The key is derived from Django's ``SECRET_KEY`` so no additional configuration
is required. If you rotate ``SECRET_KEY``, previously stored tokens can no
longer be decrypted and accounts must be reconnected.
"""
import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet():
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_text(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
