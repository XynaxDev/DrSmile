from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from flask_session import Session
from models.db import db, bcrypt, User, ChatMessage, init_app  # Import ChatMessage
from dotenv import load_dotenv
import os

load_dotenv()

# Create Flask app
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "data", "Users.sqlite3")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_app(app)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
@app.route('/chatbot')
def chatbot():
    if session.get('logged_in'):
        # Logged-in user: fetch persistent chat history from database
        user = User.query.filter_by(email=session.get('email')).first()
        if user:
            messages = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.id.asc()).all()
            messages = [{'sender': msg.sender, 'text': msg.text, 'time': msg.time} for msg in messages]
        else:
            messages = []
    else:
        # Not logged in: use temporary session-based chat history
        if 'messages' not in session:
            session['messages'] = []
        messages = session['messages']
    return render_template('chatbot.html', messages=messages)

@app.route('/chatbot_ajax', methods=['POST'])
def chatbot_ajax():
    data = request.get_json()
    user_input = data.get('user_input', '').strip()

    if not user_input:
        if session.get('logged_in'):
            user = User.query.filter_by(email=session.get('email')).first()
            messages = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.id.asc()).all()
            messages = [{'sender': msg.sender, 'text': msg.text, 'time': msg.time} for msg in messages]
        else:
            messages = session.get('messages', [])
        return jsonify({'messages': messages})

    current_time = datetime.now().strftime("%I:%M %p")
    
    if session.get('logged_in'):
        # Logged-in user: store in database
        user = User.query.filter_by(email=session.get('email')).first()
        if not user:
            return jsonify({'error': 'User not found'}), 400

        # Save user message
        user_message = ChatMessage(
            user_id=user.id,
            sender='user',
            text=user_input,
            time=current_time
        )
        db.session.add(user_message)

        # Bot response
        if user_input.lower() == 'what is my name?':
            bot_response = ChatMessage(
                user_id=user.id,
                sender='bot',
                text=user.name,  # Use the user's actual name
                time=current_time
            )
        else:
            bot_response = ChatMessage(
                user_id=user.id,
                sender='bot',
                text='This is a sample response.',
                time=current_time
            )
        db.session.add(bot_response)
        db.session.commit()

        # Fetch all messages for this user
        messages = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.id.asc()).all()
        messages = [{'sender': msg.sender, 'text': msg.text, 'time': msg.time} for msg in messages]
    else:
        # Not logged in: store in session (temporary)
        if 'messages' not in session:
            session['messages'] = []

        session['messages'].append({
            'sender': 'user',
            'text': user_input,
            'time': current_time
        })

        # Bot response
        if user_input.lower() == 'what is my name?':
            session['messages'].append({
                'sender': 'bot',
                'text': 'You’re not logged in, so I don’t know your name!',
                'time': current_time
            })
        else:
            session['messages'].append({
                'sender': 'bot',
                'text': 'This is a sample response.',
                'time': current_time
            })
        session.modified = True
        messages = session['messages']

    return jsonify({'messages': messages})

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
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = user.name
            session['email'] = user.email
            session.pop('messages', None)
            return redirect(url_for('dashboard'))
        else:
            error = "Incorrect email or password. Please try again."
            return render_template('auth/login.html', error=error, message_type='error')

    return render_template('auth/login.html')

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
            return render_template('auth/register.html', error=error, message_type='error')

        if User.query.filter_by(email=email).first():
            error = "Email already registered."
            return render_template('auth/register.html', error=error, message_type='error')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('auth/register.html')

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
        user = User.query.filter_by(email=email).first()

        if user:
            return redirect(url_for('check_email', email=email))
        else:
            error = "Email not found. Please try again."
            return render_template('auth/reset_password.html', error=error, message_type='error', last_email=email)

    last_email = session.get('last_email', '')
    return render_template('auth/reset_password.html', last_email=last_email)

@app.route('/check_email')
def check_email():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    email = request.args.get('email', 'user@example.com')
    return render_template('auth/check_email.html', email=email)

if __name__ == '__main__':
    app.run(debug=True)