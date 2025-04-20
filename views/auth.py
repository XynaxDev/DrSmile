from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from flask import current_app  # Import current_app for app context
from models.db import db, bcrypt, User, ChatMessage, ResetToken
from flask_mail import Message
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
import os
import secrets
from utils.helpers import normalize

load_dotenv()

auth_bp = Blueprint('auth', __name__)

# Global Mail instance (will be set by setup_auth)
mail = None

def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# Setup function to initialize Mail
def setup_auth(app):
    global mail
    mail = app.extensions['mail']  # Set the Mail instance

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        if 'last_email' in request.form:
            last_email = request.form.get('last_email', '')
            print(f"last_email from form in login (POST): {last_email}")  
            if last_email:
                session['last_email'] = last_email
                session.modified = True  
            return redirect(url_for('auth.login', email=last_email))

        email = request.form.get('email')
        password = request.form.get('password')

        print(f"Login attempt with email: {email}")  
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = user.name
            session['email'] = user.email
            session['last_email'] = email  # Set last_email only on successful login
            session.modified = True
            session.pop('messages', None)
            return redirect(url_for('auth.dashboard'))
        else:
            error = "Incorrect email or password. Please try again."
            # Use the attempted email for the form on failure, not session['last_email']
            return render_template('auth/login.html', error=error, message_type='error', last_email=email if email else '')

    # Use session['last_email'] as the default, only if no other input
    last_email = session.get('last_email', '')
    print(f"last_email in login (GET, initial from session): {last_email}")
    if not last_email:  # Fallback only if session is empty
        last_reset_token = ResetToken.query.order_by(ResetToken.id.desc()).first()
        if last_reset_token:
            user = User.query.get(last_reset_token.user_id)
            if user:
                last_email = user.email
                session['last_email'] = last_email
                session.modified = True
                print(f"Fallback: Retrieved last_email from user in login (GET): {last_email}")
    print(f"last_email in login (GET, final): {last_email}")
    
    error = None
    message_type = None
    return render_template('auth/login.html', last_email=last_email, error=error, message_type=message_type)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('logged_in'):
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([name, email, password]):
            error = "All fields are required."
            error_type = "required"
            highlight_password = False
            return render_template('auth/register.html', error=error, message_type='error', error_type=error_type, 
                                 highlight_password=highlight_password, name=name, email=email)

        if len(password) < 8:
            error = "Password must be at least 8 characters long."
            error_type = "length"
            highlight_password = True
            return render_template('auth/register.html', error=error, message_type='error', error_type=error_type, 
                                 highlight_password=highlight_password, name=name, email=email)

        if User.query.filter_by(email=email).first():
            error = "Email already registered."
            error_type = "email_exists"
            highlight_password = False
            return render_template('auth/register.html', error=error, message_type='error', error_type=error_type, 
                                 highlight_password=highlight_password, name=name, email=email)

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', name='', email='')

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', username=session.get('username'), email=session.get('email'))

@auth_bp.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('email', None)
    session.pop('last_email', None)  # Clear last_email on logout
    return redirect(url_for('chat.chatbot'))

@auth_bp.route('/terms')
def terms():
    return render_template('terms.html')

@auth_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if session.get('logged_in'):
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            error = "Please enter an email to reset password."
            return render_template('auth/reset_password.html', error=error, message_type='error', last_email='')
        
        session['last_email'] = email
        session.modified = True  
        print(f"Set session['last_email'] in reset_password: {session['last_email']}")
        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(UTC) + timedelta(hours=1)
            reset_token = ResetToken(user_id=user.id, token=token, expires_at=expires_at)
            db.session.add(reset_token)
            db.session.commit()

            reset_url = url_for('auth.reset_password_confirm', token=token, _external=True)

            msg = Message(
                subject="Reset Your Password - DrSmile",
                recipients=[email],
                html=render_template('auth/reset_email.html', reset_url=reset_url)
            )
            try:
                with current_app.app_context():  # Use current_app for context
                    mail.send(msg)
                print("Email sent successfully to:", email)
            except Exception as e:
                print(f"Email sending failed: {str(e)}")
                error = "Failed to send email. Please try again later."
                return render_template('auth/reset_password.html', error=error, message_type='error', last_email=email)

            return redirect(url_for('auth.check_email', email=email))
        else:
            error = "Email not found. Please try again."
            return render_template('auth/reset_password.html', error=error, message_type='error', last_email=email)

    last_email = request.args.get('email', session.get('last_email', ''))
    print(f"last_email in reset_password (GET): {last_email}")
    return render_template('auth/reset_password.html', last_email=last_email)

