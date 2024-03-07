from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Collection,
    Generator,
    Hashable,
    Iterable,
    Literal,
    NamedTuple,
    Optional,
    Type,
    TypedDict,
    TypeVar,
    Union,
    overload,
)

from graphene.relay.connection import ConnectionOptions
from graphene_django.types import DjangoObjectTypeOptions
from graphql_relay import ConnectionType

# New in version 3.10
try:
    from typing import ParamSpec, TypeAlias, TypeGuard
except ImportError:
    from typing_extensions import ParamSpec, TypeAlias, TypeGuard


from django.core.handlers.wsgi import WSGIRequest
from django.db.models import (
    Field,
    ForeignKey,
    ForeignObject,
    ForeignObjectRel,
    Manager,
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneField,
    QuerySet,
)
from graphql import FieldNode, GraphQLResolveInfo, SelectionNode

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser, User
    from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
    from django_filters import FilterSet

__all__ = [
    "Any",
    "Callable",
    "Collection",
    "ConnectionResolver",
    "FieldNodes",
    "FilterFields",
    "GQLInfo",
    "Generator",
    "GraphQLFilterInfo",
    "Hashable",
    "Iterable",
    "Literal",
    "ModelField",
    "ModelResolver",
    "NamedTuple",
    "OptimizedDjangoOptions",
    "Optional",
    "PK",
    "ParamSpec",
    "QueryCache",
    "QuerySetResolver",
    "OptimizerKey",
    "TableName",
    "ToManyField",
    "ToOneField",
    "Type",
    "TypeGuard",
    "TypeOptions",
    "TypeVar",
    "TypedDict",
    "Union",
    "overload",
]


TModel = TypeVar("TModel", bound=Model)
TableName: TypeAlias = str
OptimizerKey: TypeAlias = str
PK: TypeAlias = Any
QueryCache: TypeAlias = dict[TableName, dict[OptimizerKey, dict[PK, TModel]]]
ModelField: TypeAlias = Union[Field, ForeignObjectRel, "GenericForeignKey"]
ToManyField: TypeAlias = Union["GenericRelation", ManyToManyField, ManyToOneRel, ManyToManyRel]
ToOneField: TypeAlias = Union["GenericRelation", ForeignObject, ForeignKey, OneToOneField]
TypeOptions: TypeAlias = Union[DjangoObjectTypeOptions, ConnectionOptions]
AnyUser: TypeAlias = Union["User", "AnonymousUser"]
FilterFields: TypeAlias = Union[dict[str, list[str]], list[str]]

QuerySetResolver = Callable[..., Union[QuerySet, Manager, None]]
ModelResolver = Callable[..., Union[Model, None]]
ConnectionResolver = Callable[..., ConnectionType]
FieldNodes = Iterable[Union[FieldNode, SelectionNode]]


class UserHintedWSGIRequest(WSGIRequest):
    user: AnyUser


class GQLInfo(GraphQLResolveInfo):
    context: UserHintedWSGIRequest


class OptimizedDjangoOptions(DjangoObjectTypeOptions):
    max_complexity: int


class GraphQLFilterInfo(TypedDict, total=False):
    name: str
    filters: dict[str, Any]
    children: dict[str, GraphQLFilterInfo]
    filterset_class: Optional[type[FilterSet]]
    is_connection: bool
    is_node: bool
