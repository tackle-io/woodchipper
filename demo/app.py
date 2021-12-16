import woodchipper

from flask import Flask
from woodchipper.configs import JSONLogToStdout
from woodchipper.http.flask import WoodchipperFlask

app = Flask(__name__)
WoodchipperFlask(app).chipperize()

woodchipper.configure(config=JSONLogToStdout, facilities={"": "INFO"})
logger = woodchipper.get_logger(__name__)


@app.route('/')
def hello_world():
    logger.info('Hello World Woodchipper')
    return {'msg': 'Hello Woodchipper!'}


if __name__ == '__main__':
    app.run()
