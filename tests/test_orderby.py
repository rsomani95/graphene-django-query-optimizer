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
