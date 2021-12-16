import json
from unittest.mock import patch

from flask import Flask

from woodchipper.context import LoggingContext, logging_ctx
from woodchipper.flask import WoodchipperFlask

app = Flask(__name__)
WoodchipperFlask(app).chipperize()


@app.route("/")
def hello_world():
    with LoggingContext({"testvar": "testval"}):
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
