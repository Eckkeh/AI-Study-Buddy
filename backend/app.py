from flask import Flask, request, jsonify
import pdfplumber
import spacy
from transformers import pipeline

app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    doc = nlp(text)
    questions = []

    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            questions.append(f"Who is {ent.text}?")
        elif ent.label_ in ['ORG', 'GPE', 'LOC', 'PRODUCT']:
            questions.append(f"What is {ent.text}?")

    if len(questions) < 3:
        for sent in doc.sents:
            words = [token.text.lower() for token in sent]
            if 'is' in words or 'are' in words:
                questions.append(f"What is the meaning of: \"{sent.text.strip()}\"?")
            if len(questions) >= 5:
                break

    return jsonify({'summary': '\n'.join(questions) or "No study questions generated."})

if __name__ == '__main__':
    app.run(debug=False)