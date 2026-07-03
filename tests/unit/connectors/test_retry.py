"""Tests for mineproductivity.connectors.retry."""

from __future__ import annotations

import pytest

from mineproductivity.core import ValidationError
from mineproductivity.connectors.exceptions import SourceUnavailableError
from mineproductivity.connectors.retry import BackoffStrategy, RetryPolicy, run_with_retry


class TestBackoffStrategy:
    def test_has_three_strategies(self) -> None:
        assert len(list(BackoffStrategy)) == 3

    def test_values(self) -> None:
        assert BackoffStrategy.FIXED.value == "fixed"
        assert BackoffStrategy.EXPONENTIAL.value == "exponential"
        assert BackoffStrategy.EXPONENTIAL_JITTER.value == "exponential_jitter"


class TestRetryPolicyConstruction:
    def test_defaults(self) -> None:
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.backoff is BackoffStrategy.EXPONENTIAL_JITTER
        assert policy.base_delay_s == 1.0
        assert policy.retryable_exceptions == (SourceUnavailableError,)

    def test_max_attempts_below_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RetryPolicy(max_attempts=0)

    def test_negative_base_delay_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RetryPolicy(base_delay_s=-1.0)

    def test_from_mapping(self) -> None:
        policy = RetryPolicy.from_mapping({"max_attempts": 5})
        assert policy.max_attempts == 5


class TestComputeDelay:
    def test_fixed_backoff_is_constant(self) -> None:
        policy = RetryPolicy(backoff=BackoffStrategy.FIXED, base_delay_s=2.0)
        assert policy.compute_delay(1) == 2.0
        assert policy.compute_delay(5) == 2.0

    def test_exponential_backoff_doubles(self) -> None:
        policy = RetryPolicy(backoff=BackoffStrategy.EXPONENTIAL, base_delay_s=1.0)
        assert policy.compute_delay(1) == 1.0
        assert policy.compute_delay(2) == 2.0
        assert policy.compute_delay(3) == 4.0

    def test_exponential_jitter_applies_jitter_factor(self) -> None:
        policy = RetryPolicy(backoff=BackoffStrategy.EXPONENTIAL_JITTER, base_delay_s=1.0)
        assert policy.compute_delay(1, jitter_fn=lambda: 0.5) == 1.0
        assert policy.compute_delay(1, jitter_fn=lambda: 0.0) == 0.5
        assert policy.compute_delay(2, jitter_fn=lambda: 0.5) == 2.0

    def test_attempt_below_one_rejected(self) -> None:
        policy = RetryPolicy()
        with pytest.raises(ValueError, match="attempt must be >= 1"):
            policy.compute_delay(0)


class TestIsRetryable:
    def test_default_retryable_exception(self) -> None:
        policy = RetryPolicy()
        assert policy.is_retryable(SourceUnavailableError("boom"))

    def test_non_retryable_exception(self) -> None:
        policy = RetryPolicy()
        assert not policy.is_retryable(ValueError("boom"))

    def test_custom_retryable_exceptions(self) -> None:
        policy = RetryPolicy(retryable_exceptions=(ValueError,))
        assert policy.is_retryable(ValueError("boom"))
        assert not policy.is_retryable(SourceUnavailableError("boom"))


class TestRunWithRetry:
    def test_succeeds_on_first_attempt_without_sleeping(self) -> None:
        sleeps: list[float] = []
        result = run_with_retry(lambda: "ok", RetryPolicy(), sleep_fn=sleeps.append)
        assert result == "ok"
        assert sleeps == []

    def test_retries_until_success(self) -> None:
        attempts = {"n": 0}

        def flaky() -> str:
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise SourceUnavailableError("transient")
            return "ok"

        sleeps: list[float] = []
        result = run_with_retry(
            flaky,
            RetryPolicy(max_attempts=5, base_delay_s=1.0),
            sleep_fn=sleeps.append,
            jitter_fn=lambda: 0.5,
        )
        assert result == "ok"
        assert attempts["n"] == 3
        assert len(sleeps) == 2

    def test_raises_after_exhausting_max_attempts(self) -> None:
        def always_fails() -> None:
            raise SourceUnavailableError("permanent")

        with pytest.raises(SourceUnavailableError):
            run_with_retry(
                always_fails,
                RetryPolicy(max_attempts=2, base_delay_s=0.0),
                sleep_fn=lambda _s: None,
            )

    def test_non_retryable_exception_raises_immediately(self) -> None:
        calls = {"n": 0}

        def raises_value_error() -> None:
            calls["n"] += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            run_with_retry(
                raises_value_error, RetryPolicy(max_attempts=5), sleep_fn=lambda _s: None
            )
        assert calls["n"] == 1

    def test_sleep_fn_receives_computed_delay(self) -> None:
        attempts = {"n": 0}

        def flaky() -> str:
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise SourceUnavailableError("transient")
            return "ok"

        sleeps: list[float] = []
        run_with_retry(
            flaky,
            RetryPolicy(max_attempts=3, base_delay_s=1.0, backoff=BackoffStrategy.FIXED),
            sleep_fn=sleeps.append,
        )
        assert sleeps == [1.0]
