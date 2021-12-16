import woodchipper
import sqlalchemy

from flask import Flask, Response
from woodchipper.configs import JSONLogToStdout
from woodchipper.http.flask import WoodchipperFlask
from woodchipper.http.lambda import WoodchipperLambda
from woodchipper.context import LoggingContext
from woodchipper.monitors.sqlalchemy import SQLAlchemyMonitor

engine = sqlalchemy.create_engine("sqlite:///:memory:")


app = Flask(__name__)
WoodchipperFlask(app).chipperize()
app.wsgi_app = WoodchipperLambda(app.wsgi_app)
woodchipper.configure(config=JSONLogToStdout, facilities={"": "INFO"}, monitors=[SQLAlchemyMonitor])
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
        1/0
    except Exception as e:
        logger.error("Error Exception", exc_info=e)
        return Response("Error", status=500)

    return Response("Success", status=201)

@app.route("/context")
def set_context():
    with LoggingContext(dict(
        woodchipper_added_context="Hello from Woodchipper"
    )):
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
            return Response(f"SQL Result {row}", status=201)


if __name__ == "__main__":
    app.run()
