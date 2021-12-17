import json

import woodchipper
import sqlalchemy

from flask import Flask, Response
from woodchipper.http.aws_lambda import WoodchipperLambda
from woodchipper.http.flask import WoodchipperFlask
from woodchipper.context import LoggingContext
from woodchipper.monitors.sqlalchemy import SQLAlchemyMonitor

import demo.settings

engine = sqlalchemy.create_engine("sqlite:///:memory:")


app = Flask(__name__)


WoodchipperFlask(app).chipperize()
app.wsgi_app = WoodchipperLambda(app.wsgi_app)


woodchipper.configure(**demo.settings.logging_config)
logger = woodchipper.get_logger(__name__)


def connect(sa_monitor):
    sa_monitor.engine = engine


SQLAlchemyMonitor.instance_setup_cb = connect


@app.route("/")
def hello_world():
    logger.info("Hello World Woodchipper")
    return {"msg": "Hello Woodchipper!"}


@app.route("/error")
def trigger_error():
    try:
        1 / 0
    except Exception as e:
        logger.error("Error Exception", exc_info=e)
        return Response(json.dumps({"msg": "Error"}), status=500, mimetype="application/json")

    return {"msg": "Success"}


@app.route("/context")
def set_context():
    with LoggingContext(dict(woodchipper_added_context="Hello from Woodchipper")):
        logger.info("Test Log Context")
        return {"msg": "Testing Log Context"}


@app.route("/sql-event")
def sql_event():
    logger = woodchipper.get_logger(__name__)
    with LoggingContext({"test": "sqlalchemy"}):
        with engine.connect() as conn:
            rows = conn.execute("SELECT 1")
            row = rows.fetchone()
            logger.info("SQL result.", row=row)
            return Response(json.dumps({"msg": f"SQL Result {row}"}), status=201, mimetype="application/json")


if __name__ == "__main__":
    app.run()
