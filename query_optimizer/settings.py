from __future__ import annotations

from typing import TYPE_CHECKING

from django.test.signals import setting_changed  # type: ignore[attr-defined]
from settings_holder import SettingsHolder, reload_settings

from .typing import NamedTuple

if TYPE_CHECKING:
    from .typing import Any, Union


__all__ = [
    "optimizer_settings",
]


SETTING_NAME: str = "GRAPHQL_QUERY_OPTIMIZER"


class DefaultSettings(NamedTuple):
    QUERY_CACHE_KEY: str = "_query_cache"
    """Key to store fetched model instances under in the GraphQL schema extensions."""
    OPTIMIZER_MARK: str = "_optimized"
    """Key used mark if a queryset has been optimized by the query optimizer."""
    OPTIMIZER_PREFETCH_COUNT_KEY: str = "_optimizer_count"
    """Name used for annotating prefetched queryset total count."""
    DISABLE_ONLY_FIELDS_OPTIMIZATION: bool = False
    """Disable optimizing fetched fields with `queryset.only()`."""
    MAX_COMPLEXITY: int = 10
    """Default max number of 'select_related' and 'prefetch related' joins optimizer is allowed to optimize."""
    SKIP_OPTIMIZATION_ON_ERROR: bool = False
    """If there is an unexpected error, should the optimizer skip optimization (True) or throw an error (False)?"""
    DEFAULT_FILTERSET_CLASS: str = ""
    """The default filterset class to use."""


DEFAULTS: dict[str, Any] = DefaultSettings()._asdict()
IMPORT_STRINGS: set[Union[bytes, str]] = set()
REMOVED_SETTINGS: set[str] = {
    "PK_CACHE_KEY",
    "DONT_OPTIMIZE_ON_ERROR",
}

optimizer_settings = SettingsHolder(
    setting_name=SETTING_NAME,
    defaults=DEFAULTS,
    import_strings=IMPORT_STRINGS,
    removed_settings=REMOVED_SETTINGS,
)

reload_my_settings = reload_settings(SETTING_NAME, optimizer_settings)
setting_changed.connect(reload_my_settings)
