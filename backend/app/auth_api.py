"""Authentication API router, dependencies, and browser-security middleware.

This router is intentionally not imported by ``main.py`` until auth migrations
are confirmed and startup no longer creates schemas implicitly.  Mount it only
behind the approved migration and trusted-origin deployment gates.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import secrets
from typing import Any, Awaitable, Callable

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .auth_models import (
    AuthRefreshTokenHistoryModel,
    AuthSessionModel,
    RoleModel,
    UserModel,
    UserRoleModel,
)
from .auth_service import (
    InvalidRefreshTokenError,
    RefreshServiceUnavailableError,
    rotate_refresh_token,
)
from .config import settings
from .database import get_db
from .security import (
    InvalidAccessTokenError,
    SecurityConfigurationError,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    validate_access_token_configuration,
    verify_access_token,
    verify_password,
)


AUTH_BODY_MAX_BYTES = 16 * 1024
_REFRESH_COOKIE_PATH = f"{settings.API_PREFIX}/auth"
_GENERIC_CREDENTIALS = "Invalid email or password."
_GENERIC_AUTHENTICATION = "Authentication required."
_STORAGE_UNAVAILABLE = "Authentication service is unavailable."

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/auth",
    tags=["Authentication"],
)
_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("Invalid email address.")
        return normalized


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    user: UserModel
    session: AuthSessionModel
    roles: tuple[str, ...]


class AuthRequestSecurityMiddleware:
    """Bound auth request bodies and mark every auth response non-cacheable."""

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive, send) -> None:
        request_path = scope.get("path", "")
        if (
            scope.get("type") != "http"
            or not (
                request_path == _REFRESH_COOKIE_PATH
                or request_path.startswith(f"{_REFRESH_COOKIE_PATH}/")
            )
        ):
            await self.app(scope, receive, send)
            return

        async def send_no_store(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers = [
                    (name, value)
                    for name, value in headers
                    if name.lower() not in {b"cache-control", b"pragma"}
                ]
                headers.extend(
                    [(b"cache-control", b"no-store"), (b"pragma", b"no-cache")]
                )
                message["headers"] = headers
            await send(message)

        if scope.get("method") not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send_no_store)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                if int(content_length) > AUTH_BODY_MAX_BYTES:
                    await self._too_large(send_no_store)
                    return
            except ValueError:
                await self._too_large(send_no_store)
                return

        messages: list[dict[str, Any]] = []
        body_length = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            messages.append(message)
            body_length += len(message.get("body", b""))
            if body_length > AUTH_BODY_MAX_BYTES:
                await self._too_large(send_no_store)
                return
            if not message.get("more_body", False):
                break

        remaining = iter(messages)

        async def replay_receive() -> dict[str, Any]:
            try:
                return next(remaining)
            except StopIteration:
                return await receive()

        await self.app(scope, replay_receive, send_no_store)

    @staticmethod
    async def _too_large(
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        body = b'{"detail":"Request body is too large."}'
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_GENERIC_AUTHENTICATION,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=_STORAGE_UNAVAILABLE,
    )


def _invalid_auth_response(clear_cookies: bool = False) -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": _GENERIC_AUTHENTICATION},
        headers={"WWW-Authenticate": "Bearer"},
    )
    if clear_cookies:
        _clear_auth_cookies(response)
    return response


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _require_trusted_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    trusted_origins = {
        configured.rstrip("/") for configured in settings.AUTH_TRUSTED_ORIGINS
    }
    if (
        not trusted_origins
        or origin is None
        or origin.rstrip("/") not in trusted_origins
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request origin is not allowed.",
        )


def _require_csrf(request: Request) -> None:
    _require_trusted_origin(request)
    cookie_value = request.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)
    header_value = request.headers.get(settings.AUTH_CSRF_HEADER_NAME)
    if (
        not cookie_value
        or not header_value
        or not secrets.compare_digest(cookie_value, header_value)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request verification failed.",
        )


def _set_auth_cookies(
    response: Response,
    refresh_token: str,
    csrf_token: str,
    expires_at: datetime,
) -> None:
    max_age = max(0, int((_as_utc(expires_at) - _now_utc()).total_seconds()))
    common = {
        "path": _REFRESH_COOKIE_PATH,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "max_age": max_age,
    }
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        **common,
    )
    response.set_cookie(
        settings.AUTH_CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        path="/",
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=max_age,
    )


def _clear_auth_cookies(response: Response) -> None:
    common = {
        "path": _REFRESH_COOKIE_PATH,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        httponly=True,
        **common,
    )
    response.delete_cookie(
        settings.AUTH_CSRF_COOKIE_NAME,
        path="/",
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        httponly=False,
    )


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    return hash_password(secrets.token_urlsafe(32))


def _load_principal(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> AuthenticatedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        claims = verify_access_token(credentials.credentials)
    except InvalidAccessTokenError:
        raise _unauthorized() from None

    try:
        auth_session = db.scalar(
            select(AuthSessionModel)
            .where(AuthSessionModel.id == claims.session_id)
            .execution_options(populate_existing=True)
        )
        if (
            auth_session is None
            or auth_session.user_id != claims.user_id
            or auth_session.revoked_at is not None
            or _now_utc() >= _as_utc(auth_session.expires_at)
        ):
            raise _unauthorized()
        user = db.scalar(
            select(UserModel)
            .where(UserModel.id == claims.user_id)
            .execution_options(populate_existing=True)
        )
        if user is None or not user.is_active:
            raise _unauthorized()
        roles = tuple(
            db.scalars(
                select(RoleModel.name)
                .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
                .where(UserRoleModel.user_id == user.id)
                .order_by(RoleModel.name)
            ).all()
        )
        return AuthenticatedPrincipal(
            user=user,
            session=auth_session,
            roles=roles,
        )
    except SQLAlchemyError:
        db.rollback()
        raise _database_unavailable() from None


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AuthenticatedPrincipal:
    return _load_principal(credentials, db)


def require_roles(*allowed_roles: str):
    required = frozenset(allowed_roles)

    async def dependency(
        principal: AuthenticatedPrincipal = Depends(get_current_principal),
    ) -> AuthenticatedPrincipal:
        if not required.intersection(principal.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return principal

    return dependency


def _issue_access_token(user_id: str, session_id: str) -> str:
    try:
        return create_access_token(user_id=user_id, session_id=session_id)
    except SecurityConfigurationError:
        raise _database_unavailable() from None


def _commit_or_unavailable(db: Session) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise _database_unavailable() from None


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    _require_trusted_origin(request)
    if db.in_transaction():
        raise _database_unavailable()

    now = _now_utc()
    result: dict[str, Any] | None = None
    login_failed = False
    try:
        with db.begin():
            user = db.scalar(
                select(UserModel)
                .where(UserModel.email == payload.email)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if user is None:
                verify_password(payload.password, _dummy_password_hash())
                login_failed = True
            else:
                lock_until = None
                if user.locked_until is not None:
                    lock_until = _as_utc(user.locked_until)
                locked = lock_until is not None and now < lock_until
                if not user.is_active or locked:
                    verify_password(payload.password, _dummy_password_hash())
                    login_failed = True
                else:
                    if lock_until is not None:
                        user.locked_until = None
                        user.failed_login_count = 0
                    password_matches = verify_password(
                        payload.password,
                        user.password_hash,
                    )
                    if not password_matches:
                        user.failed_login_count += 1
                        if (
                            user.failed_login_count
                            >= settings.AUTH_LOGIN_MAX_FAILURES
                        ):
                            user.locked_until = now + timedelta(
                                minutes=settings.AUTH_LOGIN_LOCKOUT_MINUTES
                            )
                        login_failed = True
                    else:
                        user.failed_login_count = 0
                        user.locked_until = None
                        raw_refresh_token = generate_refresh_token()
                        csrf_token = secrets.token_urlsafe(32)
                        absolute_expiry = now + timedelta(
                            days=settings.AUTH_SESSION_EXPIRE_DAYS
                        )
                        refresh_expiry = min(
                            now
                            + timedelta(
                                days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS
                            ),
                            absolute_expiry,
                        )
                        auth_session = AuthSessionModel(
                            user_id=user.id,
                            token_hash=hash_refresh_token(raw_refresh_token),
                            issued_at=now,
                            expires_at=absolute_expiry,
                            current_refresh_expires_at=refresh_expiry,
                        )
                        db.add(auth_session)
                        db.flush()
                        access_token = _issue_access_token(
                            user.id,
                            auth_session.id,
                        )
                        result = {
                            "access_token": access_token,
                            "token_type": "bearer",
                            "expires_in": (
                                settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60
                            ),
                            "csrf_token": csrf_token,
                            "refresh_token": raw_refresh_token,
                            "refresh_expires_at": refresh_expiry,
                        }
    except SQLAlchemyError:
        db.rollback()
        raise _database_unavailable() from None

    if login_failed or result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_GENERIC_CREDENTIALS,
        )

    _set_auth_cookies(
        response,
        result.pop("refresh_token"),
        result["csrf_token"],
        result.pop("refresh_expires_at"),
    )
    return result


@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    _require_csrf(request)
    raw_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if not raw_token:
        return _invalid_auth_response(clear_cookies=True)

    try:
        validate_access_token_configuration()
    except SecurityConfigurationError:
        raise _database_unavailable() from None

    try:
        rotation = rotate_refresh_token(
            db,
            raw_token,
            token_lifetime=timedelta(
                days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )
        access_token = _issue_access_token(
            rotation.user_id,
            rotation.session_id,
        )
    except InvalidRefreshTokenError:
        return _invalid_auth_response(clear_cookies=True)
    except RefreshServiceUnavailableError:
        raise _database_unavailable() from None

    csrf_token = secrets.token_urlsafe(32)
    _set_auth_cookies(
        response,
        rotation.token,
        csrf_token,
        rotation.expires_at,
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "csrf_token": csrf_token,
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
):
    _require_csrf(request)
    claims = None
    if credentials is not None and credentials.scheme.lower() == "bearer":
        try:
            claims = verify_access_token(credentials.credentials)
        except InvalidAccessTokenError:
            claims = None

    raw_refresh_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    try:
        with db.begin():
            session_id = None
            if claims is not None:
                session_id = claims.session_id
            elif raw_refresh_token:
                refresh_hash = hash_refresh_token(raw_refresh_token)
                session_id = db.scalar(
                    select(AuthSessionModel.id).where(
                        AuthSessionModel.token_hash == refresh_hash
                    )
                )
                if session_id is None:
                    session_id = db.scalar(
                        select(AuthRefreshTokenHistoryModel.session_id).where(
                            AuthRefreshTokenHistoryModel.token_hash
                            == refresh_hash
                        )
                    )

            if session_id is not None:
                auth_session = db.scalar(
                    select(AuthSessionModel)
                    .where(AuthSessionModel.id == session_id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
                if (
                    auth_session is not None
                    and (
                        claims is None
                        or auth_session.user_id == claims.user_id
                    )
                    and auth_session.revoked_at is None
                ):
                    auth_session.revoked_at = _now_utc()
    except SQLAlchemyError:
        db.rollback()
        raise _database_unavailable() from None

    _clear_auth_cookies(response)
    return {"status": "logged_out"}


@router.post("/logout-all")
def logout_all(
    request: Request,
    response: Response,
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_csrf(request)
    try:
        sessions = db.scalars(
            select(AuthSessionModel)
            .where(AuthSessionModel.user_id == principal.user.id)
            .order_by(AuthSessionModel.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        now = _now_utc()
        for auth_session in sessions:
            if auth_session.revoked_at is None:
                auth_session.revoked_at = now
        _commit_or_unavailable(db)
    except SQLAlchemyError:
        db.rollback()
        raise _database_unavailable() from None

    _clear_auth_cookies(response)
    return {"status": "logged_out"}


@router.get("/me")
def current_user(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
):
    return {
        "id": principal.user.id,
        "email": principal.user.email.strip().lower(),
        "roles": list(principal.roles),
    }
