import sqlalchemy

import woodchipper
from woodchipper.configs import DevLogToStdout
from woodchipper.context import LoggingContext
from woodchipper.monitors.sqlalchemy import SQLAlchemyMonitor

engine = sqlalchemy.create_engine("sqlite:///:memory:")


def connect(sa_monitor):
    sa_monitor.engine = engine


SQLAlchemyMonitor.instance_setup_cb = connect
woodchipper.configure(config=DevLogToStdout, facilities={"": "INFO"}, monitors=[SQLAlchemyMonitor])


def test_sqlalchemy():
    logger = woodchipper.get_logger(__name__)
    with LoggingContext(test="sqlalchemy"):
        with engine.connect() as conn:
            rows = conn.execute("SELECT 1")
            logger.info("SQL result.", row=rows.fetchone())
    # FIXME: Actually test something here
