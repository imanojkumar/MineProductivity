"""Tests for mineproductivity.decision.what_if.

Design spec §19/§34's "interface-purity proof": WhatIfEngine has zero
concrete, non-test subclasses anywhere in ``src/mineproductivity/decision/``,
and its own abstract method body is a docstring only (no accidental
orchestration/business logic)."""

from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path

import pytest

from mineproductivity.decision.abstractions import DecisionModel
from mineproductivity.decision.what_if import WhatIfEngine


class TestWhatIfEngineIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            WhatIfEngine()  # type: ignore[abstract]

    def test_is_a_decision_model(self) -> None:
        assert issubclass(WhatIfEngine, DecisionModel)

    def test_both_decide_and_simulate_remain_abstract(self) -> None:
        """Leaves _decide (inherited from DecisionModel) unoverridden,
        exactly like DecisionStrategy/RankingStrategy/RootCauseAnalyzer
        -- only a future concrete subclass decides how _decide relates
        to _simulate."""
        assert WhatIfEngine.__abstractmethods__ == frozenset({"_decide", "_simulate"})


class TestWhatIfEngineInterfacePurity:
    def test_zero_concrete_subclasses_exist_in_the_decision_package(self) -> None:
        """Design spec §19: 'THIS MODULE SHIPS NO CONCRETE SUBCLASS.'
        Mechanically verified via AST across every source file in
        src/mineproductivity/decision/, not merely asserted in prose."""
        import mineproductivity.decision as decision_package

        decision_dir = Path(decision_package.__file__).parent
        subclass_names: list[str] = []
        for py_file in decision_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    base_names = [base.id for base in node.bases if isinstance(base, ast.Name)]
                    if "WhatIfEngine" in base_names:
                        subclass_names.append(f"{py_file.name}:{node.name}")
        assert subclass_names == [], f"Found concrete subclasses: {subclass_names}"

    def test_simulate_method_body_is_a_docstring_only(self) -> None:
        """No accidental helper methods or business logic exists beyond
        the abstract contract's own docstring."""
        source = inspect.getsource(WhatIfEngine._simulate)
        (function_def,) = ast.parse(textwrap.dedent(source)).body
        assert isinstance(function_def, ast.FunctionDef)
        assert len(function_def.body) == 1
        assert isinstance(function_def.body[0], ast.Expr)
        assert isinstance(function_def.body[0].value, ast.Constant)
        assert isinstance(function_def.body[0].value.value, str)

    def test_no_additional_public_methods_beyond_the_inherited_and_own_contract(self) -> None:
        """Public API matches the specification exactly: only _simulate
        is added beyond what DecisionModel already defines."""
        own_members = {
            name
            for name, value in vars(WhatIfEngine).items()
            if not name.startswith("__") and callable(value)
        }
        assert own_members == {"_simulate"}
