import logging
from math import e
import token
import jwt

from datetime import UTC, timedelta, datetime
from typing import Optional, Union
from uu import decode, encode

from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from open_knowledge.models.users import Users
from open_knowledge.env import SRC_LOG_LEVELS, WEBUI_SECRET_KEY, ENV, WEBUI_ADMIN_USER
from open_knowledge.constants import ERROR_MESSAGES


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OAUTH"])

SESSION_SECRET = WEBUI_SECRET_KEY
ALGORITHM = "HS256"


##############
# Auth Utils
##############


bearer_security = HTTPBearer(auto_error=False)


def create_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    payload = data.copy()

    if expires_delta:
        expires = datetime.now(UTC) + expires_delta
        payload.update({"exp": expires})

    encode_jwt = jwt.encode(payload, SESSION_SECRET, algorithm=[ALGORITHM])
    return encode_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        decoded = jwt.decode(token, SESSION_SECRET, algorithms=(ALGORITHM))
        return decode
    except Exception:
        log.error(f"Error decoding the token: {e}")
        return None


def extract_token_from_auth_header(auth_header: str):
    return auth_header[len("Bearer "):]


def get_http_authorization_cred(auth_header: Optional[str]):
    if not auth_header:
        return None

    try:
        scheme, credentials = auth_header.split(" ")
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)
    except Exception:
        return None


def get_current_user(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    auth_token: HTTPAuthorizationCredentials = Depends(bearer_security),
):
    if ENV == "dev":
        # Disable authentication
        user = Users.get_user_by_id(WEBUI_ADMIN_USER)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User `{WEBUI_ADMIN_USER}` not found"
            )
        else:
            return user
    else:
        token = None

        if auth_token is not None:
            token = auth_token.credentials

        if token is None and "token" in request.cookies:
            token = request.cookies.get("token")

        # auth by jwt token
        try:
            data = decode_token(token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        if data is not None and "id" in data:
            user = Users.get_user_by_id(data["id"])
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=ERROR_MESSAGES.INVALID_TOKEN
                )

            # TODO: Refresh the user's last active timestamp asynchronously
            # to prevent blocking the request
            if background_tasks:
                # background_tasks.add_task(Users.update_user_last_active_by_id, user.id)
                pass
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.UNAUTHORIZED
            )


def get_verified_user(user=Depends(get_current_user)):
    if not user.user_info or user.user_info.role not in {"user", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED
        )
    return user


def get_admin_user(user=Depends(get_current_user)):
    if user.user_info and user.user_info.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED
        )
    return user
