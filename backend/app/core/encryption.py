"""
ShelfIQ Backend — AES-256 Field-Level Encryption.

Used to encrypt sensitive data stored in the database:
- RTSP camera stream URLs
- Associate WhatsApp phone numbers

Never store these in plaintext. Never log them.
"""
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend

from backend.app.core.config import settings


def _get_key() -> bytes:
    """Get the AES-256 encryption key from settings."""
    key_hex = settings.FIELD_ENCRYPTION_KEY
    key_bytes = bytes.fromhex(key_hex)
    if len(key_bytes) != 32:
        raise ValueError(
            f"FIELD_ENCRYPTION_KEY must be 32 bytes (64 hex chars). Got {len(key_bytes)} bytes."
        )
    return key_bytes


def encrypt_field(plaintext: str) -> bytes:
    """
    Encrypt a string field using AES-256-CBC.

    Returns:
        bytes: IV (16 bytes) + ciphertext, suitable for BYTEA column storage.
    """
    if not plaintext:
        return b""

    key = _get_key()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # PKCS7 padding
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv + ciphertext


def decrypt_field(encrypted: bytes) -> str:
    """
    Decrypt an AES-256-CBC encrypted field.

    Args:
        encrypted: IV (first 16 bytes) + ciphertext.

    Returns:
        Decrypted plaintext string.
    """
    if not encrypted:
        return ""

    key = _get_key()
    iv = encrypted[:16]
    ciphertext = encrypted[16:]

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # PKCS7 unpadding
    unpadder = sym_padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()

    return data.decode("utf-8")


def mask_phone(phone: str) -> str:
    """
    Mask a phone number for display: +91 98765****0

    Never log or display full phone numbers.
    """
    if len(phone) <= 4:
        return "****"
    return phone[:6] + "****" + phone[-1]
