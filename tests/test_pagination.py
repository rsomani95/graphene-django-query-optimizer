import pytest

from tests.factories import (
    ApartmentFactory,
    BuildingFactory,
    DeveloperFactory,
    HousingCompanyFactory,
    PropertyManagerFactory,
)
from tests.helpers import has, like

pytestmark = [
    pytest.mark.django_db,
]


def test_pagination__first(graphql_client):
    BuildingFactory.create(name="1")
    BuildingFactory.create(name="2")
    BuildingFactory.create(name="3")
    BuildingFactory.create(name="4")
    BuildingFactory.create(name="5")

    query = """
        query {
          pagedBuildings(first: 2) {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    assert response.queries.count == 2, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 2",
    )

    assert response.content == {
        "edges": [
            {"node": {"name": "1"}},
            {"node": {"name": "2"}},
        ],
    }


def test_pagination__last(graphql_client):
    BuildingFactory.create(name="1")
    BuildingFactory.create(name="2")
    BuildingFactory.create(name="3")
    BuildingFactory.create(name="4")
    BuildingFactory.create(name="5")

    query = """
        query {
          pagedBuildings(last: 2) {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    assert response.queries.count == 2, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 2 OFFSET 3",
    )

    assert response.content == {
        "edges": [
            {"node": {"name": "4"}},
            {"node": {"name": "5"}},
        ]
    }


def test_pagination__offset(graphql_client):
    BuildingFactory.create(name="1")
    BuildingFactory.create(name="2")
    BuildingFactory.create(name="3")
    BuildingFactory.create(name="4")
    BuildingFactory.create(name="5")

    query = """
        query {
          pagedBuildings(offset: 2) {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    assert response.queries.count == 2, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 3 OFFSET 2",
    )

    assert response.content == {
        "edges": [
            {"node": {"name": "3"}},
            {"node": {"name": "4"}},
            {"node": {"name": "5"}},
        ]
    }


def test_pagination__nested__one_to_many__first(graphql_client):
    building_1 = BuildingFactory.create(name="1")
    building_2 = BuildingFactory.create(name="2")
    ApartmentFactory.create(street_address="1", building=building_1)
    ApartmentFactory.create(street_address="2", building=building_1)
    ApartmentFactory.create(street_address="3", building=building_1)
    ApartmentFactory.create(street_address="4", building=building_2)
    ApartmentFactory.create(street_address="5", building=building_2)
    ApartmentFactory.create(street_address="6", building__name="3")

    query = """
        query {
          pagedBuildings {
            edges {
              node {
                apartments(first: 2) {
                  edges {
                    node {
                      streetAddress
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    # 1 query for fetching apartments.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 3",
    )

    assert response.queries[2] == has(
        'FROM "example_apartment"',
        'ROW_NUMBER() OVER (PARTITION BY "example_apartment"."building_id" ORDER BY "example_apartment"."id")',
        '0 AS "qual2"',
        '2 AS "qual0"',
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "1"}},
                            {"node": {"streetAddress": "2"}},
                        ],
                    },
                },
            },
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "4"}},
                            {"node": {"streetAddress": "5"}},
                        ],
                    },
                },
            },
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "6"}},
                        ],
                    },
                },
            },
        ],
    }


