let selectedPdf = null;

document.getElementById('pdfUpload').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    const output = document.getElementById('output');

    if (!file) return;

    if (file.type !== 'application/pdf') {
        output.textContent = "Error: Please upload a valid PDF file.";
        selectedPdf = null;
        return;
    }

    selectedPdf = file; // Save file for processing later when button is clicked
    output.textContent = "PDF uploaded. Ready to generate quiz.";
});

document.getElementById('processBtn').addEventListener('click', async () => {
    const input = document.getElementById('userInput').value.trim();
    const output = document.getElementById('output');
    output.textContent = "Processing...";

    try {
        let result;

        if (selectedPdf) {
            const arrayBuffer = await selectedPdf.arrayBuffer();
            result = await window.api.sendPdf(new Uint8Array(arrayBuffer));
        } else if (input) {
            result = await window.api.sendText(input);
        } else {
            output.textContent = "Please enter text or upload a PDF.";
            return;
        }

        console.log("API result:", result);
        output.textContent = result?.questions
            ? `Quiz Questions:\n${result.questions}`
            : "No questions returned.";
    } catch (err) {
        output.textContent = `Error: ${err.message}`;
    }
});