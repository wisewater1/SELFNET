from io import BytesIO
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults

from selfnet.ui import create_app


def call_app(app, method="GET", path="/", data=None):
    environ = {}
    setup_testing_defaults(environ)
    environ["REQUEST_METHOD"] = method
    environ["PATH_INFO"] = path
    if data is not None:
        encoded = urlencode(data).encode()
        environ["CONTENT_LENGTH"] = str(len(encoded))
        environ["wsgi.input"] = BytesIO(encoded)
    else:
        environ["CONTENT_LENGTH"] = "0"
        environ["wsgi.input"] = BytesIO()

    result = {}

    def start_response(status, headers):
        result["status"] = status
        result["headers"] = dict(headers)

    body_parts = app(environ, start_response)
    body = b"".join(body_parts)
    return result["status"], result.get("headers", {}), body


def test_index_renders():
    app = create_app()
    status, headers, body = call_app(app)
    assert status.startswith("200")
    assert b"SELFNet Simulation Console" in body
    assert headers["Content-Type"].startswith("text/html")


def test_identity_and_ubi_flow():
    app = create_app()

    status, _, _ = call_app(app, method="POST", path="/add-trusted-source", data={"source_id": "validator-1"})
    assert status.startswith("303")

    status, _, _ = call_app(
        app,
        method="POST",
        path="/register-identity",
        data={"identifier": "alice", "attestations": "validator-1"},
    )
    assert status.startswith("303")

    status, _, _ = call_app(app, method="POST", path="/run-ubi", data={"epoch": "0"})
    assert status.startswith("303")

    status, _, body = call_app(app)
    assert status.startswith("200")
    assert b"alice" in body
    assert b"Distributed UBI" in body
