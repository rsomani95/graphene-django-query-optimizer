import json

import pytest

from tests.example.models_2 import SegmentProperTags
from tests.example.utils import capture_database_queries

pytestmark = pytest.mark.django_db


def test_optimizer__order_by__top_level(client_query):
    query = """
{
  pagedSegments(orderBy:"inTime") {
    edges {
      node {
        id
        inTime
      }
    }
  }
}
    """

    with capture_database_queries() as results:
        response = client_query(query)

    content = json.loads(response.content)

    assert "errors" not in content, content["errors"]

    queries = len(results.queries)
    # 1 query for counting segments
    # 1 query for selecting and ordering segments
    assert queries == 2, results.log
    assert "ORDER BY" in results.queries[-1]

    # Assert returned values order
    edges = content["data"]["pagedSegments"]["edges"]
    in_times = [edge["node"]["inTime"] for edge in edges]
    assert in_times == sorted(in_times)


def test_optimizer__order_by__nested(client_query):
    query = """
{
  pagedAssets {
    edges {
      node {
        segments(orderBy:"inTime") {
          edges {
            node {
              id
              inTime
            }
          }
        }
      }
    }
  }
}
    """

    with capture_database_queries() as results:
        response = client_query(query)

    content = json.loads(response.content)

    assert "errors" not in content, content["errors"]

    queries = len(results.queries)
    # 1 query for counting assets
    # 1 query for selecting assets
    # 1 query for ordering partitioned segments
    assert queries == 3, results.log
    assert "ORDER BY" in results.queries[-1]

    # Assert returned values order
    for va_edge in content["data"]["pagedAssets"]["edges"]:
        edges = va_edge["node"]["segments"]["edges"]
        in_times = [edge["node"]["inTime"] for edge in edges]
        assert in_times == sorted(in_times)
