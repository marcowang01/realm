from fastapi import FastAPI, Request
from . import config

logger = config.get_logger(__name__)
web_app = FastAPI()

@web_app.post("/api/hello")
async def hello_endpoint(request: Request):
    name = await request.json()
    return {"message": f"hello {name['name']}"}

# create collection and persist it to shared volume