def test_pagination__nested__one_to_many__last(graphql_client):
    building_1 = BuildingFactory.create(name="1")
    building_2 = BuildingFactory.create(name="2")
    ApartmentFactory.create(street_address="1", building=building_1)
    ApartmentFactory.create(street_address="2", building=building_1)
    ApartmentFactory.create(street_address="3", building=building_1)
    ApartmentFactory.create(street_address="4", building=building_2)
    ApartmentFactory.create(street_address="5", building=building_2)
    ApartmentFactory.create(street_address="6", building__name="3")

    query = """
        query {
          pagedBuildings {
            edges {
              node {
                apartments(last: 2) {
                  edges {
                    node {
                      streetAddress
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    # 1 query for fetching apartments.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 3",
    )

    assert response.queries[2] == has(
        'FROM "example_apartment"',
        'ROW_NUMBER() OVER (PARTITION BY "example_apartment"."building_id" ORDER BY "example_apartment"."id")',
        # Since the last argument is used, the total count needs to be calculated for each partition.
        'AS "_optimizer_count"',
    )

    # The offset needs to be calculated for each partition for last.
    assert response.queries[2] == like(
        r".*CASE WHEN.*SELECT COUNT\(\*\).*THEN 0 ELSE.*SELECT COUNT\(\*\).*END.*",
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "2"}},
                            {"node": {"streetAddress": "3"}},
                        ],
                    },
                },
            },
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "4"}},
                            {"node": {"streetAddress": "5"}},
                        ],
                    },
                },
            },
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "6"}},
                        ],
                    },
                },
            },
        ],
    }


def test_pagination__nested__one_to_many__offset(graphql_client):
    building_1 = BuildingFactory.create(name="1")
    building_2 = BuildingFactory.create(name="2")
    ApartmentFactory.create(street_address="1", building=building_1)
    ApartmentFactory.create(street_address="2", building=building_1)
    ApartmentFactory.create(street_address="3", building=building_1)
    ApartmentFactory.create(street_address="4", building=building_2)
    ApartmentFactory.create(street_address="5", building=building_2)
    ApartmentFactory.create(street_address="6", building__name="3")

    query = """
        query {
          pagedBuildings {
            edges {
              node {
                apartments(offset: 2) {
                  edges {
                    node {
                      streetAddress
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    # 1 query for fetching apartments.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 3",
    )

    assert response.queries[2] == has(
        'FROM "example_apartment"',
        'ROW_NUMBER() OVER (PARTITION BY "example_apartment"."building_id" ORDER BY "example_apartment"."id")',
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "3"}},
                        ],
                    },
                },
            },
            {
                "node": {
                    "apartments": {
                        "edges": [],
                    },
                },
            },
            {
                "node": {
                    "apartments": {
                        "edges": [],
                    },
                },
            },
        ],
    }


