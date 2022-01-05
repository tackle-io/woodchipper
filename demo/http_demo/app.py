# To demo:
# ./demo.sh

import os

from flask import Flask

import woodchipper
from woodchipper.configs import DevLogToStdout
from woodchipper.http.flask import WoodchipperFlask

os.environ["WOODCHIPPER_KEY_PREFIX"] = "tkl"

woodchipper.configure(config=DevLogToStdout, facilities={"": "INFO"})

logger = woodchipper.get_logger(__name__)

app = Flask(__name__)
WoodchipperFlask(app).chipperize()


@app.route("/")
def hello():
    logger.info("Responding.")
    return "<p>Hello, world!</p>\n"
