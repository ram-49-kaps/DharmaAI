"""
Firebase ID token verification for DharmaAI.

Usage as FastAPI dependency:
    @app.post("/api/chat")
    async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
        ...
"""

import os
import logging
from typing import Optional

import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None
_security = HTTPBearer(auto_error=False)


def init_firebase() -> None:
    """Initialise Firebase Admin SDK from environment variables."""
    global _firebase_app
    if _firebase_app is not None:
        return

    project_id = os.getenv("FIREBASE_PROJECT_ID")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL")

    if not all([project_id, private_key, client_email]):
        logger.warning(
            "[Firebase] Missing env vars — auth will be DISABLED. "
            "Set FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL."
        )
        return

    try:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key,
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info(f"[Firebase] Initialised for project: {project_id}")
    except Exception as exc:
        logger.error(f"[Firebase] Init failed: {exc}")


def is_firebase_enabled() -> bool:
    """Return True if Firebase Admin SDK was initialised successfully."""
    return _firebase_app is not None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
) -> dict:
    """
    FastAPI dependency — verifies Firebase ID token from Authorization header.

    Returns decoded token dict with keys: uid, email, name, picture, etc.
    Raises 401 if token is missing or invalid.
    If Firebase is not configured (dev mode), returns a mock user.
    """
    if not is_firebase_enabled():
        # Dev mode: return a mock user so endpoints still work without Firebase
        return {
            "uid": "dev_user",
            "email": "dev@dharmaai.local",
            "name": "Dev User",
        }

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        decoded = auth.verify_id_token(credentials.credentials)
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.error(f"[Firebase] Token verification error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that additionally checks user is in ADMIN_USER_IDS."""
    admin_ids_raw = os.getenv("ADMIN_USER_IDS", "")
    admin_ids = {uid.strip() for uid in admin_ids_raw.split(",") if uid.strip()}

    # In dev mode or if no admins configured, allow all
    if not admin_ids or user.get("uid") == "dev_user":
        return user

    if user.get("uid") not in admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
