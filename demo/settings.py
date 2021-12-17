import os

from woodchipper.configs import DevLogToStdout, JSONLogToStdout
from woodchipper.monitors.sqlalchemy import SQLAlchemyMonitor

logging_configurations = {
    "development": dict(
        config=DevLogToStdout, facilities={"": "DEBUG", "noisy_subsystem": "INFO"}, monitors=[SQLAlchemyMonitor]
    ),
    "production": dict(
        config=JSONLogToStdout, facilities={"": "INFO", "noisy_subsystem": "WARNING"}, monitors=[SQLAlchemyMonitor]
    ),
}

if os.getenv("FLASK_ENV") == "production":
    logging_config = logging_configurations["production"]
else:
    logging_config = logging_configurations["development"]
