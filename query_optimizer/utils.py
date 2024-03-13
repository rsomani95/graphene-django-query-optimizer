from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING

from django.db import models

from .errors import OptimizerError
from .settings import optimizer_settings

if TYPE_CHECKING:
    from .typing import Optional, ParamSpec, TypeVar

    T = TypeVar("T")
    P = ParamSpec("P")


__all__ = [
    "add_slice_to_queryset",
    "calculate_slice_for_queryset",
    "check_for_optimizer_errors",
    "is_optimized",
    "mark_optimized",
    "mark_unoptimized",
    "optimizer_logger",
    "SubqueryCount",
]


optimizer_logger = logging.getLogger("query_optimizer")


def mark_optimized(queryset: models.QuerySet) -> None:
    """Mark queryset as optimized so that later optimizers know to skip optimization"""
    queryset._hints[optimizer_settings.OPTIMIZER_MARK] = True  # type: ignore[attr-defined]


def mark_unoptimized(queryset: models.QuerySet) -> None:  # pragma: no cover
    """Mark queryset as unoptimized so that later optimizers will run optimization"""
    queryset._hints.pop(optimizer_settings.OPTIMIZER_MARK, None)  # type: ignore[attr-defined]


def is_optimized(queryset: models.QuerySet) -> bool:
    """Has the queryset been optimized?"""
    return queryset._hints.get(optimizer_settings.OPTIMIZER_MARK, False)  # type: ignore[no-any-return, attr-defined]


def calculate_queryset_slice(
    *,
    after: Optional[int],
    before: Optional[int],
    first: Optional[int],
    last: Optional[int],
    size: int,
) -> slice:
    """
    Calculate queryset slicing based on the provided arguments.
    Before this, the arguments should be validated so that:
     - `first` and `last`, positive integers or `None`
     - `after` and `before` are non-negative integers or `None`
     - If both `after` and `before` are given, `after` is less than or equal to `before`

    This function is based on the Relay pagination algorithm.
    See. https://relay.dev/graphql/connections.htm#sec-Pagination-algorithm

    :param after: The index after which to start (exclusive).
    :param before: The index before which to stop (exclusive).
    :param first: The number of items to return from the start.
    :param last: The number of items to return from the end (after evaluating first).
    :param size: The total number of items in the queryset.
    """
    #
    # Start from form fetching max number of items.
    #
    start: int = 0
    stop: int = size
    #
    # If `after` is given, change the start index to `after`.
    # If `after` is greater than the current queryset size, change it to `size`.
    #
    if after is not None:
        start = min(after, stop)
    #
    # If `before` is given, change the stop index to `before`.
    # If `before` is greater than the current queryset size, change it to `size`.
    #
    if before is not None:
        stop = min(before, stop)
    #
    # If first is given, and it's smaller than the current queryset size,
    # change the stop index to `start + first`
    # -> Length becomes that of `first`, and the items after it have been removed.
    #
    if first is not None and first < (stop - start):
        stop = start + first
    #
    # If last is given, and it's smaller than the current queryset size,
    # change the start index to `stop - last`.
    # -> Length becomes that of `last`, and the items before it have been removed.
    #
    if last is not None and last < (stop - start):
        start = stop - last

    return slice(start, stop)


def calculate_slice_for_queryset(
    queryset: models.QuerySet,
    *,
    after: Optional[int],
    before: Optional[int],
    first: Optional[int],
    last: Optional[int],
    size: int,
) -> models.QuerySet:
    """
    Annotate queryset with pagination slice start and stop indexes.
    This is the Django ORM equivalent of the `calculate_queryset_slice` function.
    """
    size_key = optimizer_settings.PREFETCH_COUNT_KEY
    # If the queryset has not been annotated with the total count, add an alias with the provided size.
    # (Since this is used in prefetch QuerySets, the provided size is likely wrong though.)
    if size_key not in queryset.query.annotations:  # pragma: no cover
        queryset = queryset.alias(**{size_key: models.Value(size)})

    start = models.Value(0)
    stop = models.F(optimizer_settings.PREFETCH_COUNT_KEY)

    if after is not None:
        start = models.Case(
            models.When(
                models.Q(**{f"{size_key}__lt": after}),
                then=stop,
            ),
            default=models.Value(after),
            output_field=models.IntegerField(),
        )

    if before is not None:
        stop = models.Case(
            models.When(
                models.Q(**{f"{size_key}__lt": before}),
                then=stop,
            ),
            default=models.Value(before),
            output_field=models.IntegerField(),
        )

    if first is not None:
        queryset = queryset.alias(**{f"{size_key}_size_1": stop - start})
        stop = models.Case(
            models.When(
                models.Q(**{f"{size_key}_size_1__lt": first}),
                then=stop,
            ),
            default=start + models.Value(first),
            output_field=models.IntegerField(),
        )

    if last is not None:
        queryset = queryset.alias(**{f"{size_key}_size_2": stop - start})
        start = models.Case(
            models.When(
                models.Q(**{f"{size_key}_size_2__lt": last}),
                then=start,
            ),
            default=stop - models.Value(last),
            output_field=models.IntegerField(),
        )

    return add_slice_to_queryset(queryset, start=start, stop=stop)


def add_slice_to_queryset(
    queryset: models.QuerySet,
    *,
    start: models.Expression,
    stop: models.Expression,
) -> models.QuerySet:
    return queryset.alias(
        **{
            optimizer_settings.PREFETCH_SLICE_START: start,
            optimizer_settings.PREFETCH_SLICE_STOP: stop,
        },
    )


class SubqueryCount(models.Subquery):
    template = "(SELECT COUNT(*) FROM (%(subquery)s) _count)"
    output_field = models.BigIntegerField()


@contextlib.contextmanager
def check_for_optimizer_errors() -> None:
    try:
        yield

    # Allow known errors to be raised.
    except OptimizerError:  # pragma: no cover
        raise

    # Raise unknown errors if not allowed to skip optimization on error.
    except Exception:  # noqa: BLE001  # pragma: no cover
        if not optimizer_settings.SKIP_OPTIMIZATION_ON_ERROR:
            raise
