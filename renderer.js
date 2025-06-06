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