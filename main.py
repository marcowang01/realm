import dataclasses
import datetime
import json
import pathlib
import os
from typing import Iterator, Tuple

from modal import (
    Dict,
    Image,
    Mount,
    Period,
    Secret,
    SharedVolume,
    Stub,
    asgi_app,
)

from . import config

# TODO: add a input text box for query
# TODO: add function for query, count, and reset
# TODO: hook up to S3 or somehow do dynamo

logger = config.get_logger(__name__)
volume = SharedVolume().persist("chroma-cache-vol")
# define container image
app_image = (
    Image.debian_slim()
    .pip_install(
        "chromadb",
        "langchain",
        "openai",
        "boto3",
    )
)

stub = Stub(
    "instructdb",
    image=app_image,
    secrets=[Secret.from_name("mw01-openai-secret"), Secret.from_name("mw01-aws-secret")],
)

# deploys the frontend static files and also the fast API server
@stub.function(
    mounts=[Mount.from_local_dir(config.ASSETS_PATH, remote_path="/")],
    shared_volumes={config.CACHE_DIR: volume},
    keep_warm=2,
)
@asgi_app()
def fastapi_app():
    import fastapi.staticfiles

    from .api import web_app

    web_app.mount(
        "/", fastapi.staticfiles.StaticFiles(directory="/", html=True)
    )

    return web_app

# create or get collection and persist it to shared volume
@stub.function(shared_volumes={config.CACHE_DIR: volume})
def create_and_get_collection(name):
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    # from langchain.vectorstores import Chroma
    # from langchain.embeddings import OpenAIEmbeddings

    chroma_dir = str(config.CHROMA_DIR)
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=chroma_dir,
    ))
    logger.info(f"created client {client}")

    try:
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ["OPENAI_API_KEY"],
            model_name="text-embedding-ada-002"
        )
        collection = client.get_or_create_collection(
            name=name,
            embedding_function=openai_ef,
        )
        # collection.persist()
        logger.info(f"created and got collection {name}")
        return collection.name
    except Exception as e:
        logger.error(f"error creating and getting collection: {e}")
        return f"error: {e}"


# get collection and return the first 10 items
@stub.function(shared_volumes={config.CACHE_DIR: volume})
def peek_collection(name):
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    chroma_dir = str(config.CHROMA_DIR)
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=chroma_dir,
    ))
    logger.info(f"created client {client}")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-ada-002"
    )
    try:
        collection = client.get_collection(
            name=name,
            embedding_function=openai_ef,
        )
        logger.info(f"peeking collection {name}...")
        return dict(message=collection.peek())
    except Exception as e:
        logger.error(f"error getting collection: {e}")
        return "error: {e}"

# get collection and return the name
@stub.function(shared_volumes={config.CACHE_DIR: volume})
def add_to_collection(name, documents):
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    import boto3
    import zipfile
    import traceback
    import os

    chroma_dir = str(config.CHROMA_DIR)
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=chroma_dir,
    ))
    logger.info(f"created client {client}")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-ada-002"
    )
    try:
        # add new documents to collection inside shared volume
        collection = client.get_collection(
            name=name,
            embedding_function=openai_ef,
        )
        logger.info(f"adding to collection {name}...")
        # collection.add(
        #     documents=[str(doc) for doc in documents],
        #     metadatas=[{"source": "alpaca"} for i in range(len(documents))],
        #     ids=[f'id{i}' for i in range(len(documents))]
        # )
        logger.info(f"added to collection {name} locally")
        
        # delete all files and directories from S3 bucket before uploading new files
        s3 = boto3.client('s3')
        bucket_name = os.environ["BUCKET_NAME"]
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            delete_keys = [{'Key': k['Key']} for k in response['Contents']]
            s3.delete_objects(Bucket=bucket_name, Delete={'Objects': delete_keys})
            logger.info(f"deleted all files and directories from {bucket_name} bucket")

        zip_file = config.ZIP_FILE
        # create a zip file of CHROMA_DIR
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zip:
            for root, dirs, files in os.walk(chroma_dir):
                for file in files:
                    zip.write(os.path.join(root, file))

        # upload zip file to S3 bucket
        with open(zip_file, "rb") as f:
            # fileobj, bucket, key
            s3.upload_fileobj(f, bucket_name, config.S3_KEY)
            logger.info(f"{zip_file} has been uploaded to {bucket_name} bucket.")

        # config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        # config.INDEX_DIR.mkdir(parents=True, exist_ok=True)

        return collection.name
    except Exception as e:
        logger.error(f"error adding to collection: {e}")
        logger.error(traceback.format_exc())
        return "error: {e}"

# delete the collection by name
@stub.function(shared_volumes={config.CACHE_DIR: volume})
def delete_collection(name):
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    chroma_dir = str(config.CHROMA_DIR)
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=chroma_dir,
    ))
    logger.info(f"created client {client}")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-ada-002"
    )
    try:
        collection = client.get_collection(
            name=name,
            embedding_function=openai_ef,
        )
        logger.info(f"deleting collection {name}...")
        collection.delete()
        client.reset()
        return collection.name
    except Exception as e:
        logger.error(f"error deleting collection: {e}")
        return "error: {e}"
