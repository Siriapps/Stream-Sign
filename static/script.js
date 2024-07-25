const dropArea = document.getElementById('drop-area');
const loader = document.getElementById('loader');

// Prevent default behavior for drag events
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight the drop area when file is dragged over it
dropArea.addEventListener('dragenter', () => dropArea.classList.add('hover'), false);
dropArea.addEventListener('dragleave', () => dropArea.classList.remove('hover'), false);
dropArea.addEventListener('drop', (e) => {
    dropArea.classList.remove('hover');
    handleFiles(e.dataTransfer.files);
}, false);

// Handle file drop
function handleFiles(files) {
    const file = files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        // Show loader
        loader.style.display = 'block';

        // Send file to server
        fetch('/process', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.text())
        .then(html => {
            // Hide loader and update the page with the response
            loader.style.display = 'none';
            document.open();
            document.write(html);
            document.close();
        })
        .catch(error => {
            // Hide loader and log error
            loader.style.display = 'none';
            console.error('Error uploading file:', error);
        });
    }
}

// Optionally, handle click to open file dialog
dropArea.addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*';
    input.onchange = (e) => handleFiles(e.target.files);
    input.click();
});