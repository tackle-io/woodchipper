import ast
import json
import logging
from unittest.mock import patch
from urllib.parse import urlencode

from flask import Flask

from woodchipper.context import LoggingContext, logging_ctx
from woodchipper.http.flask import WoodchipperFlask

app = Flask(__name__)
WoodchipperFlask(app).chipperize()


@app.route("/")
def hello_world():
    with LoggingContext(testvar="testval"):
        return logging_ctx.as_dict()


def test_flask_with_woodchipper(caplog):
    caplog.set_level(logging.DEBUG)
    with patch.dict("woodchipper.context.os.environ", WOODCHIPPER_KEY_PREFIX="woodchip"):
        with app.test_client() as client:
            response = client.get("/")
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["woodchip.testvar"] == "testval"
    assert response_json["http.method"] == "GET"
    assert response_json["http.header.host"] == "localhost"
    assert response_json["http.path"] == "http://localhost/"

    # These logs won't be available until after the context has exited and the response as returned
    flask_colon_request_enter_log = None
    flask_colon_request_exit_log = None
    for log in caplog.records:
        msg = ast.literal_eval(log.message)  # weirdly the log.message is a python dict that is a string
        if msg["event"] == "Entering context: flask:request":
            flask_colon_request_enter_log = msg

        if msg["event"] == "Exiting context: flask:request":
            flask_colon_request_exit_log = msg

        if flask_colon_request_exit_log and flask_colon_request_exit_log:
            break

    assert (
        flask_colon_request_enter_log is not None
    ), "An exit message matching the flask:request pattern couldn't be found"
    assert (
        flask_colon_request_exit_log is not None
    ), "An exit message matching the flask:request pattern couldn't be found"
    assert flask_colon_request_exit_log["http.response.status_code"] == 200
    assert type(flask_colon_request_exit_log["http.response.content_length"]) is int


@app.route("/raise_unhandled_exception")
def raise_unhandled_exception():
    raise ValueError("oh no!")


def test_flask_raises_unhandled_exception(caplog):
    caplog.set_level(logging.DEBUG)
    with app.test_client() as client:
        response = client.get("/raise_unhandled_exception")
    assert response.status_code == 500

    # These logs won't be available until after the context has exited and the response as returned
    flask_colon_request_enter_log = None
    flask_colon_request_exit_log = None
    for log in caplog.records:
        msg = ast.literal_eval(log.message)  # weirdly the log.message is a python dict that is a string
        if msg["event"] == "Entering context: flask:request":
            flask_colon_request_enter_log = msg

        if msg["event"] == "Exiting context: flask:request":
            flask_colon_request_exit_log = msg

        if flask_colon_request_exit_log and flask_colon_request_exit_log:
            break

    assert (
        flask_colon_request_enter_log is not None
    ), "An exit message matching the flask:request pattern couldn't be found"
    assert (
        flask_colon_request_exit_log is not None
    ), "An exit message matching the flask:request pattern couldn't be found"
    assert flask_colon_request_exit_log["http.response.status_code"] == 500


def test_flask_with_woodchipper_adds_query_params():
    query_dict = {
        "key1": "value1",
        "key2": ["val1", "val2", "val3"],  # confirms that multiple params are handled
        "KEY3": "value3",  # confirms that it lowercases qparams
        "key4": "",  # confirms that it can handle empty values
    }
    encoded = urlencode(query_dict, doseq=True)

    with patch.dict("woodchipper.context.os.environ", WOODCHIPPER_KEY_PREFIX="woodchip"):
        with app.test_client() as client:
            response = client.get("/", query_string=encoded)

    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["http.query_param.key1"] == "value1"
    assert response_json["http.query_param.key2"] == ["val1", "val2", "val3"]
    assert response_json["http.query_param.key3"] == "value3"
    assert response_json["http.query_param.key4"] == ""
    assert response_json["http.path"] == "http://localhost/"  # confirms that querystring isn't included
