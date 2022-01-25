import time

from flask import Flask

import config
from models import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.app_context().push()
    db.init_app(app)

    # Connect to database
    tries = 10
    while tries > 0:
        try:
            db.create_all()
            tries = 0
        except:
            tries += -1
            seconds = 10
            print('Failed to connect to database. Waiting %i seconds and then trying again (try countdown: %s)' % (
            seconds, tries))
            time.sleep(seconds)  # Wait a bit until database is loaded

    return app
