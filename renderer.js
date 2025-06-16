let selectedPdf = null;

const uploadSection = document.getElementById('uploadSection');
const loadingSection = document.getElementById('loadingSection');
const quizSection = document.getElementById('quizSection');
const quizContainer = document.getElementById('quizContainer');

function showSection(section) {
  uploadSection.style.display = 'none';
  loadingSection.style.display = 'none';
  quizSection.style.display = 'none';

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
        q.options.forEach(opt => {
          const li = document.createElement('li');
          li.textContent = opt;
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