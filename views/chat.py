from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models.db import db, User, ChatMessage
from datetime import datetime
from utils.helpers import normalize, match_queries, dentist_queries, dentist_responses, nlp

chat_bp = Blueprint('chat', __name__)

def is_meaningful_input(text):
    if not text or not isinstance(text, str):
        return False
    text = normalize(text)
    return any(text in normalize(q) or normalize(q) in text for q in dentist_queries) or \
           any(kw in text for kw in ['dental', 'dentist', 'tooth', 'teeth', 'cavity', 'implant', 'braces', 'whiten', 'oral', 'gum', 'hygiene'])

@chat_bp.route('/chatbot')
def chatbot():
    if not session.get('logged_in'):
        current_startup_time = session.get('server_startup_time', 0)
        if current_startup_time != session.get('server_startup_time', 0):
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

@chat_bp.route('/chatbot_ajax', methods=['POST'])
def chatbot_ajax():
    data = request.get_json()
    user_input = data.get('user_input', '').strip()
    current_time = datetime.now().strftime("%I:%M %p")

    if not session.get('logged_in'):
        messages = session.get('messages', [])
    else:
        user = User.query.filter_by(email=session.get('email')).first()
        if not user:
            return jsonify({'error': 'User not found'}), 400
        messages = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.id.asc()).all()
        messages = [{'sender': msg.sender, 'text': msg.text, 'time': msg.time} for msg in messages]

    suggestions = []
    if user_input:
        user_message = {'sender': 'user', 'text': user_input, 'time': current_time}

        if not session.get('logged_in'):
            if not any(msg['text'] == user_input and msg['time'] == current_time for msg in session['messages']):
                session['messages'].append(user_message)
                session.modified = True
            messages = session['messages']
        else:
            if not ChatMessage.query.filter_by(user_id=user.id, text=user_input, time=current_time).first():
                db_user_message = ChatMessage(user_id=user.id, **user_message)
                db.session.add(db_user_message)
                db.session.commit()
            messages.append(user_message)

        if not is_meaningful_input(user_input):
            bot_response = {'sender': 'bot', 'text': 'The input does not appear to be a dental-related query. Please provide a question related to dental care.', 'time': current_time}
        else:
            print(f"Processing input: {user_input}")
            suggestions = match_queries(user_input, dentist_queries)
            print(f"Suggestions: {suggestions}")
            matched_query = next((q for q in suggestions if normalize(q) in normalize(user_input) or normalize(user_input) in normalize(q)), suggestions[0] if suggestions else None)
            response = dentist_responses.get(matched_query, "I could not find a specific match. Please provide a more detailed dental-related question.")
            print(f"Matched query: {matched_query}, Response: {response}")
            bot_response = {'sender': 'bot', 'text': response, 'time': current_time}

        if not session.get('logged_in'):
            if not any(msg['text'] == bot_response['text'] and msg['time'] == current_time for msg in session['messages']):
                session['messages'].append(bot_response)
                session.modified = True
            messages = session['messages']
        else:
            if not ChatMessage.query.filter_by(user_id=user.id, text=bot_response['text'], time=current_time).first():
                db_bot_message = ChatMessage(user_id=user.id, **bot_response)
                db.session.add(db_bot_message)
                db.session.commit()
            messages.append(bot_response)

    return jsonify({'messages': messages, 'suggestions': suggestions})

@chat_bp.route('/new_chat')
def new_chat():
    if session.get('logged_in'):
        user = User.query.filter_by(email=session.get('email')).first()
        if user:
            ChatMessage.query.filter_by(user_id=user.id).delete()
            db.session.commit()
    else:
        session['messages'] = []
        session.modified = True
    return redirect(url_for('chat.chatbot'))