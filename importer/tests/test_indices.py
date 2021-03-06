import asyncio
from unittest import TestCase

from importer.connections import connect_to_elasticsearch
from importer.indices import IndexPaginator
from importer.utils import run_sync


class IndexPaginatorTestCase(TestCase):
    index_name = 'test'

    @run_sync
    async def setUp(self):
        self.elastic = await connect_to_elasticsearch()
        await self.elastic.indices.create(self.index_name)

    @run_sync
    async def tearDown(self):
        await self.elastic.indices.delete(self.index_name)
        self.elastic.close()

    @run_sync
    async def test_returns_all_items(self):
        test_type = 'my_document'
        test_items = [
            {'field': 'one'},
            {'field': 'two'},
            {'field': 'three'},
        ]

        await asyncio.wait([
            self.elastic.index(self.index_name, test_type, item)
            for item in test_items
        ])
        await self.elastic.indices.refresh(self.index_name)

        result_items = []
        async for page in IndexPaginator(self.elastic, self.index_name, size=2):
            for hit in page:
                result_items.append(hit['_source'])

        self.assertEqual(len(result_items), 3)
        self.assertTrue(all(item in result_items for item in test_items))
