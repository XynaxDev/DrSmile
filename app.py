from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from dotenv import load_dotenv
from flask_session import Session

load_dotenv()
app = Flask(__name__)


# ADDED: configure Flask-Session to store sessions server-side
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/')
@app.route('/chatbot')
def chatbot():
    # Just render the chatbot page. The actual message logic is in /chatbot_ajax
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
        return redirect(url_for('dashboard'))
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', user_name="John Doe")

@app.route('/profile')
def profile():
    return render_template('profile.html', user_name="John Doe", email="johndoe@example.com")

if __name__ == '__main__':
    app.run(debug=True)
