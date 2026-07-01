"""Result[T] and Maybe[T]: exception-free error handling and explicit
optionality, with chainable combinators.

Run: python examples/core/06_result_and_maybe.py
"""

from __future__ import annotations

from mineproductivity.core import Maybe, Result


def parse_percentage(raw: str) -> Result[float]:
    try:
        value = float(raw)
    except ValueError:
        return Result.err(f"{raw!r} is not a number")
    if not (0 <= value <= 100):
        return Result.err(f"{value} is out of range [0, 100]")
    return Result.ok(value)


def find_first_over(values: list[float], threshold: float) -> Maybe[float]:
    for value in values:
        if value > threshold:
            return Maybe.some(value)
    return Maybe.nothing()


def main() -> None:
    print("--- Result[T]: success/failure without exceptions ---")
    for raw in ["42.5", "not-a-number", "150"]:
        result = parse_percentage(raw)
        if result.is_ok:
            print(f"parse_percentage({raw!r}) -> ok({result.unwrap()})")
        else:
            print(f"parse_percentage({raw!r}) -> err({result.error})")

    chained = (
        parse_percentage("80")
        .map(lambda pct: pct / 100)
        .and_then(lambda ratio: Result.ok(ratio * 1000))
    )
    print(f"chained map/and_then -> {chained.unwrap_or(-1.0)}")

    print()
    print("--- Maybe[T]: explicit optionality without None ambiguity ---")
    readings = [12.0, 45.5, 88.2, 30.0]
    found = find_first_over(readings, 50)
    print(f"find_first_over(readings, 50) -> {found}")
    print(f"unwrap_or(default) -> {found.unwrap_or(-1.0)}")

    none_found = find_first_over(readings, 1000)
    print(f"find_first_over(readings, 1000) -> {none_found}")

    as_result = none_found.to_result("no reading exceeded threshold")
    print(f"Maybe.to_result(...) -> is_err: {as_result.is_err}, error: {as_result.error}")


if __name__ == "__main__":
    main()