@auth_bp.route('/check_email')
def check_email():
    if session.get('logged_in'):
        return redirect(url_for('auth.dashboard'))
    email = request.args.get('email', 'user@example.com')
    error = request.args.get('error', None)
    return render_template('auth/check_email.html', email=email, error=error)

@auth_bp.route('/resend_email', methods=['POST'])
def resend_email():
    if session.get('logged_in'):
        return redirect(url_for('auth.dashboard'))
    
    email = request.form.get('email')
    if not email:
        return redirect(url_for('auth.check_email', email='user@example.com', error="No email provided for resend."))
    
    user = User.query.filter_by(email=email).first()
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        reset_token = ResetToken(user_id=user.id, token=token, expires_at=expires_at)
        db.session.add(reset_token)
        db.session.commit()

        reset_url = url_for('auth.reset_password_confirm', token=token, _external=True)

        msg = Message(
            subject="Reset Your Password - DrSmile",
            recipients=[email],
            html=render_template('auth/reset_email.html', reset_url=reset_url)
        )
        try:
            with current_app.app_context():  # Use current_app for context
                mail.send(msg)
            print("Resend email sent successfully to:", email)
        except Exception as e:
            print(f"Resend email failed: {str(e)}")
            return redirect(url_for('auth.check_email', email=email, error="Failed to resend email. Please try again later."))

    return redirect(url_for('auth.check_email', email=email))

@auth_bp.route('/reset_password_confirm/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    if session.get('logged_in'):
        return redirect(url_for('auth.dashboard'))

    reset_token = ResetToken.query.filter_by(token=token).first()
    if not reset_token:
        error = "Invalid or expired reset link. Please request a new one."
        return render_template('auth/reset_password.html', error=error, message_type='error', last_email='')

    from datetime import timezone
    expires_at = reset_token.expires_at.replace(tzinfo=timezone.utc) if reset_token.expires_at.tzinfo is None else reset_token.expires_at
    if expires_at < datetime.now(UTC):
        error = "Invalid or expired reset link. Please request a new one."
        return render_template('auth/reset_password.html', error=error, message_type='error', last_email='')

    user = User.query.get(reset_token.user_id)
    print(f"session['last_email'] in reset_password_confirm: {session.get('last_email', '')}")
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            error = "All fields are required."
            error_type = "required"
            highlight_password = False
            return render_template('auth/reset_password_confirm.html', error=error, message_type='error', error_type=error_type, 
                                 highlight_password=highlight_password, token=token, password=password, confirm_password=confirm_password)
        
        if password != confirm_password:
            error = "Passwords do not match."
            error_type = "mismatch"
            highlight_password = True
            return render_template('auth/reset_password_confirm.html', error=error, message_type='error', error_type=error_type, 
                                 highlight_password=highlight_password, token=token, password=password, confirm_password=confirm_password)

        if len(password) < 8:
            error = "Password must be at least 8 characters long."
            error_type = "length"
            highlight_password = True
            return render_template('auth/reset_password_confirm.html', error=error, message_type='error', error_type=error_type, 
                                 highlight_password=highlight_password, token=token, password=password, confirm_password=confirm_password)

        if bcrypt.check_password_hash(user.password, password):
            error = "Password has previously been used."
            error_type = "reuse"
            highlight_password = True
            return render_template('auth/reset_password_confirm.html', error=error, message_type='error', error_type=error_type, 
                                 highlight_password=highlight_password, token=token, password=password, confirm_password=confirm_password)

        user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.delete(reset_token)
        db.session.commit()
        return redirect(url_for('auth.password_reset_success'))

    return render_template('auth/reset_password_confirm.html', token=token, password='', confirm_password='')

@auth_bp.route('/password_reset_success')
def password_reset_success():
    last_email = session.get('last_email', '')
    print(f"last_email in password_reset_success (from session): {last_email}")
    if not last_email:
        last_reset_token = ResetToken.query.order_by(ResetToken.id.desc()).first()
        if last_reset_token:
            user = User.query.get(last_reset_token.user_id)
            if user:
                last_email = user.email
                session['last_email'] = last_email
                session.modified = True
                print(f"Fallback: Retrieved last_email from user: {last_email}")
        if not last_email: 
            last_email = ''
            print("Warning: Could not retrieve last_email in password_reset_success")
    return render_template('auth/password_reset_success.html', last_email=last_email if last_email else '')