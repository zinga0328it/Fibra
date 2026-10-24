"""Experimental passwordless Telegram approval protocol for Lia Fibra.

Pure Python state machine; no FastAPI routes, Telegram requests, DB writes,
JWT issuance, or side effects. DO NOT use this in production. The gateway
must authenticate webhook traffic and load TelegramBinding from trusted,
verified enrollment records (never request JSON).
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
from dataclasses import dataclass
from typing import Literal


class LoginError(Exception):
    """Stable, generic error code. Do not leak tokens in logs."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class TelegramBinding:
    """MUST be loaded from trusted records after verified bot enrollment."""

    tenant_id: str
    user_id: str
    telegram_user_id: int
    private_chat_id: int


@dataclass(frozen=True)
class BrowserChallenge:
    """Deliver only to the initiating browser over authenticated HTTPS."""

    request_id: str
    browser_secret: str
    comparison_code: str
    expires_at: int


@dataclass(frozen=True)
class BotNotification:
    """Deliver only through server-side Telegram Bot API to linked chat."""

    chat_id: int
    message: str
    approve_callback: str
    deny_callback: str


@dataclass(frozen=True)
class LoginGrant:
    """One-time proof for a separate, trusted session issuer (not a JWT)."""

    tenant_id: str
    user_id: str
    telegram_user_id: int
    authenticated_at: int
    amr: tuple[str, ...] = ("telegram_approval",)


@dataclass
class _Challenge:
    binding: TelegramBinding
    browser_secret_digest: bytes
    expires_at: int
    state: Literal["pending", "approved", "denied", "expired", "consumed"] = "pending"
    failures: int = 0


_ID = re.compile(r"[A-Za-z0-9_-]{1,96}\Z")
_CALLBACK = re.compile(r"login:(approve|deny):([A-Za-z0-9_-]{20,40})\Z")


