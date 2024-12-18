document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const uploadMessage = document.getElementById('upload-message');
    const qaForm = document.getElementById('qa-form');
    const qaMessage = document.getElementById('qa-message');
    const documentContent = document.getElementById('document-content');
    const documentImages = document.getElementById('document-images');

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const fileInput = document.getElementById('file-input');
        const file = fileInput.files[0];

        if (!file) {
            uploadMessage.textContent = 'Please select a file.';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                uploadMessage.textContent = `File uploaded and processed. Document ID: ${data.doc_id}`;
            } else {
                uploadMessage.textContent = data.error;
            }
        } catch (error) {
            uploadMessage.textContent = 'An error occurred while uploading the file.';
        }
    });

    qaForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const docId = document.getElementById('doc-id').value;
        const question = document.getElementById('question').value;

        if (!docId || !question) {
            qaMessage.textContent = 'Please provide both Document ID and question.';
            return;
        }

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ doc_id: docId, question: question })
            });
            const data = await response.json();
            if (response.ok) {
                qaMessage.textContent = `Answer: ${data.answer}`;
            } else {
                qaMessage.textContent = data.error;
            }
        } catch (error) {
            qaMessage.textContent = 'An error occurred while asking the question.';
        }
    });

    document.getElementById('doc-id').addEventListener('input', async (event) => {
        const docId = event.target.value;
        if (docId) {
            try {
                const response = await fetch(`/document/${docId}`);
                const data = await response.json();
                if (response.ok) {
                    documentContent.textContent = data.text; // Display only the text content
                    documentImages.innerHTML = ''; // Clear previous images

                    // Display images
                    data.images.forEach(image => {
                        const imgElement = document.createElement('img');
                        imgElement.src = `data:image/png;base64,${image.data}`;
                        imgElement.alt = `Image on page ${image.page}, index ${image.image_index}`;
                        documentImages.appendChild(imgElement);
                    });
                } else {
                    documentContent.textContent = data.error;
                    documentImages.innerHTML = ''; // Clear images on error
                }
            } catch (error) {
                documentContent.textContent = 'An error occurred while fetching the document.';
                documentImages.innerHTML = ''; // Clear images on error
            }
        } else {
            documentContent.textContent = '';
            documentImages.innerHTML = ''; // Clear images when docId is empty
        }
    });
});
