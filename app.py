from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from dotenv import load_dotenv
from flask_session import Session

load_dotenv()
app = Flask(__name__)

# to store sessions server-side
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# to track whether we've cleared messages
cleared_once = False

@app.before_request
def clear_messages_on_restart():
    global cleared_once
    if not cleared_once:
        session.pop('messages', None)
        cleared_once = True

@app.route('/')
@app.route('/chatbot')
def chatbot():
    if 'messages' not in session:
        session['messages'] = []
    messages = session['messages']
    return render_template('chatbot.html', messages=messages)

@app.route('/chatbot_ajax', methods=['POST'])
def chatbot_ajax():
    data = request.get_json()
    user_input = data.get('user_input', '').strip()

    if 'messages' not in session:
        session['messages'] = []

    if user_input:
        current_time = datetime.now().strftime("%I:%M %p")

        # Add user message
        session['messages'].append({
            'sender': 'user',
            'text': user_input,
            'time': current_time
        })

        # Bot logic
        if user_input.lower() == 'aadi kesa hai?':
            session['messages'].append({
                'sender': 'bot',
                'text': 'bahut bada mauga hai',
                'time': current_time
            })
        else:
            session['messages'].append({
                'sender': 'bot',
                'text': 'This is a sample response.',
                'time': current_time
            })

        session.modified = True

    return {'messages': session['messages']}

@app.route('/new_chat')
def new_chat():
    session['messages'] = []
    session.modified = True
    return redirect(url_for('chatbot'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email == 'test@example.com' and password == 'password':
            session['logged_in'] = True
            session['username'] = email
            return redirect(url_for('dashboard'))
        else:
            error = "Incorrect email address or password.\nPlease check and try again."
            return render_template('auth/login.html', error=error, message_type='error')

    error = session.pop('error', None)
    return render_template('auth/login.html', error=error, message_type='success' if error else None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=username)

@app.route('/profile')
def profile():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    email = username
    return render_template('profile.html', user_name=username, email=email)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('chatbot'))

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')

        # Simple validation: check if email matches the test user
        if email == 'test@example.com':
            # Redirect to the new check_email page with the email
            return redirect(url_for('check_email', email=email))
        else:
            error = "Email address not found. Please check and try again."
            return render_template('auth/reset_password.html', error=error, message_type='error')

    # On GET request, render the reset password page
    error = session.pop('error', None)
    return render_template('auth/reset_password.html', error=error, message_type='success' if error else None)

@app.route('/check_email')
def check_email():
    email = request.args.get('email', 'user@example.com')  # Default email if none provided
    return render_template('auth/check_email.html', email=email)

if __name__ == '__main__':
    app.run(debug=True)