import json

import pytest

from tests.example.models_2 import SegmentProperTags
from tests.example.utils import capture_database_queries

pytestmark = pytest.mark.django_db


def test_optimizer__tagged_items(client_query):
    query = """
{
  pagedSegments {
    edges {
      node {
        id
        taggedItems {
          name
          category
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
    # 1 query for counting segments
    # 1 query for selecting segments
    # 1 query for joining taggedItems
    assert queries == 3, results.log
