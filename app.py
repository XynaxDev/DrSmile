from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta, UTC
from flask_session import Session
from models.db import db, bcrypt, User, ChatMessage, ResetToken, init_app
from dotenv import load_dotenv
from flask_mail import Mail, Message
import os
import json
import secrets

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

base_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True) 
db_path = os.path.join(data_dir, "Users.sqlite3")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_app(app)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(base_dir, 'flask_session')
Session(app)

app.config['SERVER_STARTUP_TIME'] = datetime.now().timestamp()

def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/chatbot')
def chatbot():
    if not session.get('logged_in'):
        current_startup_time = app.config['SERVER_STARTUP_TIME']
        session_startup_time = session.get('server_startup_time', 0)

        if session_startup_time != current_startup_time:
            session['messages'] = [] 
            session['server_startup_time'] = current_startup_time 
            session.modified = True

    if session.get('logged_in'):
        user = User.query.filter_by(email=session.get('email')).first()
        if user:
            messages = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.id.asc()).all()
            messages = [{'sender': msg.sender, 'text': msg.text, 'time': msg.time} for msg in messages]
        else:
            messages = []
    else:
        if 'messages' not in session:
            session['messages'] = []
        messages = session['messages']
    return render_template('chatbot.html', messages=messages)


def normalize(text):
    return text.lower().strip().rstrip('?.!')

