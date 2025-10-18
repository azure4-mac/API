from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(app)

    database_url = os.getenv('DATABASE_URL') or 'sqlite:///kahoot.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "CHAVE_SUPER_SECRETA_DEV")

    db.init_app(app)

    from app.routes import init_routes
    init_routes(app)

    with app.app_context():
        db.create_all()

    return app
