let selectedPdf = null;

const uploadSection = document.getElementById('uploadSection');
const loadingSection = document.getElementById('loadingSection');
const quizSection = document.getElementById('quizSection');
const quizContainer = document.getElementById('quizContainer');
const submitBtn = document.getElementById('submitBtn');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');

let currentQuestions = [];

function showSection(section) {
  uploadSection.style.display = 'none';
  loadingSection.style.display = 'none';
  quizSection.style.display = 'none';
  resultsSection.style.display = 'none';

  section.style.display = 'block';
}

document.getElementById('pdfUpload').addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (file && file.type === 'application/pdf') {
    selectedPdf = file;
  } else {
    selectedPdf = null;
    alert("Please upload a valid PDF file.");
  }
});

document.getElementById('processBtn').addEventListener('click', async () => {
  const input = document.getElementById('userInput').value.trim();
  const quizType = document.getElementById('quizType').value;

  if (!input && !selectedPdf) {
    alert("Please enter text or upload a PDF.");
    return;
  }

  showSection(loadingSection);

  try {
    let result;
    if (selectedPdf) {
      const arrayBuffer = await selectedPdf.arrayBuffer();
      result = await window.api.sendPdf(new Uint8Array(arrayBuffer), quizType);
    } else {
      result = await window.api.sendText(input, quizType);
    }

    if (result?.questions) {
      displayQuiz(result.questions);
      showSection(quizSection);
    } else {
      alert("No questions returned.");
      showSection(uploadSection);
    }
  } catch (err) {
    alert("Error: " + err.message);
    showSection(uploadSection);
  }
});

function displayQuiz(questions) {
  quizContainer.innerHTML = '';

  questions.forEach((q, idx) => {
    const questionBox = document.createElement('div');
    questionBox.className = 'box';

    if (typeof q === 'string') {
      questionBox.innerHTML = `<p><strong>Q${idx + 1}:</strong> ${q}</p>`;
    } else {
      questionBox.innerHTML = `<p><strong>Q${idx + 1}:</strong> ${q.question}</p>`;

      if (q.type === 'mcq' && q.options) {
        const ul = document.createElement('ul');
        ul.style.listStyleType = 'none';

        q.options.forEach((opt, i) => {
          const li = document.createElement('li');

          const radio = document.createElement('input');
          radio.type = 'radio';
          radio.name = `question${idx}`;
          radio.id = `q${idx}_opt${i}`;
          radio.value = opt;

          const label = document.createElement('label');
          label.htmlFor = radio.id;
          label.textContent = opt;
          label.style.marginLeft = '8px';

          li.appendChild(radio);
          li.appendChild(label);
          ul.appendChild(li);
        });

        questionBox.appendChild(ul);
      } else if (q.type === 'fill') {
        const input = document.createElement('input');
        input.className = 'input';
        input.placeholder = 'Your answer...';
        questionBox.appendChild(input);
      }
    }

    quizContainer.appendChild(questionBox);
  });
}

submitBtn.addEventListener('click', () => {
    let correct = 0;
    let total = currentQuestions.length;
    resultsContainer.innerHTML = '';

    currentQuestions.forEach((q, idx) => {
        if (typeof q === 'string') return;
        let userAnswer = '';
        let correctAnswer = q.answer || '';

        if (q.type === 'mcq') {
            const selected = document.querySelector(`input[name="question${idx}"]:checked`);
            userAnswer = selected ? selected.value : '';
        } else if (q.type === 'fill') {
            const input = quizContainer.querySelector(`input[data-question-index="${idx}"]`);
            userAnswer = input?.value?.trim() || '';
        }

        const resultBox = document.createElement('div');
        resultBox.className = 'box';

        const isCorrect = userAnswer.toLowerCase() === correctAnswer.toLowerCase();

        resultBox.innerHTML = `
        <p><strong>Q${idx + 1}:</strong> ${q.question}</p>
        <p>Your answer: <em>${userAnswer || '(no answer)'}</em></p>
        <p>Correct answer: <strong>${correctAnswer}</strong></p>
        <p style="color: ${isCorrect ? 'green' : 'red'};">${isCorrect ? 'Correct!' : 'Incorrect'}</p>
        `;

        if (isCorrect) correct++;
        resultsContainer.appendChild(resultBox);
    });

    const summary = document.createElement('div');
    summary.className = 'notification is-info';
    summary.innerHTML = `<strong>You got ${correct} out of ${total} correct.</strong>`;
    resultsContainer.prepend(summary);

    showSection(resultsSection);
});