"""Tests for mineproductivity.core.service."""

from __future__ import annotations

from mineproductivity.core.service import BaseService


class TransferService(BaseService):
    def transfer(self, amount: int) -> int:
        return amount


class TestBaseService:
    def test_is_instantiable_without_abstract_methods(self) -> None:
        # BaseService declares no abstract methods, so it can be
        # instantiated directly (unlike the ABCs with abstract methods).
        BaseService()

    def test_subclass_exposes_use_case_specific_api(self) -> None:
        assert TransferService().transfer(5) == 5

    def test_subclass_is_instance_of_base(self) -> None:
        assert isinstance(TransferService(), BaseService)
