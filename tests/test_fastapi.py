import ast
import logging
from unittest.mock import patch

import pytest
from fastapi import FastAPI, testclient
from fastapi.testclient import TestClient

import woodchipper
from woodchipper.configs import DevLogToStdout
from woodchipper.context import LoggingContext, logging_ctx
from woodchipper.http.fastapi import WoodchipperFastAPI


@pytest.fixture
def app():
    app = FastAPI()
    WoodchipperFastAPI(app).chipperize()

    @app.get("/foo")
    def hello_world():
        with LoggingContext(testvar="testval"):
            return logging_ctx.as_dict()

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


woodchipper.configure(
    config=DevLogToStdout,
    facilities={"": "INFO"},
)


def test_fastapi_with_woodchipper(client, caplog):
    caplog.set_level(logging.DEBUG)
    with patch.dict("woodchipper.context.os.environ", WOODCHIPPER_KEY_PREFIX="woodchip"):
        response = client.get("/foo")

    assert response.status_code == 200
    assert response.json()["woodchip.testvar"] == "testval"
    assert response.json()["http.method"] == "GET"
    assert response.json()["http.header.host"] == "testserver"
    assert response.json()["http.path"] == "http://testserver/foo"

    # These logs won't be available until after the context has exited and the response as returned
    fastapi_colon_request_enter_log = None
    fastapi_colon_request_exit_log = None
    for log in caplog.records:
        msg = ast.literal_eval(log.message)  # weirdly the log.message is a python dict that is a string
        if msg["event"] == "Entering context: fastapi:request":
            fastapi_colon_request_enter_log = msg

        if msg["event"] == "Exiting context: fastapi:request":
            fastapi_colon_request_exit_log = msg

        if fastapi_colon_request_enter_log and fastapi_colon_request_exit_log:
            break

    assert (
        fastapi_colon_request_enter_log is not None
    ), "An enter message matching the fastapi:request pattern couldn't be found"
    assert (
        fastapi_colon_request_exit_log is not None
    ), "An exit message matching the fastapi:request pattern couldn't be found"
    assert fastapi_colon_request_exit_log["http.response.status_code"] == 200
    assert type(fastapi_colon_request_exit_log["http.response.content_length"]) is int


def test_fastapi_with_woodchipper_adds_query_params(
    client,
):
    query_dict = {
        "key1": "value1",
        "key2": ["val1", "val2", "val3"],  # confirms that multiple params are handled
        "KEY3": "value3",  # confirms that it lowercases qparams
        "key4": "",  # confirms that it can handle empty values
    }
    response = client.get("/foo", params=query_dict)

    assert response.status_code == 200
    assert response.json()["http.query_param.key1"] == "value1"
    assert response.json()["http.query_param.key2"] == ["val1", "val2", "val3"]
    assert response.json()["http.query_param.key3"] == "value3"
    assert response.json()["http.query_param.key4"] == ""
    assert response.json()["http.path"] == "http://testserver/foo"  # confirms that querystring isn't included


def test_fastapi_header_blacklist():
    app = FastAPI()
    WoodchipperFastAPI(app, blacklisted_headers=["host"]).chipperize()
    client = testclient.TestClient(app)

    @app.get("/")
    def hello():
        return logging_ctx.as_dict()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["http.path"] == "http://testserver/"
    assert response.json()["http.header.host"] == "******"


def test_fastapi_gen_id():
    app = FastAPI()
    WoodchipperFastAPI(app, request_id_factory=lambda: "id").chipperize()
    client = testclient.TestClient(app)

    @app.get("/id_gen")
    def hello():
        return logging_ctx.as_dict()

    response = client.get("/id_gen")

    assert response.status_code == 200
    assert response.json()["http.id"] == "id"


def test_fastapi_uncaught_error(caplog):
    caplog.set_level(logging.DEBUG)
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


def test_alternate_installation(caplog):
    caplog.set_level(logging.DEBUG)
    # If users do not want to use chipperize, which overrides the middleware installation order,
    # they can install using the typical FastAPI add_middleware pattern
    app = FastAPI()
    app.add_middleware(WoodchipperFastAPI)

    @app.get("/foo")
    def hello_world():
        with LoggingContext(testvar="testval"):
            return logging_ctx.as_dict()

    client = TestClient(app)

    with patch.dict("woodchipper.context.os.environ", WOODCHIPPER_KEY_PREFIX="woodchip"):
        response = client.get("/foo")

    assert response.status_code == 200
    assert response.json()["woodchip.testvar"] == "testval"
    assert response.json()["http.method"] == "GET"
    assert response.json()["http.header.host"] == "testserver"
    assert response.json()["http.path"] == "http://testserver/foo"

    # These logs won't be available until after the context has exited and the response as returned
    fastapi_colon_request_enter_log = None
    fastapi_colon_request_exit_log = None
    for log in caplog.records:
        msg = ast.literal_eval(log.message)  # weirdly the log.message is a python dict that is a string
        if msg["event"] == "Entering context: fastapi:request":
            fastapi_colon_request_enter_log = msg

        if msg["event"] == "Exiting context: fastapi:request":
            fastapi_colon_request_exit_log = msg

        if fastapi_colon_request_enter_log and fastapi_colon_request_exit_log:
            break

    assert (
        fastapi_colon_request_enter_log is not None
    ), "An enter message matching the fastapi:request pattern couldn't be found"
    assert (
        fastapi_colon_request_exit_log is not None
    ), "An exit message matching the fastapi:request pattern couldn't be found"
    assert fastapi_colon_request_exit_log["http.response.status_code"] == 200
    assert type(fastapi_colon_request_exit_log["http.response.content_length"]) is int
