# To demo:
# ./demo.sh

import os

from flask import Flask
import woodchipper
from woodchipper.http.flask import WoodchipperFlask
from woodchipper.configs import DevLogToStdout

os.environ["WOODCHIPPER_KEY_PREFIX"] = "tkl"

woodchipper.configure(
    config=DevLogToStdout,
    facilities={
        "app": "INFO"
    }
)

logger = woodchipper.get_logger(__name__)

app = Flask(__name__)
WoodchipperFlask(app).chipperize()


@app.route("/")
def hello():
    logger.info("Responding.")
    return "<p>Hello, world!</p>\n"
