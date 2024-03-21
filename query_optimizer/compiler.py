from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Optional, Union

from django.db.models import ForeignKey, Manager, ManyToOneRel, Model, QuerySet
from graphene.utils.str_converters import to_snake_case
from graphene_django.utils import maybe_queryset
from loguru import logger

from .ast import GraphQLASTWalker
from .cache import get_from_query_cache, store_in_query_cache
from .errors import OptimizerError
from .filter_info import get_filter_info
from .optimizer import QueryOptimizer
from .settings import optimizer_settings
from .utils import (
    get_order_by_info,
    is_optimized,
    optimizer_logger,
    order_queryset,
    parse_order_by_args,
)

if TYPE_CHECKING:
    import graphene
    from django.db import models
    from graphene.types.definitions import GrapheneObjectType
    from graphql import FieldNode

    from .typing import PK, GQLInfo, ToManyField, ToOneField, TypeVar

    TModel = TypeVar("TModel", bound=Model)


__all__ = [
    "optimize",
    "optimize_single",
    "OptimizationCompiler",
]


def optimize(
    queryset: QuerySet[TModel],
    info: GQLInfo,
    *,
    max_complexity: Optional[int] = None,
) -> QuerySet[TModel]:
    """Optimize the given queryset according to the field selections received in the GraphQLResolveInfo."""
    optimizer = OptimizationCompiler(info, max_complexity=max_complexity).compile(queryset)
    if optimizer is not None:
        logger.debug("About to optimize queryset")
        queryset = optimizer.optimize_queryset(queryset)

        order_by = parse_order_by_args(
            queryset=queryset,
            order_by=get_order_by_info(get_filter_info(optimizer.info, queryset.model)),
        )
        logger.debug(f"Top level Qset `order_by`: {order_by}")
        if order_by:
            queryset = order_queryset(queryset, order_by)
            logger.debug("Ordered top level qset")

        store_in_query_cache(queryset, optimizer, info)

    return queryset


def optimize_single(
    queryset: QuerySet[TModel],
    info: GQLInfo,
    *,
    pk: PK,
    max_complexity: Optional[int] = None,
) -> Optional[TModel]:
    """Optimize the given queryset for a single model instance by its primary key."""
    queryset = queryset.filter(pk=pk)

    optimizer = OptimizationCompiler(info, max_complexity=max_complexity).compile(queryset)
    if optimizer is None:  # pragma: no cover
        return queryset.first()

    cached_item = get_from_query_cache(queryset.model, pk, optimizer, info)
    if cached_item is not None:
        return cached_item

    logger.debug("About to optimize queryset")
    optimized_queryset = optimizer.optimize_queryset(queryset)
    store_in_query_cache(optimized_queryset, optimizer, info)

    # Shouldn't use .first(), as it can apply additional ordering, which would cancel the optimization.
    # The queryset should have the right model instance, since we started by filtering by its pk,
    # so we can just pick that out of the result cache (if it hasn't been filtered out).
    return next(iter(optimized_queryset._result_cache or []), None)


