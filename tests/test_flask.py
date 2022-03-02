import json
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


def test_flask_with_woodchipper():
    with patch("woodchipper.context.os.getenv", return_value="woodchip"):
        with app.test_client() as client:
            response = client.get("/")
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["woodchip.testvar"] == "testval"
    assert response_json["http.method"] == "GET"
    assert response_json["http.header.host"] == "localhost"
    assert response_json["http.path"] == "http://localhost/"


def test_flask_with_woodchipper_adds_query_params():
    query_dict = {
        "key1": "value1",
        "key2": ["val1", "val2", "val3"],  # confirms that multiple params are handled
        "KEY3": "value3",  # confirms that it lowercases qparams
        "key4": "",  # confirms that it can handle empty values
    }
    encoded = urlencode(query_dict, doseq=True)

    with patch("woodchipper.context.os.getenv", return_value="woodchip"):
        with app.test_client() as client:
            response = client.get("/", query_string=encoded)

    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["http.query_param.key1"] == "value1"
    assert response_json["http.query_param.key2"] == ["val1", "val2", "val3"]
    assert response_json["http.query_param.key3"] == "value3"
    assert response_json["http.query_param.key4"] == ""
    assert response_json["http.path"] == "http://localhost/"  # confirms that querystring isn't included
