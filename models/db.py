from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

# User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('ChatMessage', backref='user', lazy=True)

# ChatMessage model for storing chat history
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False)
    text = db.Column(db.Text, nullable=False)
    time = db.Column(db.String(20), nullable=False)

def init_app(app):
    db.init_app(app)
    bcrypt.init_app(app)
    
    with app.app_context():
        db.create_all()