@app.route('/chatbot_ajax', methods=['POST'])
def chatbot_ajax():
    data = request.get_json()
    user_input = data.get('user_input', '').strip()
    current_time = datetime.now().strftime("%I:%M %p")

    if not user_input:
        if session.get('logged_in'):
            user = User.query.filter_by(email=session.get('email')).first()
            if not user:
                return jsonify({'error': 'User not found'}), 400
            messages_query = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.id.asc()).all()
            messages = [{'sender': msg.sender, 'text': msg.text, 'time': msg.time} for msg in messages_query]
        else:
            messages = session.get('messages', [])
        return jsonify({'messages': messages})

    dentist_keywords = ['dental', 'dentist', 'tooth', 'teeth', 'cavity', 'implant', 'braces', 'whiten']
    is_dentist_query = any(keyword in user_input.lower() for keyword in dentist_keywords)

    base_dir = os.path.abspath(os.path.dirname(__file__))
    json_file = os.path.normpath(os.path.join(base_dir,'chat_data', 'dentist_responses.json'))

    def load_dentist_responses(file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f: 
                    data = json.load(f)
                    if not isinstance(data, dict):
                        print(f"Invalid JSON format: {data}")
                        return []
                    return data.get('dentist_responses', [])
            except UnicodeDecodeError as e:
                print(f"Unicode decode error in JSON file: {e}")
                return []
            except Exception as e:
                print(f"Error loading JSON: {e}")
                return []
        else:
            print(f"JSON file not found at: {file_path}")
            return []

    responses = load_dentist_responses(json_file)
    if not responses:
        print("Warning: No responses loaded from JSON file")

    default_response = "I'm not sure about that dental query. Please provide more details or consult your dentist."

    # Logged-in user logic
    if session.get('logged_in'):
        user = User.query.filter_by(email=session.get('email')).first()
        if not user:
            return jsonify({'error': 'User not found'}), 400

        user_message = ChatMessage(
            user_id=user.id,
            sender='user',
            text=user_input,
            time=current_time
        )
        db.session.add(user_message)

        # Determine bot response
        normalized_input = normalize(user_input)
        selected_response = default_response

        if user_input.lower() == 'what is my name?':
            selected_response = f" Your name is {user.name}!"
        else:
            for entry in responses:
                query_key = normalize(entry.get('query', ''))
                if query_key in normalized_input or normalized_input in query_key:
                    selected_response = entry.get('response')
                    print(f"Matched '{user_input}' to '{query_key}' -> '{selected_response}'")
                    break
            if selected_response == default_response:
                print(f"No match for '{user_input}' in dentist responses")

        bot_message = ChatMessage(
            user_id=user.id,
            sender='bot',
            text=selected_response,
            time=current_time
        )
        db.session.add(bot_message)
        db.session.commit()

        messages_query = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.id.asc()).all()
        messages = [{'sender': msg.sender, 'text': msg.text, 'time': msg.time} for msg in messages_query]

    # Non-logged-in user logic
    else:
        if 'messages' not in session:
            session['messages'] = []

        user_message = {
            'sender': 'user',
            'text': user_input,
            'time': current_time
        }
        session['messages'].append(user_message)

        # Determine bot response
        normalized_input = normalize(user_input)
        selected_response = default_response

        if user_input.lower() == 'what is my name?':
            selected_response = "You're not logged in, so I don't know your name!"
        else:
            for entry in responses:
                query_key = normalize(entry.get('query', ''))
                if query_key in normalized_input or normalized_input in query_key:
                    selected_response = entry.get('response')
                    print(f"Matched '{user_input}' to '{query_key}' -> '{selected_response}'")
                    break
            if selected_response == default_response:
                print(f"No match for '{user_input}' in dentist responses")

        bot_message = {
            'sender': 'bot',
            'text': selected_response,
            'time': current_time
        }
        session['messages'].append(bot_message)
        session.modified = True
        messages = session['messages']

    response = jsonify({'messages': messages})
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/new_chat')
def new_chat():
    if session.get('logged_in'):
        user = User.query.filter_by(email=session.get('email')).first()
        if user:
            ChatMessage.query.filter_by(user_id=user.id).delete()
            db.session.commit()
    else:
        session['messages'] = []
        session.modified = True
    return redirect(url_for('chatbot'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        if 'last_email' in request.form:
            last_email = request.form.get('last_email', '')
            print(f"last_email from form in login (POST): {last_email}")  
            if last_email:
                session['last_email'] = last_email
                session.modified = True  
            return redirect(url_for('login', email=last_email))

        email = request.form.get('email')
        password = request.form.get('password')

        print(f"Login attempt with email: {email}")  
        session['last_email'] = email
        session.modified = True  #

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = user.name
            session['email'] = user.email
            session.pop('messages', None)
            return redirect(url_for('dashboard'))
        else:
            error = "Incorrect email or password. Please try again."
            return render_template('auth/login.html', error=error, message_type='error', last_email=email)

    last_email = request.args.get('email', session.get('last_email', ''))
    print(f"last_email in login (GET, initial): {last_email}")
    if not last_email:
        last_reset_token = ResetToken.query.order_by(ResetToken.id.desc()).first()
        if last_reset_token:
            user = User.query.get(last_reset_token.user_id)
            if user:
                last_email = user.email
                session['last_email'] = last_email
                session.modified = True
                print(f"Fallback: Retrieved last_email from user in login (GET): {last_email}")
    if last_email and last_email != session.get('last_email', ''):
        session['last_email'] = last_email
        session.modified = True
    
    last_email = last_email if last_email else ''
    print(f"last_email in login (GET, final): {last_email}")
    
    error = None
    message_type = None
    return render_template('auth/login.html', last_email=last_email, error=error, message_type=message_type)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
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

        return redirect(url_for('login'))

    return render_template('auth/register.html', name='', email='')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', username=session.get('username'), email=session.get('email'))

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('email', None)
    session.pop('last_email', None)
    return redirect(url_for('chatbot'))

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            error = "Please enter an email to reset password."
            return render_template('auth/reset_password.html', error=error, message_type='error', last_email='')
        
        session['last_email'] = email
        session.modified = True  # Ensure the session is saved
        print(f"Set session['last_email'] in reset_password: {session['last_email']}")
        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(UTC) + timedelta(hours=1)
            reset_token = ResetToken(user_id=user.id, token=token, expires_at=expires_at)
            db.session.add(reset_token)
            db.session.commit()

            reset_url = url_for('reset_password_confirm', token=token, _external=True)

            msg = Message(
                subject="Reset Your Password - DrSmile",
                recipients=[email],
                html=render_template('auth/reset_email.html', reset_url=reset_url)
            )
            try:
                mail.send(msg)
                print("Email sent successfully to:", email)
            except Exception as e:
                print(f"Email sending failed: {str(e)}")
                error = "Failed to send email. Please try again later."
                return render_template('auth/reset_password.html', error=error, message_type='error', last_email=email)

            return redirect(url_for('check_email', email=email))
        else:
            error = "Email not found. Please try again."
            return render_template('auth/reset_password.html', error=error, message_type='error', last_email=email)

    last_email = request.args.get('email', session.get('last_email', ''))
    print(f"last_email in reset_password (GET): {last_email}")
    return render_template('auth/reset_password.html', last_email=last_email)

@app.route('/check_email')
def check_email():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    email = request.args.get('email', 'user@example.com')
    error = request.args.get('error', None)
    return render_template('auth/check_email.html', email=email, error=error)

@app.route('/resend_email', methods=['POST'])
def resend_email():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    email = request.form.get('email')
    if not email:
        return redirect(url_for('check_email', email='user@example.com', error="No email provided for resend."))
    
    user = User.query.filter_by(email=email).first()
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        reset_token = ResetToken(user_id=user.id, token=token, expires_at=expires_at)
        db.session.add(reset_token)
        db.session.commit()

        reset_url = url_for('reset_password_confirm', token=token, _external=True)

        msg = Message(
            subject="Reset Your Password - DrSmile",
            recipients=[email],
            html=render_template('auth/reset_email.html', reset_url=reset_url)
        )
        try:
            mail.send(msg)
            print("Resend email sent successfully to:", email)
        except Exception as e:
            print(f"Resend email failed: {str(e)}")
            return redirect(url_for('check_email', email=email, error="Failed to resend email. Please try again later."))

    return redirect(url_for('check_email', email=email))

@app.route('/reset_password_confirm/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))

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
        return redirect(url_for('password_reset_success'))

    return render_template('auth/reset_password_confirm.html', token=token, password='', confirm_password='')

@app.route('/password_reset_success')
def password_reset_success():
    last_email = session.get('last_email', '')
    print(f"last_email in password_reset_success (from session): {last_email}")
    if not last_email:  # Fallback: retrieve the email from the last reset token
        last_reset_token = ResetToken.query.order_by(ResetToken.id.desc()).first()
        if last_reset_token:
            user = User.query.get(last_reset_token.user_id)
            if user:
                last_email = user.email
                session['last_email'] = last_email
                session.modified = True
                print(f"Fallback: Retrieved last_email from user: {last_email}")
        if not last_email:  # If still empty, set a default for debugging
            last_email = ''
            print("Warning: Could not retrieve last_email in password_reset_success")
    return render_template('auth/password_reset_success.html', last_email=last_email if last_email else '')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)