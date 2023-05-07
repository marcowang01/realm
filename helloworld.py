# # Hello, world!
#
# This is a trivial example of a Modal function, but it illustrates a few features:
#
# * You can print things to stdout and stderr.
# * You can return data.
# * You can map over a function.
#
# ## Import Modal and define the app
#
# Let's start with the top level imports.
# You need to import Modal and define the app.
# A stub is an object that defines everything that will be run.

# import sys

# import modal

# stub = modal.Stub("example-hello-world")

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

# volume = SharedVolume().persist("aws-cache-vol")
# image = Image.debian_slim().pip_install(
#     "boto3",
# )
# stub = Stub(
#     name="example-aws",
#     image=image,
# )
stub = Stub("example-aws")



# ## Defining a function
#
# Here we define a Modal function using the `modal.function` decorator.
# The body of the function will automatically be run remotely.
# This particular function is pretty silly: it just prints "hello"
# and "world" alternatingly to standard out and standard error.


# @stub.function()
@stub.function(
    # shared_volumes={"/cache": volume},
    # secret=[Secret.from_name("mw01-aws-secret")]
)
def f(i):
    if i % 2 == 0:
        print("hello", i)
    else:
        print("world", i, file=sys.stderr)

    return i * i


# ## Running it
#
# Finally, let's actually invoke it.
# We put this invocation code inside a `@stub.local_entrypoint()`.
# This is because this module will be imported in the cloud, and we don't want
# this code to be executed a second time in the cloud.
#
# Run `modal run hello_world.py` and the `@stub.local_entrypoint()` decorator will handle
# starting the Modal app and then executing the wrapped function body.
#
# Inside the `main()` function body, we are calling the function `f` in three ways:
#
# 1  As a simple local call, `f(1000)`
# 2. As a simple *remote* call `f.call(1000)`
# 3. By mapping over the integers `0..19`


@stub.local_entrypoint()
def main():
    # Call the function locally.
    print(f(1000))

    # Call the function remotely.
    print(f.call(1000))

    # Parallel map.
    total = 0
    for ret in f.map(range(20)):
        total += ret

    print(total)
