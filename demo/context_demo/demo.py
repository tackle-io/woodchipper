# To demo:
# python demo.py

import os

import woodchipper
from woodchipper.configs import DevLogToStdout
from woodchipper.context import LoggingContext

os.environ["WOODCHIPPER_KEY_PREFIX"] = "tkl"

woodchipper.configure(config=DevLogToStdout, facilities={"": "INFO"})

logger = woodchipper.get_logger(__name__)


@LoggingContext(vendor="product.vendor")
def decorated_func(product: dict):
    logger.info("Decorated.")


def ctx_func(product: dict):
    with LoggingContext(vendor=product["vendor"]):
        logger.info("Context one.")
        with LoggingContext(product=product["id"]):
            logger.info("Context two.")
        logger.info("Context three.")
    logger.info("Context four.")


def demo():
    product = dict(vendor="DEMOVENDOR", id="DEMOPRODUCT")
    decorated_func(product)
    ctx_func(product)


if __name__ == "__main__":
    demo()
