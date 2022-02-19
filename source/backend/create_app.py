""" Create flask app and connect to database """
import time
from flask import Flask
from sqlalchemy.exc import OperationalError
import config
from models import db


def create_app():
    """
    Creates the app and connects to database
    :return Flask app instance
    """
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
        except OperationalError:
            tries += -1
            seconds = 10
            print(f'Failed to connect to database. '
                  f'Waiting {seconds} seconds and then trying again (try countdown: {tries})')
            time.sleep(seconds)  # Wait a bit until database is loaded

    return app
