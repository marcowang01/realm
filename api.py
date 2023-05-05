from fastapi import FastAPI, Request
from . import config

from .main import (
    create_and_get_collection,
    peek_collection,
    add_to_collection,
    delete_collection,
)

logger = config.get_logger(__name__)
web_app = FastAPI()

@web_app.post("/api/hello")
async def hello_endpoint(request: Request):
    body = await request.json()
    return {"message": f"hello {body['name']}"}

# create or get collection and persist it to shared volume
@web_app.post("/api/create_and_get_collection")
async def create_and_get_collection_endpoint(request: Request):
    logger.info("creating and getting collection")
    try:
        body = await request.json()
        name = create_and_get_collection(body["name"])
        # FIXME: what if collection is named error? need to send erros better
        if "error" in name:
            return dict(error=f"error creating and getting collection {name}")
        return dict(message=f"created and got collection {name}")
    except Exception as e:
        logger.error(f"error creating and getting collection: {e}")
        return {"error": str(e)}

# get collection and return the first 10
@web_app.post("/api/peek_collection")
async def peek_collection_endpoint(request: Request):
    import json

    logger.info("peeking collection")
    try:
        body = await request.json()
        docs = peek_collection(body["name"])
        # check if docs is a string or a list
        if isinstance(docs, str):
            return dict(error=f"error peeking collection: {docs}")
        texts = json.dumps(docs["message"], indent=None, separators=(',', ': '), sort_keys=True, ensure_ascii=False)
        return dict(message=texts)
    except Exception as e:
        logger.error(f"error peeking collection: {e}")
        return {"error": str(e)}

# add to collection
@web_app.post("/api/add_to_collection")
async def add_to_collection_endpoint(request: Request):
    logger.info("adding to collection")
    try:
        body = await request.json()
        name = add_to_collection(body["name"], body["documents"])
        if "error" in name:
            return dict(error=f"error adding to collection:: {name}")
        return dict(message=f"added to collection {name}")
    except Exception as e:
        logger.error(f"error adding to collection: {e}")
        return {"error": str(e)}

# delete collection
@web_app.post("/api/delete_collection")
async def delete_collection_endpoint(request: Request):
    logger.info("deleting collection")
    try:
        body = await request.json()
        name = delete_collection(body["name"])
        if "error" in name:
            return dict(error=f"error deleting collection: {name}")
        return dict(message=f"deleted collection {name}")
    except Exception as e:
        logger.error(f"error deleting collection: {e}")
        return {"error": str(e)}