class TelegramPasswordless:
    """Non-persistent proof of concept for chat-confirmed login.

    Gateway requirements: verified account enrollment, Telegram webhook
    secret-header validation, Bot API send, CSRF protections, real rate limits,
    shared transactional storage, signed sessions and per-WR authorization.
    """

    def __init__(self, webhook_secret: str, ttl_seconds: int = 120):
        if len(webhook_secret) < 32 or not webhook_secret.isascii():
            raise ValueError("webhook_secret must be a strong configured secret")
        if not (30 <= ttl_seconds <= 300):
            raise ValueError("ttl_seconds must be between 30 and 300")
        self._webhook_secret = webhook_secret
        self._ttl = ttl_seconds
        self._requests: dict[str, _Challenge] = {}
        self._active_by_owner: dict[tuple[str, str], str] = {}

    @staticmethod
    def _now(now: int | None) -> int:
        return int(time.time()) if now is None else int(now)

    @staticmethod
    def _validate_binding(binding: TelegramBinding) -> None:
        if not _ID.fullmatch(binding.tenant_id) or not _ID.fullmatch(binding.user_id):
            raise LoginError("invalid_binding")
        if (binding.telegram_user_id <= 0 or binding.private_chat_id <= 0
                or binding.private_chat_id != binding.telegram_user_id):
            raise LoginError("invalid_binding")

    @staticmethod
    def _hash_browser_secret(secret: str) -> bytes:
        return hashlib.sha256(secret.encode("utf-8")).digest()

    def start(self, binding: TelegramBinding, *, now: int | None = None) -> tuple[BrowserChallenge, BotNotification]:
        """Only the trusted gateway calls this after finding a verified binding.

        No Telegram message is sent here; caller must send BotNotification and
        cancel on delivery failure. Never expose BotNotification to the browser.
        """
        self._validate_binding(binding)
        timestamp = self._now(now)
        owner = (binding.tenant_id, binding.user_id)
        previous = self._active_by_owner.get(owner)
        if previous in self._requests:
            self._requests[previous].state = "denied"
        request_id = secrets.token_urlsafe(18)
        browser_secret = secrets.token_urlsafe(32)
        comparison_code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = timestamp + self._ttl
        self._requests[request_id] = _Challenge(
            binding=binding,
            browser_secret_digest=self._hash_browser_secret(browser_secret),
            expires_at=expires_at,
        )
        self._active_by_owner[owner] = request_id
        browser = BrowserChallenge(request_id, browser_secret, comparison_code, expires_at)
        notification = BotNotification(
            chat_id=binding.private_chat_id,
            message=(
                "Lia Fibra - richiesta di accesso.\n"
                f"Codice sullo schermo: {comparison_code}\n"
                "Conferma solo se hai avviato TU l'accesso e il codice coincide. "
                "Valido per 2 minuti. Se non sei tu, premi Rifiuta."
            ),
            approve_callback=f"login:approve:{request_id}",
            deny_callback=f"login:deny:{request_id}",
        )
        return browser, notification

    def cancel_failed_delivery(self, request_id: str) -> None:
        """Only trusted dispatch code should call this if Bot API send fails."""
        challenge = self._requests.get(request_id)
        if challenge and challenge.state == "pending":
            challenge.state = "denied"

    def _get_live(self, request_id: str, now: int) -> _Challenge:
        challenge = self._requests.get(request_id)
        if challenge is None:
            raise LoginError("invalid_request")
        if now >= challenge.expires_at and challenge.state in ("pending", "approved"):
            challenge.state = "expired"
        return challenge

    def callback_from_verified_webhook(
        self, callback_data: str, *, header_secret: str,
        telegram_user_id: int, chat_id: int, chat_type: str,
        now: int | None = None,
    ) -> str:
        """Use only from HTTPS webhook handler. Verify secret, sender and chat.

        In production authenticate Telegram delivery at the external gateway too;
        do not accept webhook fields provided by browser, GPT, or MCP tool args.
        """
        if not hmac.compare_digest(self._webhook_secret, header_secret):
            raise LoginError("untrusted_webhook")
        if chat_type != "private" or telegram_user_id <= 0 or chat_id != telegram_user_id:
            raise LoginError("invalid_chat")
        parsed = _CALLBACK.fullmatch(callback_data)
        if parsed is None:
            raise LoginError("invalid_callback")
        action, request_id = parsed.groups()
        challenge = self._get_live(request_id, self._now(now))
        if (challenge.binding.telegram_user_id != telegram_user_id
                or challenge.binding.private_chat_id != chat_id):
            raise LoginError("identity_mismatch")
        if challenge.state != "pending":
            raise LoginError("already_handled")
        challenge.state = "approved" if action == "approve" else "denied"
        return challenge.state

    def _check_browser(self, request_id: str, browser_secret: str, timestamp: int) -> _Challenge:
        challenge = self._get_live(request_id, timestamp)
        if challenge.failures >= 3:
            raise LoginError("invalid_browser_proof")
        if not hmac.compare_digest(
            challenge.browser_secret_digest,
            self._hash_browser_secret(browser_secret),
        ):
            challenge.failures += 1
            raise LoginError("invalid_browser_proof")
        return challenge

    def browser_status(self, request_id: str, browser_secret: str, *, now: int | None = None) -> str:
        """Browser polls using the secret tied to its original login request."""
        challenge = self._check_browser(request_id, browser_secret, self._now(now))
        return challenge.state

    def redeem(self, request_id: str, browser_secret: str, *, now: int | None = None) -> LoginGrant:
        """No JWT generated: a separate backend must issue a scoped session."""
        timestamp = self._now(now)
        challenge = self._check_browser(request_id, browser_secret, timestamp)
        if challenge.state != "approved":
            raise LoginError("not_approved")
        challenge.state = "consumed"
        binding = challenge.binding
        return LoginGrant(binding.tenant_id, binding.user_id, binding.telegram_user_id, timestamp)
