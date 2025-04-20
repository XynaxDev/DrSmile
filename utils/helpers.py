import os
import json
import spacy
import numpy as np

nlp = spacy.load('en_core_web_sm')

base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
json_file = os.path.normpath(os.path.join(base_dir, 'chat_data', 'dentist_responses.json'))

def load_chat_data(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    print(f"Invalid JSON format: {data}")
                    return [], {}
                responses = data.get('dentist_responses', [])
                queries = [entry['query'] for entry in responses]
                query_responses = {entry['query']: entry['response'] for entry in responses}
                return queries, query_responses
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return [], {}
    else:
        print(f"JSON file not found at: {file_path}")
        return [], {}

dentist_queries, dentist_responses = load_chat_data(json_file)

def match_queries(input_text, queries):
    if not input_text or not queries:
        return queries[:5] if queries else []

    input_text = normalize(input_text)
    # Exact or substring match
    exact_match = next((q for q in queries if input_text in normalize(q) or normalize(q) in input_text), None)
    if exact_match:
        return [exact_match] + [q for q in queries if q != exact_match][:4]

    doc_input = nlp(input_text)
    query_docs = [nlp(normalize(q)) for q in queries]
    similarities = [doc_input.similarity(query_doc) for query_doc in query_docs]
    top_indices = np.argsort(similarities)[-5:][::-1]
    return [queries[i] for i in top_indices]

def normalize(text):
    return text.lower().strip().rstrip('?.!')