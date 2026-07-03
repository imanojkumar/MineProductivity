"""Tests for mineproductivity.kpis.backends (the process-level active
backend singleton)."""

from __future__ import annotations

from mineproductivity.kpis.backends import (
    NumPyBackend,
    PandasBackend,
    get_active_backend,
    set_active_backend,
)


class TestActiveBackendSingleton:
    def teardown_method(self) -> None:
        set_active_backend(PandasBackend())

    def test_default_active_backend_is_pandas(self) -> None:
        assert isinstance(get_active_backend(), PandasBackend)

    def test_set_active_backend_changes_the_process_level_default(self) -> None:
        set_active_backend(NumPyBackend())
        assert isinstance(get_active_backend(), NumPyBackend)

    def test_get_active_backend_returns_the_same_instance_across_calls(self) -> None:
        backend = NumPyBackend()
        set_active_backend(backend)
        assert get_active_backend() is backend
