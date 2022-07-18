import pytest
import connexion
import sys


@pytest.fixture(scope='class')
def api():
    sys.path.append('src')

    from model import db

    options = {"swagger_ui": False}
    app = connexion.FlaskApp(
        __name__, specification_dir='../../src/api/', options=options)

    app.add_api('openapi-spec.yml', validate_responses=True)

    app = app.app

    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    with app.test_client() as c:
        yield (c, app)

    sys.path.remove('src')
