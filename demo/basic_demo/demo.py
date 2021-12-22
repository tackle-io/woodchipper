# To demo:
# python demo.py

import woodchipper
from woodchipper.configs import DevLogToStdout

woodchipper.configure(config=DevLogToStdout, facilities={"": "INFO"})

logger = woodchipper.get_logger(__name__)


def demo():
    logger.info("Something happened.")


if __name__ == "__main__":
    demo()
