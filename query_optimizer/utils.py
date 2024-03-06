from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import ForeignKey, QuerySet
from graphene import Connection
from graphene.utils.str_converters import to_snake_case
from graphene_django.utils import DJANGO_FILTER_INSTALLED
from graphql import FieldNode, FragmentSpreadNode, GraphQLField, InlineFragmentNode, get_argument_values
from graphql.execution.execute import get_field_def

from .errors import OptimizerError
from .settings import optimizer_settings
from .typing import GraphQLFilterInfo, overload

if TYPE_CHECKING:
    from graphene.types.definitions import GrapheneObjectType, GrapheneUnionType
    from graphene_django import DjangoObjectType
    from graphql import GraphQLOutputType, SelectionNode

    from .typing import (
        FieldNodes,
        GQLInfo,
        ModelField,
        Optional,
        ParamSpec,
        TModel,
        ToManyField,
        ToOneField,
        TypeGuard,
        TypeVar,
        Union,
    )

    T = TypeVar("T")
    P = ParamSpec("P")


__all__ = [
    "SubqueryCount",
    "get_field_type",
    "get_filter_info",
    "get_selections",
    "get_underlying_type",
    "is_foreign_key_id",
    "is_optimized",
    "is_to_many",
    "is_to_one",
    "mark_optimized",
    "mark_unoptimized",
    "optimizer_logger",
    "parse_order_by_args",
    "order_queryset",
]


optimizer_logger = logging.getLogger("query_optimizer")


def is_foreign_key_id(model_field: ModelField, name: str) -> bool:
    return isinstance(model_field, ForeignKey) and model_field.name != name and model_field.get_attname() == name


@overload
def get_underlying_type(
    field_type: type[GraphQLOutputType],
) -> type[Union[DjangoObjectType, GrapheneObjectType]]: ...  # pragma: no cover


@overload
def get_underlying_type(
    field_type: GraphQLOutputType,
) -> Union[DjangoObjectType, GrapheneObjectType]: ...  # pragma: no cover


def get_underlying_type(field_type):
    while hasattr(field_type, "of_type"):
        field_type = field_type.of_type
    return field_type


from loguru import logger


def is_to_many(model_field: ModelField) -> TypeGuard[ToManyField]:
    val = bool(model_field.one_to_many or model_field.many_to_many)
    # logger.debug(f"Detected `is_to_many` for field `{model_field}`: {val}")
    return val


def is_to_one(model_field: ModelField) -> TypeGuard[ToOneField]:
    return bool(model_field.many_to_one or model_field.one_to_one)


def get_field_type(info: GQLInfo) -> GrapheneObjectType:
    field_node = info.field_nodes[0]
    field_def = get_field_def(info.schema, info.parent_type, field_node)
    return get_underlying_type(field_def.type)


def get_selections(info: GQLInfo) -> tuple[SelectionNode, ...]:
    field_node = info.field_nodes[0]
    selection_set = field_node.selection_set
    return () if selection_set is None else selection_set.selections


def mark_optimized(queryset: QuerySet) -> None:
    """Mark queryset as optimized so that later optimizers know to skip optimization"""
    queryset._hints[optimizer_settings.OPTIMIZER_MARK] = True  # type: ignore[attr-defined]


def mark_unoptimized(queryset: QuerySet) -> None:  # pragma: no cover
    """Mark queryset as unoptimized so that later optimizers will run optimization"""
    queryset._hints.pop(optimizer_settings.OPTIMIZER_MARK, None)  # type: ignore[attr-defined]


def is_optimized(queryset: QuerySet) -> bool:
    """Has the queryset be optimized?"""
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


def get_filter_info(info: GQLInfo) -> GraphQLFilterInfo:
    """Find filter arguments from the GraphQL query."""
    args = _find_filtering_arguments(info.field_nodes, info.parent_type, info)  # type: ignore[arg-type]
    if not args:
        return {}
    return args[to_snake_case(info.field_name)]


def get_order_by_info(filter_info: dict) -> dict | None:
    return filter_info.get("filters", {}).get("order_by")


def _find_filtering_arguments(
    field_nodes: FieldNodes,
    parent: Union[GrapheneObjectType, GrapheneUnionType],
    info: GQLInfo,
) -> dict[str, GraphQLFilterInfo]:
    arguments: dict[str, GraphQLFilterInfo] = {}
    for selection in field_nodes:
        if isinstance(selection, FieldNode):
            _find_filter_info_from_field_node(selection, parent, arguments, info)

        elif isinstance(selection, FragmentSpreadNode):
            _find_filter_info_from_fragment_spread(selection, parent, arguments, info)

        elif isinstance(selection, InlineFragmentNode):
            _find_filter_info_from_inline_fragment(selection, parent, arguments, info)

        else:  # pragma: no cover
            msg = f"Unhandled selection node: '{selection}'"
            raise OptimizerError(msg)

    return {
        name: field
        for name, field in arguments.items()
        # Remove children that do not have filters or children.
        # Also preserve fields that are connections, so that default limiting can be applied.
        if field["filters"] or field["children"] or field["is_connection"]
    }


