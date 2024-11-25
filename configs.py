from os import environ

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv(), override=True)

WORKING_DIR = environ.get("WORKING_DIR")
ELASTIC_URL = environ.get("ELASTIC_URL")
ELASTIC_USER = environ.get("ELASTIC_USER")
ELASTIC_PASSWORD = environ.get("ELASTIC_PASSWORD")