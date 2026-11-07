import os
from importlib import import_module

from flask import Flask, request
from werkzeug.wrappers import Response


service = os.getenv("SERVICE_NAME", "C").upper()

modules = {
    "C": "server_c.app",
    "X": "server_x.app",
    "Y": "server_y.app",
}

if service not in modules:
    raise RuntimeError(f"Unknown SERVICE_NAME: {service}")

target_app = import_module(modules[service]).app

app = Flask(__name__)


@app.route("/", defaults={"path": ""}, methods=[
    "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"
])
@app.route("/<path:path>", methods=[
    "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"
])
def dispatch(path):
    return Response.from_app(target_app, request.environ)