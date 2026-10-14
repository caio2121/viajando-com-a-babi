from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


SCHEME = "pbkdf2_sha256"
ITERATIONS = 600_000


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("a senha deve ter pelo menos 12 caracteres")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{SCHEME}${ITERATIONS}${base64.urlsafe_b64encode(salt).decode()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_text, digest_text = encoded.split("$", 3)
        if scheme != SCHEME:
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = bytes.fromhex(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError, UnicodeError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
