from datetime import datetime

from marshmallow import Schema, fields

from ..helpers import list_handler, with_params

from .score import get_default_score_functions
from .events import EXPANDABLE_RELATIONS


__all__ = ['search']


class SearchParams(Schema):
    q = fields.String(required=True)
    location = fields.String()
    include_past = fields.Boolean()


@list_handler(relations=EXPANDABLE_RELATIONS)
@with_params(SearchParams)
async def search(request, q, location=None, include_past=False):
    filters = []

    if location:
        filters.append({'term': {'location': location}})

    if not include_past:
        now = datetime.now().isoformat()
        filters.append({
            'bool': {
                'should': [
                    {'range': {'end': {'gte': now}}},
                    {'missing': {'field': 'end'}}
                ]
            }
        })

    return {
        'function_score': {
            'query': {'bool': {
                'must': [
                    {'multi_match': {
                        'query': q,
                        'type': 'phrase',
                        'fields': [
                            'name.ngram',
                            'name.text',
                            'full_name.ngram',
                            'full_name.text'
                        ],
                    }},
                ],
                'filter': filters,
                'should': [
                    {'term': {'_type': 'place'}},
                    {'term': {'is_for_kids': False}},
                ],
            }},
            'functions': get_default_score_functions()
        }
    }
