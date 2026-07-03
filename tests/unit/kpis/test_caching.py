"""Tests for mineproductivity.kpis.caching."""

from __future__ import annotations

import threading

from mineproductivity.kpis.caching import ResultCache
from mineproductivity.kpis.result import KPIResult


class TestGetOrCompute:
    def test_first_call_invokes_compute(self) -> None:
        cache = ResultCache()
        calls = {"n": 0}

        def compute() -> KPIResult:
            calls["n"] += 1
            return KPIResult(code="X", value=1.0, unit="u")

        result = cache.get_or_compute("X", "shift", {"shift": "A"}, 5, compute)
        assert result.value == 1.0
        assert calls["n"] == 1

    def test_second_call_with_the_same_key_is_a_cache_hit(self) -> None:
        cache = ResultCache()
        calls = {"n": 0}

        def compute() -> KPIResult:
            calls["n"] += 1
            return KPIResult(code="X", value=1.0, unit="u")

        cache.get_or_compute("X", "shift", {"shift": "A"}, 5, compute)
        cache.get_or_compute("X", "shift", {"shift": "A"}, 5, compute)
        assert calls["n"] == 1

    def test_different_fingerprint_is_a_cache_miss(self) -> None:
        cache = ResultCache()
        calls = {"n": 0}

        def compute() -> KPIResult:
            calls["n"] += 1
            return KPIResult(code="X", value=1.0, unit="u")

        cache.get_or_compute("X", "shift", {"shift": "A"}, 5, compute)
        cache.get_or_compute("X", "shift", {"shift": "A"}, 6, compute)
        assert calls["n"] == 2

    def test_different_scope_is_a_cache_miss(self) -> None:
        cache = ResultCache()
        calls = {"n": 0}

        def compute() -> KPIResult:
            calls["n"] += 1
            return KPIResult(code="X", value=1.0, unit="u")

        cache.get_or_compute("X", "shift", {"shift": "A"}, 5, compute)
        cache.get_or_compute("X", "shift", {"shift": "B"}, 5, compute)
        assert calls["n"] == 2

    def test_scope_key_order_does_not_matter(self) -> None:
        cache = ResultCache()
        calls = {"n": 0}

        def compute() -> KPIResult:
            calls["n"] += 1
            return KPIResult(code="X", value=1.0, unit="u")

        cache.get_or_compute("X", "shift", {"a": "1", "b": "2"}, 5, compute)
        cache.get_or_compute("X", "shift", {"b": "2", "a": "1"}, 5, compute)
        assert calls["n"] == 1

    def test_different_code_is_a_cache_miss(self) -> None:
        cache = ResultCache()
        calls = {"n": 0}

        def compute() -> KPIResult:
            calls["n"] += 1
            return KPIResult(code="X", value=1.0, unit="u")

        cache.get_or_compute("X", "shift", {}, 5, compute)
        cache.get_or_compute("Y", "shift", {}, 5, compute)
        assert calls["n"] == 2


class TestInvalidate:
    def test_invalidate_by_code_drops_only_that_codes_entries(self) -> None:
        cache = ResultCache()
        cache.get_or_compute("X", "shift", {}, 1, lambda: KPIResult(code="X", value=1.0, unit="u"))
        cache.get_or_compute("Y", "shift", {}, 1, lambda: KPIResult(code="Y", value=2.0, unit="u"))
        cache.invalidate("X")
        assert len(cache) == 1

    def test_invalidate_with_no_code_clears_everything(self) -> None:
        cache = ResultCache()
        cache.get_or_compute("X", "shift", {}, 1, lambda: KPIResult(code="X", value=1.0, unit="u"))
        cache.get_or_compute("Y", "shift", {}, 1, lambda: KPIResult(code="Y", value=2.0, unit="u"))
        cache.invalidate()
        assert len(cache) == 0


class TestLen:
    def test_len_reflects_the_number_of_distinct_cached_keys(self) -> None:
        cache = ResultCache()
        assert len(cache) == 0
        cache.get_or_compute("X", "shift", {}, 1, lambda: KPIResult(code="X", value=1.0, unit="u"))
        assert len(cache) == 1


class TestThreadSafety:
    def test_concurrent_get_or_compute_for_the_same_key_computes_exactly_once(self) -> None:
        cache = ResultCache()
        calls = {"n": 0}
        call_lock = threading.Lock()

        def compute() -> KPIResult:
            with call_lock:
                calls["n"] += 1
            return KPIResult(code="X", value=1.0, unit="u")

        threads = [
            threading.Thread(
                target=cache.get_or_compute, args=("X", "shift", {"shift": "A"}, 1, compute)
            )
            for _ in range(32)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert calls["n"] == 1

    def test_independent_concurrent_keys_do_not_interfere(self) -> None:
        cache = ResultCache()
        results: dict[str, KPIResult] = {}
        results_lock = threading.Lock()

        def run(code: str, value: float) -> None:
            result = cache.get_or_compute(
                code, "shift", {}, 1, lambda: KPIResult(code=code, value=value, unit="u")
            )
            with results_lock:
                results[code] = result

        threads = [threading.Thread(target=run, args=(f"CODE-{i}", float(i))) for i in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 16
        assert all(results[f"CODE-{i}"].value == float(i) for i in range(16))
