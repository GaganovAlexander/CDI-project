from os import environ

from dotenv import find_dotenv, load_dotenv


# Constants from dotenv
load_dotenv(find_dotenv(), override=True)
ELASTIC_URL = environ.get("ELASTIC_URL")
ELASTIC_USER = environ.get("ELASTIC_USER")
ELASTIC_PASSWORD = environ.get("ELASTIC_PASSWORD")
REDIS_PORT = environ.get("REDIS_PORT")

# Quart constants
UPLOAD_FOLDER = "pdfs"
MAX_CONTENT_LENGTH = 1024**2 * 20

# Elasticsearch constants
INDEX_NAME = "documents"
MAPPINGS = {
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