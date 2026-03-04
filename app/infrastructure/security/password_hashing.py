from __future__ import annotations

import hashlib
import hmac
import secrets


ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
SALT_BYTES = 16


def hash_password(plain_password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERATIONS,
    )
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt, digest_hex = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != ALGORITHM:
        return False

    iterations = int(iterations_raw)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()

    return hmac.compare_digest(digest, digest_hex)
