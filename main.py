import dataclasses
import datetime
import json
import pathlib
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

logger = config.get_logger(__name__)
volume = SharedVolume().persist("chroma-cache-vol")
# define container image
app_image = (
    Image.debian_slim()
    .pip_install(
        "chroma",
        "langchain",
        "openai",
    )
)

stub = Stub(
    "instructdb",
    image=app_image,
    secrets=[Secret.from_name("mw01-openai-secret")],
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

# create collection and persist it to shared volume
@stub.function(shared_volumes={config.CACHE_DIR: volume})
def create_collection(name):
    import chroma

    chroma_dir = config.CHROMA_DIR
    chroma_client = chromadb.Client()

    collection = chroma.Collection(name)
    collection.persist()
    return collection.name
