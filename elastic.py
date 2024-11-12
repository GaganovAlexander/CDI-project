import json

from elasticsearch import Elasticsearch

from configs import ELASTIC_URL, ELASTIC_USER, ELASTIC_PASSWORD
from preprocessing_text import preprocess_text


es = Elasticsearch(
    ELASTIC_URL,
    basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
    verify_certs=True
)
if not es.ping():
    raise Exception("Не удалось подключиться к Elasticsearch.")


index_name = "documents"
mappings = {
    "mappings": {
        "properties": {
            "document_name": {
                "type": "text"
            },
            "page_number": {
                "type": "integer"
            },
            "paragraph_number": {
                "type": "integer"
            },
            "text": {
                "type": "text"
            },
            "lemmatized_text": {
                "type": "text"
            },
            "bbox": {
                "type": "float"
            }
        }
    }
}

if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=mappings)

def add_doc(doc_path: str):
    with open(doc_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    total_docs = len(documents)
    
    for i, doc in enumerate(documents):
        doc["lemmatized_text"] = preprocess_text(doc['text'])
        es.index(index=index_name, document=doc)
        
        yield int((i + 1) / total_docs * 100)


def process_query(user_query: str):
    query = {
        "query": {
            "match": {
                "lemmatized_text": {
                    "query": preprocess_text(user_query),
                    "minimum_should_match": "80%"
                } 
            }
        }
    }
    response = es.search(index=index_name, body=query)

    return [{
            'score': hit['_score'],
            'document_name': hit['_source']['document_name'],
            'page_number': hit['_source']['page_number'],
            'paragraph_number': hit['_source']['paragraph_number'],
            'bbox': hit['_source']['bbox'],
            'text': hit['_source']['text']
        } for hit in response['hits']['hits']]
