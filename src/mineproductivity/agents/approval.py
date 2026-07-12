"""``ApprovalRequest``/``ApprovalStatus``: the human-in-the-loop gate
(design spec §16).

Reuse audit: ``core.BaseValueObject`` reused verbatim. Genuinely new
to this series: no package below ``agents`` pauses mid-execution for a
human decision. An ``ApprovalRequest`` resolving to ``APPROVED``
transitions its ``Task`` from ``AWAITING_APPROVAL`` back to
``RUNNING``; a resolution to ``REJECTED`` transitions it directly to
``FAILED``, carrying the rejection as a warning on the eventual
``AgentResult`` (§16, §11). ``TaskExecutor`` never resolves an
``ApprovalRequest`` itself -- resolution is exclusively a caller
(human-supervisor-facing) action.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from enum import Enum

from mineproductivity.core import BaseValueObject

__all__ = ["ApprovalRequest", "ApprovalStatus"]


class ApprovalStatus(Enum):
    """The three-state approval lifecycle a ``Task`` pauses on when
    ``PolicyEngine`` (design spec §10) requires it -- closed; a new
    approval *policy* (who must approve what) is an ``AgentPolicy``
    concern, not a change here."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclasses.dataclass(frozen=True, slots=True)
class ApprovalRequest(BaseValueObject):
    """One pending, approved, or rejected request for a human to
    authorize a ``Task`` before ``TaskExecutor`` (design spec §12)
    resumes it.

    Examples
    --------
    >>> request = ApprovalRequest(task_id="TASK-1", requested_action="approve_shutdown")
    >>> request.status
    <ApprovalStatus.PENDING: 'pending'>
    >>> request.approver is None
    True
    """

    task_id: str
    requested_action: str
    status: ApprovalStatus = dataclasses.field(default=ApprovalStatus.PENDING, kw_only=True)
    approver: str | None = dataclasses.field(default=None, kw_only=True)
    resolved_at: datetime | None = dataclasses.field(default=None, kw_only=True)
