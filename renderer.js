document.getElementById('processBtn').addEventListener('click', async () => {
    const input = document.getElementById('userInput').value;
    const output = document.getElementById('output');
    output.textContent = "Processing...";

    try {
        const result = await window.api.sendText(input);
        output.textContent = `Summary:\n${result.summary}`;
    } catch (err) {
        output.textContent = `Error: ${err.message}`;
    }
});

document.getElementById('pdfUpload').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    const output = document.getElementById('output');

    if (!file) return;

    if (file.type !== 'application/pdf') {
        output.textContent = "Error: Please upload a valid PDF file.";
        return;
    }

    output.textContent = "Extracting text from PDF...";

    try {
        const arrayBuffer = await file.arrayBuffer();
        const result = await window.api.sendPdf(new Uint8Array(arrayBuffer));
        output.textContent = `Summary from PDF:\n${result.summary}`;
    } catch (err) {
        output.textContent = `Error: ${err.message}`;
    }
});