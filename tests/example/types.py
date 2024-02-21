import graphene
from django.db.models import F, Model, QuerySet, Value
from django.db.models.functions import Concat
from django_filters import CharFilter, FilterSet, OrderingFilter
from graphene import relay

from query_optimizer import DjangoConnectionField, DjangoObjectType, required_fields
from query_optimizer.optimizer import required_annotations
from query_optimizer.typing import GQLInfo
from tests.example.models import (
    Apartment,
    ApartmentProxy,
    Building,
    BuildingProxy,
    Developer,
    Example,
    ForwardManyToMany,
    ForwardManyToManyForRelated,
    ForwardManyToOne,
    ForwardManyToOneForRelated,
    ForwardOneToOne,
    ForwardOneToOneForRelated,
    HousingCompany,
    HousingCompanyProxy,
    Owner,
    Ownership,
    PostalCode,
    PropertyManager,
    RealEstate,
    RealEstateProxy,
    ReverseManyToMany,
    ReverseManyToManyToForwardManyToMany,
    ReverseManyToManyToForwardManyToOne,
    ReverseManyToManyToForwardOneToOne,
    ReverseManyToManyToReverseManyToMany,
    ReverseManyToManyToReverseOneToMany,
    ReverseManyToManyToReverseOneToOne,
    ReverseOneToMany,
    ReverseOneToManyToForwardManyToMany,
    ReverseOneToManyToForwardManyToOne,
    ReverseOneToManyToForwardOneToOne,
    ReverseOneToManyToReverseManyToMany,
    ReverseOneToManyToReverseOneToMany,
    ReverseOneToManyToReverseOneToOne,
    ReverseOneToOne,
    ReverseOneToOneToForwardManyToMany,
    ReverseOneToOneToForwardManyToOne,
    ReverseOneToOneToForwardOneToOne,
    ReverseOneToOneToReverseManyToMany,
    ReverseOneToOneToReverseOneToMany,
    ReverseOneToOneToReverseOneToOne,
    Sale,
)
from loguru import logger

__all__ = [
    "ApartmentNode",
    "ApartmentType",
    "BuildingType",
    "DeveloperType",
    "HousingCompanyNode",
    "HousingCompanyType",
    "OwnershipType",
    "OwnerType",
    "People",
    "PostalCodeType",
    "PropertyManagerType",
    "RealEstateType",
    "SaleType",
]

class IsTypeOfProxyPatch:
    @classmethod
    def is_type_of(cls, root, info):
        if cls._meta.model._meta.proxy:
            return root._meta.model._meta.concrete_model == cls._meta.model._meta.concrete_model
        return super().is_type_of(root, info)


class ApartmentNode(DjangoObjectType):
    class Meta:
        model = Apartment
        max_complexity = 10
        filter_fields = {
            "street_address": ["exact"],
            "building__name": ["exact"],
        }
        interfaces = (relay.Node,)


class BuildingNode(DjangoObjectType):
    apartments = DjangoConnectionField(ApartmentNode)

    class Meta:
        model = Building
        interfaces = (relay.Node,)


class RealEstateNode(DjangoObjectType):
    buildings = DjangoConnectionField(BuildingNode)

    class Meta:
        model = RealEstate
        interfaces = (relay.Node,)


# Django-filters


class HousingCompanyFilterSet(FilterSet):
    order_by = OrderingFilter(
        fields=[
            "name",
            "street_address",
            "postal_code__code",
            "city",
            "developers__name",
        ],
    )

    address = CharFilter(method="filter_address")

    class Meta:
        model = HousingCompany
        fields = {
            "name": ["iexact", "icontains"],
            "street_address": ["iexact", "icontains"],
            "postal_code__code": ["iexact"],
            "city": ["iexact", "icontains"],
            "developers__name": ["iexact", "icontains"],
        }

    def filter_address(self, qs: QuerySet[HousingCompany], name: str, value: str) -> QuerySet[HousingCompany]:
        return qs.alias(
            _address=Concat(
                F("street_address"),
                Value(", "),
                F("postal_code__code"),
                Value(" "),
                F("city"),
            ),
        ).filter(_address__icontains=value)


class HousingCompanyNode(DjangoObjectType):
    real_estates = DjangoConnectionField(RealEstateNode)

    def resolve_real_estates(self, info):
        # logger.info("In custom real estates resolver")
        return self.real_estates.all()

    class Meta:
        model = HousingCompany
        interfaces = (relay.Node,)
        filterset_class = HousingCompanyFilterSet
