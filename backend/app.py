from flask import Flask, request, jsonify
import fitz
import spacy
from transformers import pipeline
import traceback
import random

app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# Enhanced Question Generation Logic with Multiple Choice
def generate_questions(text):
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

    # Collect potential distractors
    all_distractors = set()
    for ent in doc.ents:
        all_distractors.add(ent.text.strip())
    for chunk in doc.noun_chunks:
        all_distractors.add(chunk.text.strip())
    all_distractors = list({d for d in all_distractors if 3 < len(d) < 50})
    used_questions = set()

    # Entity-based Questions
    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'GPE', 'LOC', 'PRODUCT']:
            correct = ent.text.strip()
            if correct.lower() in used_questions:
                continue
            used_questions.add(correct.lower())

            distractors = [d for d in all_distractors if d.lower() != correct.lower()]
            options = random.sample(distractors, k=3) if len(distractors) >= 3 else distractors[:]
            options.append(correct)
            random.shuffle(options)

            questions.append({
                "question": f"What is {correct}?",
                "options": options,
                "answer": correct,
                "type": "mcq"
            })

    # Definition-style Questions
    if len(questions) < 5:
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if 10 < len(sent_text) < 200 and (" is " in sent_text or " are " in sent_text):
                parts = sent_text.split(" is ")
                if len(parts) == 2:
                    subject = parts[0].strip()
                    answer = parts[1].strip().split('.')[0]
                else:
                    subject = sent_text
                    answer = sent_text

                if subject.lower() in used_questions or not answer:
                    continue
                used_questions.add(subject.lower())

                distractors = [d for d in all_distractors if d.lower() != answer.lower()]
                options = random.sample(distractors, k=3) if len(distractors) >= 3 else distractors[:]
                options.append(answer)
                random.shuffle(options)

                questions.append({
                    "question": f"What is {subject}?",
                    "options": [],
                    "answer": answer,
                    "type": "fill"
                })

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
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    questions = generate_questions(text)
    return jsonify({'questions': questions})


# PDF route
@app.route('/process-pdf', methods=['POST'])
def process_pdf():
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

        questions = generate_questions(full_text)
        return jsonify({'questions': questions}), 200

    except Exception as e:
        print("Exception in /process-pdf route:")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
