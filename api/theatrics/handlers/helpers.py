import json
from urllib.parse import parse_qs, urlencode
from math import ceil
from functools import wraps

import aioes
from aiohttp import web
from marshmallow import Schema, fields
from marshmallow.validate import Range

from ..connections import elastic
from ..settings import ELASTICSEARCH_INDEX

from .fields import CommaSeparatedList


class ListParams(Schema):
    page_size = fields.Integer(validate=Range(1, 100))
    page = fields.Integer(validate=Range(1))
    expand = CommaSeparatedList(fields.String())
    fields = CommaSeparatedList(fields.String())


class ItemParams(Schema):
    expand = CommaSeparatedList(fields.String())
    fields = CommaSeparatedList(fields.String())


def with_params(schema_cls):
    def decorator(f):
        @wraps(f)
        async def wrapper(request):
            schema = schema_cls(request)
            result = schema.load(request.GET)
            if result.errors:
                raise web.HTTPBadRequest(
                    text=json.dumps({
                        'errors': result.errors
                    }, ensure_ascii=False),
                    content_type='application/json',
                )
            else:
                return await f(request, **result.data)
        return wrapper
    return decorator


def item_handler(type_, relations={}):
    def decorator(f):
        @wraps(f)
        @with_params(ItemParams)
        async def wrapper(request, fields=(), expand=()):
            id_ = await f(request)

            kwargs = {}
            if fields:
                kwargs['_source'] = ','.join(fields)

            try:
                response = await elastic.get(
                    ELASTICSEARCH_INDEX, id_, type_, **kwargs)
            except aioes.NotFoundError:
                raise web.HTTPNotFound()

            item = simplify_item(response)

            for related_field in expand:
                doc_type, subfields = relations[related_field]
                if not fields or related_field in fields:
                    item = (await expand_related_items(
                        [item], related_field, doc_type, subfields))[0]

            return web.Response(
                text=json.dumps(item, ensure_ascii=False),
                content_type='application/json',
            )
        return wrapper
    return decorator


def list_handler(type_=None, relations={}):
    def decorator(f):
        @wraps(f)
        @with_params(ListParams)
        async def wrapper(request, page=1, page_size=20, fields=(), expand=()):
            query = await f(request)

            body = {
                'size': page_size,
                'from': (page - 1) * page_size,
                'query': query,
            }
            if fields:
                body['_source'] = fields

            response = await elastic.search(ELASTICSEARCH_INDEX, type_, body)
            hits = response['hits']

            took = response['took']
            count = hits['total']
            items = list(map(simplify_item, hits['hits']))
            previous = get_previous_page_uri(request, page, page_size)
            next_ = get_next_page_uri(request, page, page_size, count)

            for related_field in expand:
                doc_type, subfields = relations[related_field]
                if not fields or related_field in fields:
                    items = await expand_related_items(
                        items, related_field, doc_type, subfields)

            return web.Response(
                text=json.dumps({
                    'count': count,
                    'items': items,
                    'took': took,
                    'previous': previous,
                    'next': next_,
                }, ensure_ascii=False),
                content_type='application/json',
            )
        return wrapper
    return decorator


def get_previous_page_uri(request, page, page_size):
    if page > 2:
        return build_uri(request.path, request.query_string, page=page - 1)
    elif page == 2:
        return build_uri(request.path, request.query_string, page=None)
    else:
        return None


def get_next_page_uri(request, page, page_size, count):
    if page < ceil(count / page_size):
        return build_uri(request.path, request.query_string, page=page + 1)
    else:
        return None


async def expand_related_items(item_list, field, doc_type, subfields):
    id_list = list(compact(item.get(field) for item in item_list))
    if not id_list:
        return item_list

    response = await elastic.mget(
        {'ids': id_list},
        ELASTICSEARCH_INDEX,
        doc_type,
        _source=','.join(subfields)
    )
    related_items = {
        item['id']: item for item in
        map(simplify_item, response['docs'])
        if item is not None
    }
    for item in item_list:
        if field in item:
            item[field] = related_items.get(item[field])

    return item_list


def simplify_item(hit):
    if 'found' in hit and not hit['found']:
        return None

    simple = hit['_source']
    simple['id'] = int(hit['_id'])  # our ids are integers
    simple['type'] = hit['_type']
    if 'highlights' in hit:
        simple['highlights'] = hit['highlights']
    return simple


def compact(iterable):
    return filter(None, iterable)


def build_uri(path, query_string, **params):
    query = parse_qs(query_string)
    for k, v in params.items():
        if v is None and k in query:
            del query[k]
        elif v is not None:
            query[k] = v
    new_qs = urlencode(query, True)
    return '{}?{}'.format(path, new_qs) if new_qs else path
