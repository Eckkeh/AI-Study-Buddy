from flask import Flask, request, jsonify
import fitz
import spacy
from transformers import pipeline
import traceback
import random
import re

app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Helper to normalize answers for comparison (optional, for frontend/backend use)
def normalize_answer(ans):
    return re.sub(r'[^a-z0-9]', '', ans.lower())

# Enhanced Question Generation Logic with Accuracy & Phrasing Fixes
def generate_questions(text, quiz_type="mixed"):
    doc = nlp(text)
    questions = []

    # Summarize long texts
    if len(text) > 1024:
        summarized_chunks = []
        for i in range(0, len(text), 1000):
            chunk = text[i:i+1000]
            summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
            summarized_chunks.append(summary)
        summarized_text = " ".join(summarized_chunks)
    else:
        summarized_text = text

    # Re-analyze with spaCy
    doc = nlp(summarized_text)
    sentences = list(doc.sents)

    # Helper: try to extract definitions for entities
    def find_definition_for_entity(entity_text, sentences):
        for sent in sentences:
            lowered = sent.text.lower()
            if entity_text.lower() in lowered and (" is " in lowered or " are " in lowered):
                if " is " in lowered:
                    parts = sent.text.split(" is ", 1)
                else:
                    parts = sent.text.split(" are ", 1)

                if len(parts) == 2 and parts[0].strip().lower() == entity_text.lower():
                    return parts[1].split('.')[0].strip()
        return None

    # Collect potential distractors
    all_distractors = set()
    for ent in doc.ents:
        all_distractors.add(ent.text.strip())
    for chunk in doc.noun_chunks:
        all_distractors.add(chunk.text.strip())
    all_distractors = list({d for d in all_distractors if 3 < len(d) < 50})
    used_questions = set()

    # Define exceptions for "Where is" phrasing
    where_exceptions = ["capital"]  # add any terms here that should NOT get "Where is"

    # Entity-based MCQ Questions
    if quiz_type in ["mcq", "mixed"]:
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'LOC', 'PRODUCT']:
                entity_text = ent.text.strip()
                if entity_text.lower() in used_questions:
                    continue

                definition = find_definition_for_entity(entity_text, sentences)

                if definition and len(definition.split()) > 2 and entity_text.lower() not in definition.lower():
                    answer_text = definition
                else:
                    continue  # skip weak entries

                distractors = [d for d in all_distractors 
                                if d.lower() != answer_text.lower() 
                                and d.lower() != entity_text.lower()
                                and d.lower() not in used_questions
                                and not d.isupper()
                                and abs(len(d) - len(answer_text)) < 15]

                if len(distractors) < 3:
                    continue

                options = random.sample(distractors, k=3)
                options.append(answer_text)
                random.shuffle(options)

                # Smarter question phrasing for MCQs with exceptions
                if any(word in entity_text.lower() for word in ["statue", "city", "wall", "mountain", "building", "location", "river", "park"]) \
                    and not any(exc in entity_text.lower() for exc in where_exceptions):
                    question_text = f"Where is {entity_text}?"
                else:
                    question_text = f"What is {entity_text}?"

                questions.append({
                    "question": question_text,
                    "options": options,
                    "answer": answer_text,
                    "type": "mcq"
                })

                used_questions.add(entity_text.lower())

    # Definition-style Fill-in-the-Blank Questions
    if quiz_type in ["fill", "mixed"]:
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if 20 < len(sent_text) < 200 and (" is " in sent_text or " are " in sent_text) and sent_text.endswith("."):
                if " is " in sent_text:
                    parts = sent_text.split(" is ", 1)
                else:
                    parts = sent_text.split(" are ", 1)

                subject = parts[0].strip()
                answer = parts[1].strip().split('.')[0]

                if subject.lower() in used_questions or not answer:
                    continue
                if len(answer.split()) < 1:
                    continue

                # Simplify the answer
                simplified = answer.lower()
                for phrase in ["commonly known as", "typically", "located in", "refers to", "is", "are"]:
                    if simplified.startswith(phrase):
                        simplified = simplified.replace(phrase, "").strip()

                # Remove text in parentheses
                if "(" in simplified and ")" in simplified:
                    simplified = simplified.split("(", 1)[0].strip()

                simplified = simplified.strip().capitalize()

                # Smarter question phrasing for fill-in-the-blank with exceptions
                if any(word in subject.lower() for word in ["wall", "statue", "city", "ocean", "river", "mountain", "park", "building", "location"]) \
                    and not any(exc in subject.lower() for exc in where_exceptions):
                    question_text = f"Where is {subject}?"
                else:
                    question_text = f"What is {subject}?"

                questions.append({
                    "question": question_text,
                    "options": [],
                    "answer": simplified,
                    "type": "fill"
                })

                used_questions.add(subject.lower())

                if len(questions) >= 10:
                    break

    if not questions:
        questions.append({
            "question": "No useful study questions could be generated from this content.",
            "options": [],
            "answer": ""
        })

    return questions


# Text route
@app.route('/process', methods=['POST'])
def process():
    data = request.json
    text = data.get('text', '')
    quiz_type = data.get('quiz_type', 'mixed')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    questions = generate_questions(text, quiz_type)
    return jsonify({'questions': questions})


# PDF route
@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    quiz_type = request.headers.get('X-Quiz-Type', 'mixed')
    pdf_bytes = request.data
    if not pdf_bytes:
        return jsonify({'error': 'No PDF data received'}), 400

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
            print(f"PDF has {len(pdf)} pages")

            full_text = ''
            for i, page in enumerate(pdf):
                page_text = page.get_text()
                print(f"Page {i+1} text: {repr(page_text)}")
                if page_text:
                    full_text += page_text + '\n'

        print("Combined extracted text:", repr(full_text))

        if not full_text.strip():
            return jsonify({'error': 'No text extracted from PDF.'})

        questions = generate_questions(full_text, quiz_type)
        return jsonify({'questions': questions}), 200

    except Exception as e:
        print("Exception in /process-pdf route:")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)