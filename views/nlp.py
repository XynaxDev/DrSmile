from flask import Blueprint, request, jsonify
from utils.helpers import match_queries, dentist_queries, dentist_responses, nlp

nlp_bp = Blueprint('nlp', __name__)

def is_meaningful_input(text):
    if not text or not text.strip():
        return False
    doc = nlp(text)
    return any(token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV'] for token in doc)

@nlp_bp.route('/api/nlp_match', methods=['POST'])
def nlp_match():
    data = request.get_json()
    input_text = data.get('input', '').strip()
    matched_queries = match_queries(input_text, dentist_queries) if input_text else dentist_queries[:5]
    return jsonify({
        'matchedQueries': matched_queries,
        'responses': {q: dentist_responses.get(q, "No response available") for q in matched_queries}
    })