import asyncio

from elasticsearch import AsyncElasticsearch

from .configs import ELASTIC_URL, ELASTIC_USER, ELASTIC_PASSWORD, INDEX_NAME, MAPPINGS
from .preprocessing_text import preprocess_text


es = AsyncElasticsearch(
    ELASTIC_URL,
    basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
    verify_certs=True
)

async def wait_for_elastic(tries = 10) -> None:
    for _ in range(tries):
        try:
            if await es.ping():
                print("Elasticsearch is ready.")
                return
        except ConnectionError:
            pass
        print("Waiting for Elasticsearch...")
        await asyncio.sleep(5)
    raise TimeoutError("Elasticsearch did not become ready in time.")

async def create_index() -> None:
    exists = await es.indices.exists(index=INDEX_NAME)
    if not exists:
        response = await es.indices.create(index=INDEX_NAME, body=MAPPINGS)
        print(f"Index created: {response}")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

async def add_doc(documents):
    total_docs = len(documents)

    for i, doc in enumerate(documents):
        await es.index(index=INDEX_NAME, document=doc)
        yield int((i + 1) / total_docs * 100)


async def process_query(user_query: str) -> list[dict]:
    query = {
        "query": {
            "match": {
                "lemmatized_text": {
                    "query": await preprocess_text(user_query),
                    "minimum_should_match": "80%"
                }
            }
        }
    }
    response = await es.search(index=INDEX_NAME, body=query)

    return [
        {
            "score": hit["_score"],
            "document_name": hit["_source"]["document_name"],
            "page_number": hit["_source"]["page_number"],
            "paragraph_number": hit["_source"]["paragraph_number"],
            "bbox": hit["_source"]["bbox"],
            "text": hit["_source"]["text"]
        }
        for hit in response["hits"]["hits"]
    ]
