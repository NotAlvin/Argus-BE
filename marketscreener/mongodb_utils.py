from utils.config import DATABASE_CONNECTION_URL, DB_NAME
from pymongo import MongoClient, collection


def get_db_client() -> MongoClient:
    return MongoClient(DATABASE_CONNECTION_URL)


def get_db_collection(
        db_name: str,
        collection_name: str
        ) -> collection.Collection:
    client = get_db_client()
    return client[db_name][collection_name]


def get_db_client_and_collection(
        db_name: str, 
        collection_name: str
        ) -> tuple[MongoClient, collection.Collection]:
    client = get_db_client()
    collection = get_db_collection(db_name, collection_name)
    return client, collection


def search_by_regex(collection_name: str, search_term: str):
    _, collection = get_db_client_and_collection(DB_NAME, collection_name)
    return collection.find({"name": {"$regex": search_term, "$options": "i"}})


def search_db(collection_name: str, search_term: str):
    """
    Search the specified collection for the searchterm and return options a user can select from in a drop-down.  
    Include a prefix in the id to be able to identify the result originating from the database.

    Args:
        collection_name (str): The name of the collection to search in.
        searchterm (str): The search term to check for.
    Returns:
        A list of unique tuples of results found in the specified collection.
    """
    res = search_by_regex(collection_name, search_term)
    options_with_duplicates = [
        (
            s["name"]
        ) for s in res]
    return list(dict.fromkeys(options_with_duplicates))