from flask import Flask, request, jsonify
import fitz
import spacy
from transformers import pipeline
import io

app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# Question Generation Logic
def generate_questions(text):
    doc = nlp(text)
    questions = []

     # Step 1: If text is very long, summarize in chunks
    if len(text) > 1024:
        summarized_chunks = []
        for i in range(0, len(text), 1000):
            chunk = text[i:i+1000]
            summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
            summarized_chunks.append(summary)
        summarized_text = " ".join(summarized_chunks)
    else:
        summarized_text = text

    # Re-analyze with spaCy on summarized content
    doc = nlp(summarized_text)

    # 1. Named Entity Questions
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            questions.append(f"Who is {ent.text}?")
        elif ent.label_ in ['ORG', 'GPE', 'LOC', 'PRODUCT']:
            questions.append(f"What is {ent.text}?")

    # 2. Fact/Definition-based Questions
    if len(questions) < 5:
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if 10 < len(sent_text) < 200 and (" is " in sent_text or " are " in sent_text):
                parts = sent_text.split(" is ")
                if len(parts) == 2:
                    subject = parts[0].strip()
                    questions.append(f"What is {subject}?")
                else:
                    questions.append(f"What is the meaning of: \"{sent_text}\"?")
            if len(questions) >= 10:
                break

    if not questions:
        questions.append("No useful study questions could be generated from this content.")
    
    return questions



# Route: Text Input Processing
@app.route('/process', methods=['POST'])
def process():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    questions = generate_questions(text)
    return jsonify({'questions': '\n'.join(questions)})


# Route: PDF File Processing
@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    pdf_bytes = request.data
    if not pdf_bytes:
        return jsonify({'error': 'No PDF data received'}), 400

    try:
        with fitz.open(io.BytesIO(pdf_bytes)) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")

            full_text = ''
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                print(f"Page {i+1} text: {repr(page_text)}")
                if page_text:
                    full_text += page_text + '\n'

        print("Combined extracted text:", repr(full_text))

        if not full_text.strip():
            return jsonify({'error': 'No text extracted from PDF.'})

        questions = generate_questions(full_text)
        return jsonify({'questions': '\n'.join(questions)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