class OptimizationCompiler(GraphQLASTWalker):
    """Class for compiling SQL optimizations based on the given query."""

    def __init__(self, info: GQLInfo, max_complexity: Optional[int] = None) -> None:
        """
        Initialize the optimization compiler with the query info.

        :param info: The GraphQLResolveInfo containing the query AST.
        :param max_complexity: How many 'select_related' and 'prefetch_related' table joins are allowed.
                               Used to protect from malicious queries.
        """
        self.max_complexity = max_complexity or optimizer_settings.MAX_COMPLEXITY
        self.optimizer: QueryOptimizer = None  # type: ignore[assignment]
        self.to_attr: Optional[str] = None
        super().__init__(info)

    def compile(self, queryset: Union[QuerySet, Manager, list[Model]]) -> Optional[QueryOptimizer]:
        """
        Compile optimizations for the given queryset.

        :return: QueryOptimizer instance that can perform any needed optimization,
                 or None if queryset is already optimized.
        :raises OptimizerError: Something went wrong during the optimization process.
        """
        queryset = maybe_queryset(queryset)
        # If prior optimization has been done already, return early.
        if is_optimized(queryset):
            return None

        # Setup initial state.
        self.model = queryset.model
        self.optimizer = QueryOptimizer(model=queryset.model, info=self.info)

        # Walk the query AST to compile the optimizations.
        try:
            self.run()

        # Allow known errors to be raised.
        except OptimizerError:  # pragma: no cover
            raise

        # Raise unknown errors if not allowed to skip optimization on error.
        except Exception as error:  # noqa: BLE001  # pragma: no cover
            optimizer_logger.warning("Something went wrong during the optimization process.", exc_info=error)
            if not optimizer_settings.SKIP_OPTIMIZATION_ON_ERROR:
                raise
            return None

        return self.optimizer

    def increase_complexity(self) -> None:
        super().increase_complexity()
        if self.complexity > self.max_complexity:
            msg = f"Query complexity exceeds the maximum allowed of {self.max_complexity}"
            raise OptimizerError(msg)

    def handle_normal_field(self, field_type: GrapheneObjectType, field_node: FieldNode, field: models.Field) -> None:
        self.optimizer.only_fields.append(field.get_attname())

    def handle_to_one_field(
        self,
        field_type: GrapheneObjectType,
        field_node: FieldNode,
        related_field: ToOneField,
        related_model: type[Model],
    ) -> None:
        name = related_field.get_cache_name() or related_field.name
        optimizer = QueryOptimizer(model=related_model, info=self.info, to_attr=self.to_attr)
        self.optimizer.select_related[name] = optimizer
        if isinstance(related_field, ForeignKey):
            self.optimizer.related_fields.append(related_field.attname)

        with self.use_optimizer(optimizer):
            super().handle_to_many_field(field_type, field_node, related_field, related_model)

    def handle_to_many_field(
        self,
        field_type: GrapheneObjectType,
        field_node: FieldNode,
        related_field: ToManyField,
        related_model: type[Model],
    ) -> None:
        name = related_field.get_cache_name() or related_field.name
        optimizer = QueryOptimizer(model=related_model, info=self.info, to_attr=self.to_attr)
        self.optimizer.prefetch_related[name] = optimizer
        if isinstance(related_field, ManyToOneRel):
            optimizer.related_fields.append(related_field.field.attname)

        with self.use_optimizer(optimizer):
            super().handle_to_many_field(field_type, field_node, related_field, related_model)

    def handle_total_count(self, field_type: GrapheneObjectType, field_node: FieldNode) -> None:
        self.optimizer.total_count = True

    def handle_custom_field(self, field_type: GrapheneObjectType, field_node: FieldNode) -> None:
        field_name = to_snake_case(field_node.name.value)
        field: Optional[graphene.Field] = field_type.graphene_type._meta.fields.get(field_name)
        if field is None:  # pragma: no cover
            msg = (
                f"Field '{field_node.name.value}' not found from object type '{field_type.graphene_type}'. "
                f"Cannot optimize custom field."
            )
            optimizer_logger.warning(msg)
            return None

        # `RelatedField`, `DjangoListField` and `DjangoConnectionField` can define
        # a 'field_name' attribute to specify the actual model field name.
        actual_field_name: Optional[str] = getattr(field, "field_name", None)
        if actual_field_name is not None:
            with self.use_to_attr(field_name):
                return self.handle_model_field(field_type, field_node, actual_field_name)

        from .fields import AnnotatedField, MultiField

        if isinstance(field, AnnotatedField):
            self.optimizer.annotations[to_snake_case(field.name)] = field.expression
            if field.aliases is not None:
                self.optimizer.aliases.update(field.aliases)
            return None

        if isinstance(field, MultiField):
            self.optimizer.only_fields.extend(field.fields)
            return None

        return None  # pragma: no cover

    @contextlib.contextmanager
    def use_optimizer(self, optimizer: QueryOptimizer) -> None:
        orig_optimizer = self.optimizer
        try:
            self.optimizer = optimizer
            yield
        finally:
            self.optimizer = orig_optimizer

    @contextlib.contextmanager
    def use_to_attr(self, to_attr: str) -> None:
        orig_attr = self.to_attr
        try:
            self.to_attr = to_attr
            yield
        finally:
            self.to_attr = orig_attr
