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

# TODO: basic features
# add a input text box for query
# add function for query, count, and reset
# TODO: add function to delete shared volume
# pings front end every 5 minutes to keep backend alive (using last request time)
# have client ping with heartbeat every 5 minutes to keep frontend alive (using last request time)
# TODO: potentially parallelize adding the emebddings !
# TODO: security
# have log in system for users to prevent spamming. 
# add auth to the api end points
# overall need more security (daily quotas?, google form for review)
# have them provide openai key?
# TODO: performance
# cache the client object of the database (30 seconds to peek)

logger = config.get_logger(__name__)
volume = SharedVolume().persist("chroma-cache-vol")
# volume = SharedVolume()
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
    import boto3
    from botocore.exceptions import ClientError
    import zipfile
    import traceback

    # check if chroma directory exists
    bucket_name = ""
    if not config.CHROMA_DIR.exists() or not config.INDEX_DIR.exists():
        logger.info(f"fetching {config.ZIP_FILE} from {bucket_name} bucket.")
        chroma_dir = str(config.CHROMA_DIR)
        config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        # delete everything inside CHROMA_DIR and the directory itself
        for file in os.listdir(chroma_dir):
            file_path = os.path.join(chroma_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"error deleting {file_path}: {e}")
                continue
        try:
            os.rmdir(chroma_dir)
            logger.info(f"{chroma_dir} was deleted")
        except Exception as e:
            logger.error(f"error deleting {chroma_dir}: {e}")

        bucket_name = os.environ['BUCKET_NAME']
        key = config.S3_KEY
        file_name = config.ZIP_FILE

        try:
            s3 = boto3.client('s3')
            s3.download_file(bucket_name, key, file_name)
            config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(file_name, 'r') as zip_ref:
                zip_ref.extractall(str(config.CHROMA_DIR))
            os.remove(file_name)
            logger.info(f"Downloaded and extracted {file_name} from {bucket_name} bucket.")
        except ClientError as e:
            logger.error(f"Could not download file from S3 bucket: {e}")
            logger.error(traceback.format_exc())

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
        logger.error(traceback.format_exc())
        return f"error: {e}"


# get collection and return the first 10 items
@stub.function(shared_volumes={config.CACHE_DIR: volume})
def peek_collection(name):
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    import traceback


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
        logger.error(traceback.format_exc())
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
        logger.info(f"adding to collection {name} locally...")

        num_chunks = (len(documents)-1) // config.CHUNK_SIZE + 1
        while num_chunks > 0:
            chunk_docs = []
            if len(documents) < config.CHUNK_SIZE:
                chunk_docs = documents
            else:
                chunk_docs = documents[:config.CHUNK_SIZE]
            chunk_meta = [{"source": "alpaca"} for i in range(len(chunk_docs))]
            chunk_ids = [f'id{j}' for j in range(len(chunk_docs))]
            collection.add(
                documents=[str(doc) for doc in chunk_docs],
                metadatas=chunk_meta,
                ids=chunk_ids
            )
            if len(documents) < config.CHUNK_SIZE:
                break
            documents = documents[config.CHUNK_SIZE:]
            num_chunks -= 1
            logger.info(f"added {len(chunk_docs)} documents to collection {name}, {num_chunks} chunks left")
        
        logger.info(f"added to collection {name} locally")
        # check if the INDEX_DIR exists before sending data to s3 and timeout within 60 seconds if not found
        timeout = 60
        while not config.INDEX_DIR.exists() and timeout > 0:
            logger.info(f"waiting for {config.INDEX_DIR} to be mounted")
            timeout -= 1
            time.sleep(1)
        if timeout == 0:
            raise Exception(f"Index directory not found in {timeout} seconds")        
        logger.info(f"found {config.INDEX_DIR}, ready to send data to s3")

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
                    # writing the relative path from starting from CHROMA_DIR into the zip
                    zip.write(os.path.join(root, file), arcname=os.path.relpath(os.path.join(root, file), chroma_dir))

        # upload zip file to S3 bucket
        with open(zip_file, "rb") as f:
            # fileobj, bucket, key
            s3.upload_fileobj(f, bucket_name, config.S3_KEY)
            logger.info(f"{zip_file} has been uploaded to {bucket_name} bucket.")

        os.remove(config.ZIP_FILE)
        logger.info(f"Deleted {config.ZIP_FILE}")

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
    import traceback

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
        logger.error(traceback.format_exc())
        return "error: {e}"
