"""Tests for mineproductivity.connectors.oem -- all five vendor shapes
are structurally identical (documentation-only, non-functional), so
they are covered together via parametrization rather than five
near-duplicate test files.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import mineproductivity.connectors.oem as oem
from mineproductivity.connectors._registry import CONNECTORS
from mineproductivity.connectors.auth import _StaticAuthProvider
from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.normalization import ReasonCodeMap

_SINCE = datetime(2026, 6, 25, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, tzinfo=timezone.utc)

# Every OEM shape shares the identical (host, auth) constructor signature
# (design spec §10.7), but FMSConnector itself declares no __init__, so
# mypy cannot see host/auth as valid kwargs through this type[FMSConnector]
# list -- narrow ignores mark the two call sites that rely on the shared
# shape rather than the FMSConnector contract itself.
_VENDOR_CLASSES: list[type[FMSConnector]] = [
    oem.MineStarConnector,
    oem.DispatchConnector,
    oem.WencoConnector,
    oem.ModularConnector,
    oem.HexagonConnector,
]

_REASON_CODE_MAPS = [
    oem.MINESTAR_REASON_CODE_MAP,
    oem.DISPATCH_REASON_CODE_MAP,
    oem.WENCO_REASON_CODE_MAP,
    oem.MODULAR_REASON_CODE_MAP,
    oem.HEXAGON_REASON_CODE_MAP,
]


@pytest.fixture
def auth_provider() -> _StaticAuthProvider:
    return _StaticAuthProvider(base_token="tok")


class TestOemConnectorShapes:
    @pytest.mark.parametrize("connector_cls", _VENDOR_CLASSES)
    def test_is_an_fms_connector_subclass(self, connector_cls: type[FMSConnector]) -> None:
        assert issubclass(connector_cls, FMSConnector)

    @pytest.mark.parametrize("connector_cls", _VENDOR_CLASSES)
    def test_constructs_with_host_and_auth(
        self, connector_cls: type[FMSConnector], auth_provider: _StaticAuthProvider
    ) -> None:
        instance = connector_cls(host="vendor.example.com", auth=auth_provider)  # type: ignore[call-arg]
        assert instance is not None

    @pytest.mark.parametrize("connector_cls", _VENDOR_CLASSES)
    def test_get_cycle_data_raises_not_implemented(
        self, connector_cls: type[FMSConnector], auth_provider: _StaticAuthProvider
    ) -> None:
        instance = connector_cls(host="vendor.example.com", auth=auth_provider)  # type: ignore[call-arg]
        with pytest.raises(NotImplementedError, match="documentation-only shape"):
            list(instance.get_cycle_data(_SINCE, _UNTIL))

    @pytest.mark.parametrize("connector_cls", _VENDOR_CLASSES)
    def test_get_delay_data_raises_not_implemented(
        self, connector_cls: type[FMSConnector], auth_provider: _StaticAuthProvider
    ) -> None:
        instance = connector_cls(host="vendor.example.com", auth=auth_provider)  # type: ignore[call-arg]
        with pytest.raises(NotImplementedError, match="documentation-only shape"):
            list(instance.get_delay_data(_SINCE, _UNTIL))

    @pytest.mark.parametrize("connector_cls", _VENDOR_CLASSES)
    def test_not_auto_registered(self, connector_cls: type[FMSConnector]) -> None:
        assert connector_cls.name not in CONNECTORS

    @pytest.mark.parametrize("connector_cls", _VENDOR_CLASSES)
    def test_supports_batch_and_incremental_modes(self, connector_cls: type[FMSConnector]) -> None:
        assert connector_cls.supported_modes == (IngestionMode.BATCH, IngestionMode.INCREMENTAL)

    @pytest.mark.parametrize("connector_cls", _VENDOR_CLASSES)
    def test_vendor_name_matches_registry_name(self, connector_cls: type[FMSConnector]) -> None:
        assert connector_cls.vendor_name == connector_cls.name  # type: ignore[attr-defined]

    def test_every_vendor_has_a_distinct_name(self) -> None:
        names = {cls.name for cls in _VENDOR_CLASSES}
        assert len(names) == len(_VENDOR_CLASSES)


class TestOemReasonCodeMaps:
    @pytest.mark.parametrize("reason_map", _REASON_CODE_MAPS)
    def test_is_a_reason_code_map(self, reason_map: ReasonCodeMap) -> None:
        assert isinstance(reason_map, ReasonCodeMap)

    @pytest.mark.parametrize("reason_map", _REASON_CODE_MAPS)
    def test_has_at_least_one_mapping_entry(self, reason_map: ReasonCodeMap) -> None:
        assert len(reason_map.mapping) > 0

    @pytest.mark.parametrize("reason_map", _REASON_CODE_MAPS)
    def test_every_entry_resolves(self, reason_map: ReasonCodeMap) -> None:
        for code in reason_map.mapping:
            assert reason_map.resolve(code).is_some

    def test_every_vendor_has_a_distinct_reason_map_vendor_name(self) -> None:
        vendor_names = {rmap.vendor_name for rmap in _REASON_CODE_MAPS}
        assert len(vendor_names) == len(_REASON_CODE_MAPS)
