import itertools
from typing import Iterable, Union

import graphene
from django.db import models
from django.db.models.functions import Concat
from graphene import relay
from graphene_django import DjangoListField
from graphene_django.debug import DjangoDebug

from query_optimizer import DjangoConnectionField, optimize
from query_optimizer.filter import DjangoFilterConnectionField
from query_optimizer.typing import GQLInfo

from .types import (
    ApartmentNode,
    BuildingNode,
    HousingCompanyNode,
    RealEstateNode,
)


class Query(graphene.ObjectType):
    paged_apartments = DjangoFilterConnectionField(ApartmentNode)
    paged_buildings = DjangoConnectionField(BuildingNode)
    paged_real_estates = DjangoConnectionField(RealEstateNode)
    paged_housing_companies = DjangoFilterConnectionField(HousingCompanyNode)
    debug = graphene.Field(DjangoDebug, name="_debug")


schema = graphene.Schema(query=Query)
