import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

KEYS_DIR = Path(__file__).parent / "keys"

def load_rsa_key(env_name, filename):
    """
    Load an RSA key from an environment variable.
    Fall back to a local PEM file during development.
    """
    key = os.getenv(env_name)

    if key:
        return key.replace("\\n", "\n")

    key_file = KEYS_DIR / filename

    if key_file.exists():
        return key_file.read_text(encoding="utf-8")

    raise RuntimeError(
        f"Missing {env_name}: configure an environment variable "
        f"or provide {key_file}"
    )


class Config:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    SQLALCHEMY_DATABASE_URI = database_url.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SERVER_Y_URL = os.getenv("SERVER_Y_URL")
    SERVER_Y_API_KEY = os.getenv("SERVER_Y_API_KEY")
    SERVER_X_API_KEY = os.getenv("SERVER_X_API_KEY")

    JWT_ALGORITHM = "RS256"
    JWT_DECODE_ALGORITHMS = ["RS256"]
    JWT_ACCESS_TOKEN_EXPIRES = 1800

    JWT_PRIVATE_KEY = load_rsa_key(
        "JWT_PRIVATE_KEY",
        "private_key.pem"
    )

    JWT_PUBLIC_KEY = load_rsa_key(
        "JWT_PUBLIC_KEY",
        "public_key.pem"
    )