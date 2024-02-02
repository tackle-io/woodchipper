# To demo:
# python demo.py

import os

import woodchipper
from woodchipper.configs import DevLogToStdout
from woodchipper.context import LoggingContext

os.environ["WOODCHIPPER_KEY_PREFIX"] = "tkl"

woodchipper.configure(config=DevLogToStdout, facilities={"": "DEBUG"})

logger = woodchipper.get_logger(__name__)


@LoggingContext(vendor="product.vendor")
def decorated_func(product: dict):
    logger.info("Decorated.")


def ctx_func(product: dict):
    with LoggingContext(vendor=product["vendor"]):
        logger.info("Context one.")
        nested_ctx_func(product)
        logger.info("Context three.")
    logger.info("Context four.")


def nested_ctx_func(product: dict):
    with LoggingContext(product=product["id"]):
        logger.info("Context two.")


def ctx_func_with_log_level(product: dict):
    with LoggingContext(vendor=product["vendor"], _log_level="DEBUG"):
        logger.info("Context one.")
        nested_ctx_func(product)
        logger.info("Context three.")
    logger.info("Context four.")


def demo():
    product = dict(vendor="DEMOVENDOR", id="DEMOPRODUCT")
    decorated_func(product)
    ctx_func(product)
    ctx_func_with_log_level(product)


if __name__ == "__main__":
    demo()
