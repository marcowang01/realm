import pathlib

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

volume = SharedVolume().persist("aws-cache-vol")
image = Image.debian_slim().pip_install(
    "boto3"
)
stub = Stub(
    name="example-aws",
    image=image,
)

CACHE_DIR = "/cache"
AWS_DIR = pathlib.Path(CACHE_DIR, "data")

@stub.function(
    shared_volumes={"/cache": volume},
    secrets=[Secret.from_name("mw01-aws-secret")]
)
def read_s3_file():
    import boto3

    s3 = boto3.client("s3")
    AWS_DIR.mkdir(parents=True, exist_ok=True) # make directory (if not already exists)
    s3.download_file(
        Bucket="instruct-db", Key="data/alpaca_small.json", Filename=f"{AWS_DIR}/small.json"
    )
    # response = s3.get_object(Bucket=bucket, Key=key)
    # contents = response["Body"].read()
    # return contents.decode("utf-8")


@stub.local_entrypoint()
def main():
    # print(read_s3_file("mw01-aws-bucket", "mw01-aws-key"))
    read_s3_file.call()
    