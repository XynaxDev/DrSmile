from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

# Initialize SQLAlchemy and Bcrypt (will be passed from app.py)
db = SQLAlchemy()
bcrypt = Bcrypt()

# User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # Stores hashed password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_app(app):
    """Initialize the database and bcrypt with the Flask app."""
    db.init_app(app)
    bcrypt.init_app(app)
    
    # Create the database tables
    with app.app_context():
        db.create_all()