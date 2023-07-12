import os
from flask import Flask
from waitress import serve
import logging

UPLOAD_FOLDER = 'C:\\Users\\hleyt\\Desktop\\Morgana Tec\\Python\\Cretal\\files'
ALLOWED_EXTENSIONS = {'txt'}

logger = logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[logging.FileHandler('log.log'), logging.StreamHandler()]
    )
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'cobranzas.sqlite')
    )
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    app.add_url_rule('/', endpoint='auth.login')

    from . import importador
    app.register_blueprint(importador.bp)

    # from . import blog
    # app.register_blueprint(blog.bp)
    # app.add_url_rule('/', endpoint='index')

    return serve(app, listen='*:8080')