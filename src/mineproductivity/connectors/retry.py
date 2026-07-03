"""``BackoffStrategy``/``RetryPolicy``: shared, generic retry/backoff
configuration and execution used by every network connector -- one
implementation to test and trust, rather than one per vendor (design
spec AD-CN-05).
"""

from __future__ import annotations

import dataclasses
import logging
import random
import time
from collections.abc import Callable
from enum import Enum
from typing import TypeVar

from mineproductivity.core import BaseConfiguration, ValidationError

from mineproductivity.connectors.exceptions import SourceUnavailableError

__all__ = ["BackoffStrategy", "RetryPolicy", "run_with_retry"]

_logger = logging.getLogger(__name__)

T = TypeVar("T")


class BackoffStrategy(Enum):
    """The three backoff shapes a :class:`RetryPolicy` can compute."""

    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"


@dataclasses.dataclass(frozen=True, slots=True)
class RetryPolicy(BaseConfiguration):
    """Retry/backoff configuration for a network-connected
    :class:`~mineproductivity.connectors.base.FMSConnector`."""

    max_attempts: int = dataclasses.field(default=3, kw_only=True)
    backoff: BackoffStrategy = dataclasses.field(
        default=BackoffStrategy.EXPONENTIAL_JITTER, kw_only=True
    )
    base_delay_s: float = dataclasses.field(default=1.0, kw_only=True)
    retryable_exceptions: tuple[type[Exception], ...] = dataclasses.field(
        default=(SourceUnavailableError,), kw_only=True
    )

    def validate(self) -> None:
        if self.max_attempts < 1:
            raise ValidationError("RetryPolicy.max_attempts must be >= 1")
        if self.base_delay_s < 0:
            raise ValidationError("RetryPolicy.base_delay_s must be >= 0")

    def compute_delay(
        self, attempt: int, *, jitter_fn: Callable[[], float] = random.random
    ) -> float:
        """The backoff delay (seconds) before retry number ``attempt``
        (1-indexed: the delay before the *second* overall attempt is
        ``compute_delay(1)``)."""
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        if self.backoff is BackoffStrategy.FIXED:
            return self.base_delay_s
        delay = self.base_delay_s * float(2 ** (attempt - 1))
        if self.backoff is BackoffStrategy.EXPONENTIAL_JITTER:
            delay *= 0.5 + jitter_fn()
        return delay

    def is_retryable(self, exc: Exception) -> bool:
        """Whether ``exc`` is one of :attr:`retryable_exceptions`."""
        return isinstance(exc, self.retryable_exceptions)


def run_with_retry(
    fn: Callable[[], T],
    policy: RetryPolicy,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
    jitter_fn: Callable[[], float] = random.random,
) -> T:
    """Call ``fn()``, retrying per ``policy`` on a retryable exception.

    ``sleep_fn`` is injectable so tests can assert timing behavior
    deterministically without real sleeping (design spec §29's "no real
    sleeping in unit tests" rule).

    Raises
    ------
    Exception
        The last raised exception, once ``policy.max_attempts`` is
        exhausted, or immediately if the raised exception is not
        retryable per ``policy.is_retryable``.
    """
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if not policy.is_retryable(exc):
                raise
            if attempt == policy.max_attempts:
                _logger.error("retry exhausted after %d attempt(s): %s", attempt, exc)
                raise
            delay = policy.compute_delay(attempt, jitter_fn=jitter_fn)
            _logger.info("retry attempt %d failed, retrying in %.2fs: %s", attempt, delay, exc)
            sleep_fn(delay)
    raise AssertionError("unreachable: loop always returns or raises")  # pragma: no cover
