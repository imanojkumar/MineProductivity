"""Tests for mineproductivity.decision.root_cause.

Design spec §18/§34's "interface-purity proof": RootCauseAnalyzer has
zero concrete, non-test subclasses anywhere in
``src/mineproductivity/decision/``, and its own abstract method body is
a docstring only (no accidental orchestration/business logic)."""

from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path

import pytest

from mineproductivity.decision.abstractions import DecisionModel
from mineproductivity.decision.root_cause import RootCauseAnalyzer


class TestRootCauseAnalyzerIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            RootCauseAnalyzer()  # type: ignore[abstract]

    def test_is_a_decision_model(self) -> None:
        assert issubclass(RootCauseAnalyzer, DecisionModel)

    def test_both_decide_and_analyze_remain_abstract(self) -> None:
        """Leaves _decide (inherited from DecisionModel) unoverridden,
        exactly like DecisionStrategy/RankingStrategy -- only a future
        concrete subclass decides how _decide relates to _analyze."""
        assert RootCauseAnalyzer.__abstractmethods__ == frozenset({"_decide", "_analyze"})


class TestRootCauseAnalyzerInterfacePurity:
    def test_zero_concrete_subclasses_exist_in_the_decision_package(self) -> None:
        """Design spec §18: 'THIS MODULE SHIPS NO CONCRETE SUBCLASS.'
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
                    if "RootCauseAnalyzer" in base_names:
                        subclass_names.append(f"{py_file.name}:{node.name}")
        assert subclass_names == [], f"Found concrete subclasses: {subclass_names}"

    def test_analyze_method_body_is_a_docstring_only(self) -> None:
        """No accidental helper methods or business logic exists beyond
        the abstract contract's own docstring."""
        source = inspect.getsource(RootCauseAnalyzer._analyze)
        (function_def,) = ast.parse(textwrap.dedent(source)).body
        assert isinstance(function_def, ast.FunctionDef)
        assert len(function_def.body) == 1
        assert isinstance(function_def.body[0], ast.Expr)
        assert isinstance(function_def.body[0].value, ast.Constant)
        assert isinstance(function_def.body[0].value.value, str)

    def test_no_additional_public_methods_beyond_the_inherited_and_own_contract(self) -> None:
        """Public API matches the specification exactly: only _analyze
        is added beyond what DecisionModel already defines."""
        own_members = {
            name
            for name, value in vars(RootCauseAnalyzer).items()
            if not name.startswith("__") and callable(value)
        }
        assert own_members == {"_analyze"}
