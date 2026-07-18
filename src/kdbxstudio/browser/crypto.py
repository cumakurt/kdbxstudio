"""TweetNaCl / libsodium helpers matching KeePassXC-Browser."""

from __future__ import annotations

import base64

from nacl.public import Box, PrivateKey, PublicKey
from nacl.utils import random

NONCE_SIZE = 24
VERSION = "2.7.6"
TRUE_STR = "true"
FALSE_STR = "false"


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def generate_keypair() -> tuple[str, str]:
    """Return (public_key_b64, secret_key_b64)."""
    sk = PrivateKey.generate()
    return b64encode(bytes(sk.public_key)), b64encode(bytes(sk))


def increment_nonce(nonce_b64: str) -> str:
    raw = bytearray(b64decode(nonce_b64))
    # sodium_increment: little-endian style increment
    for i in range(len(raw)):
        raw[i] = (raw[i] + 1) & 0xFF
        if raw[i] != 0:
            break
    return b64encode(bytes(raw))


def encrypt_json(plaintext: str, nonce_b64: str, their_pk_b64: str, our_sk_b64: str) -> str:
    box = Box(PrivateKey(b64decode(our_sk_b64)), PublicKey(b64decode(their_pk_b64)))
    nonce = b64decode(nonce_b64)
    encrypted = box.encrypt(plaintext.encode("utf-8"), nonce)
    # PyNaCl prepends nonce; KeePassXC crypto_box_easy does not.
    ciphertext = encrypted.ciphertext
    return b64encode(ciphertext)


def decrypt_json(message_b64: str, nonce_b64: str, their_pk_b64: str, our_sk_b64: str) -> str:
    box = Box(PrivateKey(b64decode(our_sk_b64)), PublicKey(b64decode(their_pk_b64)))
    nonce = b64decode(nonce_b64)
    plaintext = box.decrypt(b64decode(message_b64), nonce)
    return plaintext.decode("utf-8")


def random_nonce_b64() -> str:
    return b64encode(random(NONCE_SIZE))
