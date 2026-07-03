"""Tests for mineproductivity.connectors.auth."""

from __future__ import annotations

import dataclasses
import threading
from datetime import datetime, timezone

import pytest

from mineproductivity.core import ValidationError
from mineproductivity.connectors.auth import AuthProvider, Credentials, _StaticAuthProvider


class TestCredentials:
    def test_valid_construction(self) -> None:
        creds = Credentials(token="abc123")
        assert creds.token == "abc123"
        assert creds.expires_at_utc is None

    def test_with_expiry(self) -> None:
        expires = datetime(2026, 6, 25, 12, tzinfo=timezone.utc)
        creds = Credentials(token="abc123", expires_at_utc=expires)
        assert creds.expires_at_utc == expires

    def test_empty_token_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Credentials(token="")

    def test_is_frozen(self) -> None:
        creds = Credentials(token="abc123")
        with pytest.raises(dataclasses.FrozenInstanceError):
            creds.token = "other"  # type: ignore[misc]


class TestAuthProviderAbstractContract:
    def test_cannot_instantiate_abstract_base(self) -> None:
        with pytest.raises(TypeError):
            AuthProvider()  # type: ignore[abstract]


class TestStaticAuthProvider:
    def test_credentials_returns_base_token_with_generation(self) -> None:
        provider = _StaticAuthProvider(base_token="tok")
        creds = provider.credentials()
        assert creds.token == "tok-gen0"

    def test_refresh_increments_generation(self) -> None:
        provider = _StaticAuthProvider(base_token="tok")
        first = provider.refresh()
        assert first.is_ok
        assert first.value.token == "tok-gen1"
        second = provider.refresh()
        assert second.value.token == "tok-gen2"

    def test_credentials_reflects_latest_refresh(self) -> None:
        provider = _StaticAuthProvider(base_token="tok")
        provider.refresh()
        assert provider.credentials().token == "tok-gen1"

    def test_concurrent_refresh_never_produces_duplicate_tokens(self) -> None:
        provider = _StaticAuthProvider(base_token="tok")
        results: list[str] = []

        def worker() -> None:
            results.append(provider.refresh().unwrap().token)

        threads = [threading.Thread(target=worker) for _ in range(32)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 32
        assert len(set(results)) == 32
