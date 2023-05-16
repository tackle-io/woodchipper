import ast
from unittest.mock import patch

from fastapi import FastAPI, testclient
from fastapi.testclient import TestClient

import woodchipper
from woodchipper.configs import DevLogToStdout
from woodchipper.context import LoggingContext, logging_ctx
from woodchipper.http.fastapi import WoodchipperFastAPI

app = FastAPI()
WoodchipperFastAPI(app).chipperize()
client = TestClient(app)

woodchipper.configure(
    config=DevLogToStdout,
    facilities={"": "INFO"},
)


@app.get("/")
def hello_world():
    with LoggingContext(testvar="testval"):
        return logging_ctx.as_dict()


def test_fastapi_with_woodchipper(caplog):
    with patch("woodchipper.context.os.getenv", return_value="woodchip"):
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["woodchip.testvar"] == "testval"
    assert response.json()["http.method"] == "GET"
    assert response.json()["http.header.host"] == "testserver"
    assert response.json()["http.path"] == "http://testserver/"

    # These logs won't be available until after the context has exited and the response as returned
    fastapi_colon_request_exit_log = None
    for log in caplog.records:
        msg = ast.literal_eval(log.message)  # weirdly the log.message is a python dict that is a string
        if msg["event"] == "Exiting context: fastapi:request":
            fastapi_colon_request_exit_log = msg
            break

    assert (
        fastapi_colon_request_exit_log is not None
    ), "An exit message matching the flask:request pattern couldn't be found"
    assert fastapi_colon_request_exit_log["http.response.status_code"] == 200
    assert type(fastapi_colon_request_exit_log["http.response.content_length"]) is int


def test_fastapi_with_woodchipper_adds_query_params():
    query_dict = {
        "key1": "value1",
        "key2": ["val1", "val2", "val3"],  # confirms that multiple params are handled
        "KEY3": "value3",  # confirms that it lowercases qparams
        "key4": "",  # confirms that it can handle empty values
    }
    response = client.get("/", params=query_dict)

    assert response.status_code == 200
    assert response.json()["http.query_param.key1"] == "value1"
    assert response.json()["http.query_param.key2"] == ["val1", "val2", "val3"]
    assert response.json()["http.query_param.key3"] == "value3"
    assert response.json()["http.query_param.key4"] == ""
    assert response.json()["http.path"] == "http://testserver/"  # confirms that querystring isn't included


def test_fastapi_header_blacklist():
    app = FastAPI()
    WoodchipperFastAPI(app, blacklisted_headers=["host"]).chipperize()
    client = testclient.TestClient(app)

    @app.get("/")
    def hello():
        return logging_ctx.as_dict()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["http.header.host"] == "******"


def test_fastapi_gen_id():
    app = FastAPI()
    WoodchipperFastAPI(app, request_id_factory=lambda: "id").chipperize()
    client = testclient.TestClient(app)

    @app.get("/")
    def hello():
        return logging_ctx.as_dict()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["http.id"] == "id"


def test_fastapi_uncaught_error(caplog):
    app = FastAPI()
    WoodchipperFastAPI(app, request_id_factory=lambda: "id").chipperize()
    client = testclient.TestClient(app, raise_server_exceptions=False)

    @app.get("/")
    def hello():
        raise Exception()

    client.get("/")

    # These logs won't be available until after the context has exited and the response as returned
    fastapi_colon_request_exit_log = None
    for log in caplog.records:
        msg = ast.literal_eval(log.message)  # weirdly the log.message is a python dict that is a string
        if msg["event"] == "Exiting context: fastapi:request":
            fastapi_colon_request_exit_log = msg
            break

    assert fastapi_colon_request_exit_log["http.response.status_code"] == 500