def uses_contenttypes(model: TModel) -> bool:
    # Check for GenericForeignKey usage
    for field in model._meta.fields:
        if isinstance(field, GenericForeignKey):
            return True  # Direct usage of contenttypes via GenericForeignKey

    # Check for ForeignKey relations to ContentType
    for field in model._meta.fields:  # noqa: SIM110
        if isinstance(field, ForeignKey) and field.related_model is ContentType:
            return True  # Usage of contenttypes via ForeignKey relation to ContentType

    return False  # No contenttypes usage detected


def _find_filter_info_from_field_node(
    selection: FieldNode,
    parent: GrapheneObjectType,
    arguments: dict[str, GraphQLFilterInfo],
    info: GQLInfo,
) -> None:
    field_def: Optional[GraphQLField] = get_field_def(info.schema, parent, selection)
    if field_def is None:  # pragma: no cover
        return

    name = to_snake_case(selection.name.value)
    filters = get_argument_values(type_def=field_def, node=selection, variable_values=info.variable_values)

    new_parent = get_underlying_type(field_def.type)

    # If the field is a connection, we need to go deeper to get the actual field
    if is_connection := issubclass(getattr(new_parent, "graphene_type", type(None)), Connection):
        # Find the actual parent object type.
        field_def = new_parent.fields["edges"]
        new_parent = get_underlying_type(field_def.type)
        field_def = new_parent.fields["node"]
        new_parent = get_underlying_type(field_def.type)

        # Find the actual field node.
        gen = (selection for selection in selection.selection_set.selections if selection.name.value == "edges")
        selection: Optional[FieldNode] = next(gen, None)
        # Edges was not requested, so we can skip this field
        if selection is None:
            return

        gen = (selection for selection in selection.selection_set.selections if selection.name.value == "node")
        selection: Optional[FieldNode] = next(gen, None)
        # Node was not requested, so we can skip this field
        if selection is None:
            return

    arguments[name] = filter_info = GraphQLFilterInfo(
        name=new_parent.name,
        filters=filters,
        children={},
        filterset_class=None,
        is_connection=is_connection,
    )

    if DJANGO_FILTER_INSTALLED and hasattr(new_parent, "graphene_type"):
        object_type = new_parent.graphene_type
        filter_info["filterset_class"] = getattr(object_type._meta, "filterset_class", None)

    if selection.selection_set is not None:
        result = _find_filtering_arguments(selection.selection_set.selections, new_parent, info)
        if result:
            filter_info["children"] = result


def _find_filter_info_from_fragment_spread(
    selection: FragmentSpreadNode,
    parent: GrapheneObjectType,
    arguments: dict[str, GraphQLFilterInfo],
    info: GQLInfo,
) -> None:
    graphql_name = selection.name.value
    field_node = info.fragments[graphql_name]
    selections = field_node.selection_set.selections
    arguments.update(_find_filtering_arguments(selections, parent, info))


def _find_filter_info_from_inline_fragment(
    selection: InlineFragmentNode,
    parent: GrapheneUnionType,
    arguments: dict[str, GraphQLFilterInfo],
    info: GQLInfo,
) -> None:
    fragment_type_name = selection.type_condition.name.value
    gen = (t for t in parent.types if t.name == fragment_type_name)
    selection_graphql_field: Optional[GrapheneObjectType] = next(gen, None)
    if selection_graphql_field is None:  # pragma: no cover
        return

    selections = selection.selection_set.selections
    arguments.update(_find_filtering_arguments(selections, selection_graphql_field, info))


class SubqueryCount(models.Subquery):
    template = "(SELECT COUNT(*) FROM (%(subquery)s) _count)"
    output_field = models.BigIntegerField()


def parse_order_by_args(queryset: QuerySet, order_by: list[str] | str | None) -> list[str] | None:
    if order_by:  # If not empty string or None value
        order_by = order_by.split(",") if isinstance(order_by, str) else order_by

    else:
        order_by = queryset.model._meta.ordering or None
        if order_by is None:
            return order_by

    return [to_snake_case(arg) for arg in order_by]


def order_queryset(queryset: QuerySet, order_by: list[str]) -> QuerySet:
    # FIXME: Is `.distinct()` really required?
    # https://web.archive.org/web/20230914181528/https://zainp.com/add-ordering-django-graphql/

    # return queryset.order_by(*order_by).distinct()
    return queryset.order_by(*order_by)
