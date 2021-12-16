import woodchipper

from flask import Flask
from woodchipper.flask import WoodchipperFlask


app = Flask(__name__)
WoodchipperFlask(app).chipperize()

woodchipper.configure()
logger = woodchipper.get_logger()


@app.route('/')
def hello_world():
    logger.info('Hello World log message')
    return {'msg': 'Hello World'}


if __name__ == '__main__':
    app.run()
