"""Tests for mineproductivity.agents.conversation (design spec §15)."""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.agents.conversation import ConversationContext, ConversationTurn
from mineproductivity.core.serialization import to_dict

_WHEN = datetime(2026, 7, 1, 6, 0, tzinfo=timezone.utc)


def _turn(speaker: str = "human", content: str = "Proceed.") -> ConversationTurn:
    return ConversationTurn(speaker=speaker, content=content, occurred_at=_WHEN)


class TestConversationTurn:
    def test_speaker_is_an_open_string(self) -> None:
        """Design spec §15: an Agent code, 'human', or a Tool code --
        never a closed enum."""
        for speaker in ("human", "FLEET.ReassignmentAdvisor", "TOOL.DispatchQuery"):
            assert _turn(speaker=speaker).speaker == speaker

    def test_value_equality(self) -> None:
        assert _turn() == _turn()


class TestConversationContext:
    def test_turns_default_empty(self) -> None:
        assert ConversationContext(task_id="TASK-1").turns == ()

    def test_a_new_turn_produces_a_new_instance(self) -> None:
        """Design spec §15: append-only in spirit -- never mutates
        turns in place."""
        original = ConversationContext(task_id="TASK-1")
        extended = original.replace(turns=original.turns + (_turn(),))
        assert original.turns == ()
        assert len(extended.turns) == 1
        assert extended is not original

    def test_serializes_via_core_serialization(self) -> None:
        context = ConversationContext(task_id="TASK-1", turns=(_turn(),))
        serialized = to_dict(context)
        assert serialized["task_id"] == "TASK-1"
        assert serialized["turns"][0]["speaker"] == "human"
