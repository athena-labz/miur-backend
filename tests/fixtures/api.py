import pytest
import connexion
import sys
import os


@pytest.fixture(scope="class")
def api():
    sys.path.append("src")

    from model import db

    os.environ = {
        **os.environ,
        "BLOCKFROST_PROJECT_ID": "<project_id>",
        "BLOCKFROST_BASE_URL": "<project_base_url>",
        "NETWORK_MODE": "testnet",
        "SCRIPT_PATH": "./script/script.plutus",
        "FUNDING_ASSET": "e77c6c0681f310334a286275645deb8df4f57a50bd8c930643e75c117374616b65",
    }

    options = {"swagger_ui": False}
    app = connexion.FlaskApp(
        __name__, specification_dir="../../src/api/", options=options
    )

    app.add_api("openapi-spec.yml", validate_responses=True)

    app = app.app

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    with app.test_client() as c:
        yield (c, app)

    sys.path.remove("src")
