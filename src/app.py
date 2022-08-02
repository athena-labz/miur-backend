import os
import connexion
import logging

from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS
from flask_migrate import Migrate
from model import Deliverable, Project, Subject, User, db

load_dotenv()

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
DB_CONN = os.environ.get('DB_CONN')


logging.basicConfig(level=LOGLEVEL,
                    format='%(asctime)s %(levelname)s %(message)s')

cors = CORS(supports_credentials=True)

options = {"swagger_ui": True}
conn = connexion.App(__name__, specification_dir='./api', options=options)
conn.add_api('openapi-spec.yml')
app = conn.app

app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app = conn.app

db.init_app(app)
migrate = Migrate(app, db, compare_type=True)

with app.app_context():
    db.create_all()

cors.init_app(app)

application = app

if __name__ == '__main__':
    app.run(port=8080, debug=True)