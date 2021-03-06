import asyncio
import aiohttp

from .connections import connect_to_elasticsearch
from .indices import create_new_index, switch_alias_to_index, IndexPaginator
from .importer import import_data
from .kudago import KudaGo
from .settings import ELASTICSEARCH_ALIAS


async def migrate():
    print("Starting migration...")
    elastic = await connect_to_elasticsearch()

    print("Creating new index...")
    index_name = await create_new_index(elastic)

    if await elastic.indices.exists(ELASTICSEARCH_ALIAS):
        print("Reindexing data from previous index...")
        futures = []
        async for page in IndexPaginator(elastic, ELASTICSEARCH_ALIAS):
            actions = []
            for hit in page:
                doc = hit['_source']
                id_ = hit['_id']
                type_ = hit['_type']
                actions.append({'index': {'_id': id_, '_type': type_}})
                actions.append(doc)
            futures.append(asyncio.ensure_future(
                elastic.bulk(actions, index_name)
            ))
        if futures:
            await asyncio.wait(futures)

    print("Switching to new index...")
    await switch_alias_to_index(elastic, ELASTICSEARCH_ALIAS, index_name)

    print("Done.")
    elastic.close()


async def update(since):
    print(
        "Updating events since {}...".format(since)
        if since else "Updating all events..."
    )

    async with aiohttp.ClientSession() as http_client:
        elastic = await connect_to_elasticsearch()
        kudago = KudaGo(http_client)
        await import_data(kudago, elastic, ELASTICSEARCH_ALIAS, since=since)

    print("Done.")
    elastic.close()


async def reimport():
    print("Starting reimport")
    elastic = await connect_to_elasticsearch()

    print("Creating new index...")
    index_name = await create_new_index(elastic)

    print("Importing data...")
    async with aiohttp.ClientSession() as http_client:
        kudago = KudaGo(http_client)
        await import_data(kudago, elastic, index_name)

    print("Switching to new index")
    await switch_alias_to_index(elastic, ELASTICSEARCH_ALIAS, index_name)

    print("Done.")
    elastic.close()
