# Technical details

The optimizer uses the `GraphQLResolveInfo` and GraphQL AST to introspect
the desired query, and construct [queryset.only()][only],
[queryset.select_related()][select], and [queryset.prefetch_related()][prefetch]
statements for the resolver queryset.

The result is then stored inside the schema [extensions] dictionary under
the `_query_cache` key (hopefully nothing else uses this). The cache uses
a [WeakKeyDictionary], where the key is a `info.operation` for the current query.
This ensures that the cache is automatically cleared after the request is done.
Different records are sorted based on their database table name, selected
fields & joined tables, and primary keys. Subsequent resolvers will then
attempt to retrieve the cached data stored by the parent query.

> [Inline fragments] are not supported, mainly because I don't have a use for them :P

[only]: https://docs.djangoproject.com/en/dev/ref/models/querysets/#only
[select]: https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-related
[prefetch]: https://docs.djangoproject.com/en/dev/ref/models/querysets/#prefetch-related
[extensions]: https://github.com/graphql-python/graphql-core/blob/0c93b8452eed38d4f800c7e71cf6f3f3758cd1c6/src/graphql/type/schema.py#L123
[WeakKeyDictionary]: https://docs.python.org/3/library/weakref.html#weakref.WeakKeyDictionary
[Inline fragments]: https://graphql.org/learn/queries/#inline-fragments