def test_pagination__nested__many_to_many(graphql_client):
    developer_1 = DeveloperFactory.create(name="1")
    developer_2 = DeveloperFactory.create(name="2")
    developer_3 = DeveloperFactory.create(name="3")
    developer_4 = DeveloperFactory.create(name="4")
    developer_5 = DeveloperFactory.create(name="5")
    HousingCompanyFactory.create(developers=[developer_1, developer_2, developer_3])
    HousingCompanyFactory.create(developers=[developer_4, developer_5])
    HousingCompanyFactory.create(developers__name="6")

    query = """
        query {
          pagedHousingCompanies {
            edges {
              node {
                developers(first:2) {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting housing companies.
    # 1 query for fetching housing companies.
    # 1 query for fetching real estates.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_housingcompany"',
    )
    assert response.queries[1] == has(
        'FROM "example_housingcompany"',
        "LIMIT 3",
    )
    assert response.queries[2] == has(
        'FROM "example_developer"',
        (
            "ROW_NUMBER() OVER "
            '(PARTITION BY "example_housingcompany_developers"."housingcompany_id" ORDER BY "example_developer"."id")'
        ),
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "developers": {
                        "edges": [
                            {"node": {"name": "1"}},
                            {"node": {"name": "2"}},
                        ]
                    }
                }
            },
            {
                "node": {
                    "developers": {
                        "edges": [
                            {"node": {"name": "4"}},
                            {"node": {"name": "5"}},
                        ]
                    }
                }
            },
            {
                "node": {
                    "developers": {
                        "edges": [
                            {"node": {"name": "6"}},
                        ]
                    }
                }
            },
        ]
    }


def test_pagination__nested__many_to_many__reverse(graphql_client):
    housing_company_1 = HousingCompanyFactory.create(name="1")
    housing_company_2 = HousingCompanyFactory.create(name="2")
    housing_company_3 = HousingCompanyFactory.create(name="3")
    housing_company_4 = HousingCompanyFactory.create(name="4")
    housing_company_5 = HousingCompanyFactory.create(name="5")
    DeveloperFactory.create(housingcompany_set=[housing_company_1, housing_company_2, housing_company_3])
    DeveloperFactory.create(housingcompany_set=[housing_company_4, housing_company_5])
    DeveloperFactory.create(housingcompany_set__name="6")

    query = """
        query {
          pagedDevelopers {
            edges {
              node {
                housingcompanySet(first:2) {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting developers.
    # 1 query for fetching developers.
    # 1 query for fetching housing companies.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_developer"',
    )
    assert response.queries[1] == has(
        'FROM "example_developer"',
        "LIMIT 3",
    )
    assert response.queries[2] == has(
        'FROM "example_housingcompany"',
        (
            "ROW_NUMBER() OVER "
            '(PARTITION BY "example_housingcompany_developers"."developer_id" ORDER BY "example_housingcompany"."id")'
        ),
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "housingcompanySet": {
                        "edges": [
                            {"node": {"name": "1"}},
                            {"node": {"name": "2"}},
                        ]
                    }
                }
            },
            {
                "node": {
                    "housingcompanySet": {
                        "edges": [
                            {"node": {"name": "4"}},
                            {"node": {"name": "5"}},
                        ]
                    }
                }
            },
            {
                "node": {
                    "housingcompanySet": {
                        "edges": [
                            {"node": {"name": "6"}},
                        ]
                    }
                }
            },
        ]
    }


def test_pagination__nested__custom_ordering__asc(graphql_client):
    property_manager_1 = PropertyManagerFactory.create()
    property_manager_2 = PropertyManagerFactory.create()
    HousingCompanyFactory.create(property_manager=property_manager_1, street_address="1")
    HousingCompanyFactory.create(property_manager=property_manager_1, street_address="3")
    HousingCompanyFactory.create(property_manager=property_manager_1, street_address="1")
    HousingCompanyFactory.create(property_manager=property_manager_2, street_address="5")
    HousingCompanyFactory.create(property_manager=property_manager_2, street_address="4")

    query = """
        query {
          pagedPropertyManagers {
            edges {
              node {
                housingCompanies(first:1 orderBy:"street_address") {
                  edges {
                    node {
                      streetAddress
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting property managers.
    # 1 query for fetching property managers.
    # 1 query for fetching housing companies.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_propertymanager"',
    )
    assert response.queries[1] == has(
        'FROM "example_propertymanager"',
        "LIMIT 2",
    )
    assert response.queries[2] == has(
        'FROM "example_housingcompany"',
        (
            "ROW_NUMBER() OVER "
            '(PARTITION BY "example_housingcompany"."property_manager_id" '
            'ORDER BY "example_housingcompany"."street_address")'
        ),
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "housingCompanies": {
                        "edges": [
                            {"node": {"streetAddress": "1"}},
                        ]
                    }
                }
            },
            {
                "node": {
                    "housingCompanies": {
                        "edges": [
                            {"node": {"streetAddress": "4"}},
                        ]
                    }
                }
            },
        ]
    }


def test_pagination__nested__custom_ordering__desc(graphql_client):
    property_manager_1 = PropertyManagerFactory.create()
    property_manager_2 = PropertyManagerFactory.create()
    HousingCompanyFactory.create(property_manager=property_manager_1, street_address="1")
    HousingCompanyFactory.create(property_manager=property_manager_1, street_address="3")
    HousingCompanyFactory.create(property_manager=property_manager_1, street_address="2")
    HousingCompanyFactory.create(property_manager=property_manager_2, street_address="5")
    HousingCompanyFactory.create(property_manager=property_manager_2, street_address="4")

    query = """
        query {
          pagedPropertyManagers {
            edges {
              node {
                housingCompanies(first:1 orderBy:"-street_address") {
                  edges {
                    node {
                      streetAddress
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting property managers.
    # 1 query for fetching property managers.
    # 1 query for fetching housing companies.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_propertymanager"',
    )
    assert response.queries[1] == has(
        'FROM "example_propertymanager"',
        "LIMIT 2",
    )
    assert response.queries[2] == has(
        'FROM "example_housingcompany"',
        (
            "ROW_NUMBER() OVER "
            '(PARTITION BY "example_housingcompany"."property_manager_id" '
            'ORDER BY "example_housingcompany"."street_address" DESC)'
        ),
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "housingCompanies": {
                        "edges": [
                            {"node": {"streetAddress": "3"}},
                        ]
                    }
                }
            },
            {
                "node": {
                    "housingCompanies": {
                        "edges": [
                            {"node": {"streetAddress": "5"}},
                        ]
                    }
                }
            },
        ]
    }


@pytest.mark.usefixtures("_set_building_node_apartments_max_limit")
def test_pagination__nested__implicit_limit(graphql_client):
    building = BuildingFactory.create()
    ApartmentFactory.create(street_address="1", building=building)
    ApartmentFactory.create(street_address="2", building=building)
    ApartmentFactory.create(street_address="3", building=building)
    ApartmentFactory.create(street_address="4")
    ApartmentFactory.create(street_address="5")

    query = """
        query {
          pagedBuildings {
            edges {
              node {
                apartments {
                  edges {
                    node {
                      streetAddress
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    # 1 query for fetching apartments.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 3",
    )

    assert response.queries[2] == has(
        'FROM "example_apartment"',
        'ROW_NUMBER() OVER (PARTITION BY "example_apartment"."building_id" ORDER BY "example_apartment"."id")',
        '1 AS "qual0"',
        '0 AS "qual2"',
    )

    assert response.content == {
        "edges": [
            {"node": {"apartments": {"edges": [{"node": {"streetAddress": "1"}}]}}},
            {"node": {"apartments": {"edges": [{"node": {"streetAddress": "4"}}]}}},
            {"node": {"apartments": {"edges": [{"node": {"streetAddress": "5"}}]}}},
        ]
    }


@pytest.mark.usefixtures("_remove_apartment_node_apartments_max_limit")
def test_pagination__nested__limit_first(graphql_client):
    building = BuildingFactory.create()
    ApartmentFactory.create(street_address="1", building=building)
    ApartmentFactory.create(street_address="2", building=building)
    ApartmentFactory.create(street_address="3", building=building)
    ApartmentFactory.create(street_address="4")
    ApartmentFactory.create(street_address="5")

    query = """
        query {
          pagedBuildings {
            edges {
              node {
                apartments(first: 1) {
                  edges {
                    node {
                      streetAddress
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    # 1 query for fetching apartments.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 3",
    )

    assert response.queries[2] == has(
        'FROM "example_apartment"',
        'ROW_NUMBER() OVER (PARTITION BY "example_apartment"."building_id" ORDER BY "example_apartment"."id")',
    )

    # The actual total count is calculated for the nested connection.
    assert response.queries[2] == like(
        r'.*\(SELECT COUNT\(\*\) FROM \(SELECT .* FROM "example_apartment" .*\) _count\) AS "_optimizer_count".*'
    )

    assert response.content == {
        "edges": [
            {"node": {"apartments": {"edges": [{"node": {"streetAddress": "1"}}]}}},
            {"node": {"apartments": {"edges": [{"node": {"streetAddress": "4"}}]}}},
            {"node": {"apartments": {"edges": [{"node": {"streetAddress": "5"}}]}}},
        ]
    }


@pytest.mark.usefixtures("_remove_apartment_node_apartments_max_limit")
def test_pagination__nested__limit__total_count(graphql_client):
    building = BuildingFactory.create()
    ApartmentFactory.create(street_address="1", building=building)
    ApartmentFactory.create(street_address="2", building=building)
    ApartmentFactory.create(street_address="3", building=building)
    ApartmentFactory.create(street_address="4")
    ApartmentFactory.create(street_address="5")

    query = """
        query {
          pagedBuildings {
            edges {
              node {
                apartments {
                  totalCount
                  edges {
                    node {
                      streetAddress
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting buildings.
    # 1 query for fetching buildings.
    # 1 query for fetching nested apartments.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_building"',
    )

    assert response.queries[1] == has(
        'FROM "example_building"',
        "LIMIT 3",
    )

    assert response.queries[2] == has(
        'FROM "example_apartment"',
    )

    # Since max_limit=None, and there is no limit arguments, don't limit the connection with the window function.
    assert response.queries[2] != has(
        'ROW_NUMBER() OVER (PARTITION BY "example_apartment"."building_id" ORDER BY "example_apartment"."id")',
    )

    # The actual total count is calculated for the nested connection.
    assert response.queries[2] == like(
        r'.*\(SELECT COUNT\(\*\) FROM \(SELECT .* FROM "example_apartment" .*\) _count\) AS "_optimizer_count".*'
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "1"}},
                            {"node": {"streetAddress": "2"}},
                            {"node": {"streetAddress": "3"}},
                        ],
                        "totalCount": 3,
                    }
                }
            },
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "4"}},
                        ],
                        "totalCount": 1,
                    }
                },
            },
            {
                "node": {
                    "apartments": {
                        "edges": [
                            {"node": {"streetAddress": "5"}},
                        ],
                        "totalCount": 1,
                    }
                },
            },
        ]
    }
