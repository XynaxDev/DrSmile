from flask import Flask, render_template
from views.auth import auth_bp, setup_auth
from views.chat import chat_bp
from views.nlp import nlp_bp
from models.db import init_app, db
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_session import Session
from flask_mail import Mail
import datetime
import os

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

    base_dir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "Users.sqlite3")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(base_dir, 'flask_session')
    app.config['SERVER_STARTUP_TIME'] = os.getenv('SERVER_STARTUP_TIME', default=str(datetime.datetime.now().timestamp()))

    # Initialize extensions
    init_app(app)
    Session(app)
    mail = Mail(app)

    # Register blueprints and setup auth
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(nlp_bp, url_prefix='/nlp')

    # Add landing page route
    @app.route('/')
    def index():
        return render_template('landing.html')

    # Setup auth with app
    setup_auth(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)