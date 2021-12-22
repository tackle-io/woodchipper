# To demo:
# python demo.py

import os

import woodchipper
from woodchipper.configs import DevLogToStdout
from woodchipper.context import LoggingContext
from woodchipper.decorator import arg_logger

os.environ["WOODCHIPPER_KEY_PREFIX"] = "tkl"

woodchipper.configure(config=DevLogToStdout, facilities={"": "INFO"})

logger = woodchipper.get_logger(__name__)


@arg_logger(vendor="product.vendor")
def decorated_func(product: dict):
    logger.info("Decorated.")


def ctx_func(product: dict):
    with LoggingContext(dict(vendor=product["vendor"])):
        logger.info("Context one.")
        with LoggingContext(dict(product=product["id"])):
            logger.info("Context two.")
        logger.info("Context three.")
    logger.info("Context four.")


def demo():
    product = dict(vendor="DEMOVENDOR", id="DEMOPRODUCT")
    decorated_func(product)
    ctx_func(product)


if __name__ == "__main__":
    demo()
