// Main JavaScript file

// Utility function to show alerts
function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.role = 'alert';
    
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at the top of the main container
    const container = document.querySelector('.container');
    container.insertBefore(alertContainer, container.firstChild);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertContainer);
        bsAlert.close();
    }, 5000);
}

// Form validation for resume upload
document.addEventListener('DOMContentLoaded', function() {
    const resumeForm = document.querySelector('form[action*="analyze"]');
    
    if (resumeForm) {
        resumeForm.addEventListener('submit', function(event) {
            const uploadOption = document.getElementById('upload-option');
            const pasteOption = document.getElementById('paste-option');
            const resumeFile = document.getElementById('resume-file');
            const resumeText = document.getElementById('resume-text');
            
            let isValid = true;
            let errorMessage = '';
            
            if (uploadOption && uploadOption.checked && resumeFile) {
                if (!resumeFile.files || resumeFile.files.length === 0) {
                    isValid = false;
                    errorMessage = 'Please select a file to upload.';
                }
            } else if (pasteOption && pasteOption.checked && resumeText) {
                if (!resumeText.value.trim()) {
                    isValid = false;
                    errorMessage = 'Please paste your resume text.';
                } else if (resumeText.value.trim().length < 50) {
                    isValid = false;
                    errorMessage = 'Resume text is too short. Please provide more content.';
                }
            }
            
            if (!isValid) {
                event.preventDefault();
                showAlert(errorMessage, 'warning');
            }
        });
    }
    
    // Form validation for job description in anschreiben generator
    const anschreibenForm = document.querySelector('form[action*="anschreiben"]');
    
    if (anschreibenForm) {
        anschreibenForm.addEventListener('submit', function(event) {
            const jobDescription = document.getElementById('job-description');
            
            if (jobDescription && jobDescription.value.trim().length < 50) {
                event.preventDefault();
                showAlert('Please provide a more detailed job description for better results.', 'warning');
            }
        });
    }
});
