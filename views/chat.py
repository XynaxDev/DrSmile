from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models.db import db, User, ChatMessage
from datetime import datetime
from utils.helpers import normalize, match_queries, dentist_queries, dentist_responses, nlp
from views.nlp import is_meaningful_input

chat_bp = Blueprint('chat', __name__)

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

        if not is_meaningful_input(user_input) or not any(kw in user_input.lower() for kw in ['dental', 'dentist', 'tooth', 'teeth', 'cavity', 'implant', 'braces', 'whiten', 'oral', 'gum', 'hygiene']):
            bot_response = {'sender': 'bot', 'text': 'The input does not appear to be a dental-related query. Please provide a question related to dental care.', 'time': current_time}
        else:
            default_response = 'I could not find a specific match. Please provide a more detailed dental-related question.'
            matched_queries = match_queries(user_input, dentist_queries)
            matched_query = next((q for q in matched_queries if normalize(q) in normalize(user_input) or normalize(user_input) in normalize(q)), None)
            if not matched_query and matched_queries:
                similarity_threshold = 0.8
                doc_input = nlp(user_input.lower())
                query_docs = [nlp(q.lower()) for q in matched_queries]
                similarities = [doc_input.similarity(q) for q in query_docs]
                max_similarity = max(similarities) if similarities else 0
                matched_query = matched_queries[0] if max_similarity >= similarity_threshold and matched_queries[0] in dentist_responses else None
            selected_response = dentist_responses.get(matched_query, default_response)
            if matched_query:
                print(f"Matched '{user_input}' to '{matched_query}' -> '{selected_response}'")
            else:
                print(f"No precise match for '{user_input}' in dentist responses")
            bot_response = {'sender': 'bot', 'text': selected_response, 'time': current_time}

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

    return jsonify({'messages': messages})

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