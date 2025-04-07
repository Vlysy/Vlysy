// Main JavaScript for Resume Analyzer

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize file upload enhancement
    enhanceFileUpload();
    
    // Initialize correction selection functionality
    setupCorrectionSelection();
    
    // Add smooth animations to elements
    addEntryAnimations();
    
    // Initialize progress bars with animation
    animateProgressBars();
    
    // Setup language toggle
    setupLanguageToggle();
    
    // Score tooltips
    setupScoreTooltips();
});

// Initialize Bootstrap tooltips
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Enhance file upload with drag and drop
function enhanceFileUpload() {
    const fileUploadArea = document.querySelector('.file-upload-area');
    const fileInput = document.querySelector('#resume_file');
    
    if (!fileUploadArea || !fileInput) return;
    
    // Add drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileUploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        fileUploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileUploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        fileUploadArea.classList.add('drag-over');
    }
    
    function unhighlight() {
        fileUploadArea.classList.remove('drag-over');
    }
    
    fileUploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        
        // Update file name display
        const fileNameDisplay = document.querySelector('.file-name-display');
        if (fileNameDisplay && files.length > 0) {
            fileNameDisplay.textContent = files[0].name;
        }
    }
    
    // Show selected filename
    fileInput.addEventListener('change', function() {
        const fileNameDisplay = document.querySelector('.file-name-display');
        if (fileNameDisplay && this.files.length > 0) {
            fileNameDisplay.textContent = this.files[0].name;
        }
    });
}

// Setup correction selection functionality
function setupCorrectionSelection() {
    const correctionCheckboxes = document.querySelectorAll('.correction-checkbox');
    const applySelectedBtn = document.querySelector('#apply_selected');
    const resumeTextarea = document.querySelector('#corrected_text');
    
    if (!correctionCheckboxes.length || !applySelectedBtn || !resumeTextarea) return;
    
    // Enable "Apply Selected" button when checkboxes are selected
    correctionCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const checkedBoxes = document.querySelectorAll('.correction-checkbox:checked');
            applySelectedBtn.disabled = checkedBoxes.length === 0;
        });
    });
    
    // Apply corrections when button is clicked
    applySelectedBtn.addEventListener('click', function() {
        const checkedBoxes = document.querySelectorAll('.correction-checkbox:checked');
        if (checkedBoxes.length === 0) return;
        
        // Gather selected corrections
        const selectedCorrections = [];
        checkedBoxes.forEach(checkbox => {
            const correctionId = checkbox.getAttribute('data-correction-id');
            const correctionData = JSON.parse(document.querySelector(`#correction_data_${correctionId}`).textContent);
            selectedCorrections.push(correctionData);
        });
        
        // Get current resume text
        const resumeText = resumeTextarea.value;
        
        // Send to server to apply corrections
        fetch('/apply_corrections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                selected_corrections: selectedCorrections,
                resume_text: resumeText
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.corrected_text) {
                // Update textarea with corrected text
                resumeTextarea.value = data.corrected_text;
                
                // Show success message
                const alertBox = document.createElement('div');
                alertBox.className = 'alert alert-success alert-dismissible fade show mt-3';
                alertBox.innerHTML = `
                    <strong>Success!</strong> Applied ${selectedCorrections.length} correction(s).
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                const alertContainer = document.querySelector('.alert-container');
                if (alertContainer) {
                    alertContainer.appendChild(alertBox);
                    
                    // Auto dismiss after 5 seconds
                    setTimeout(() => {
                        alertBox.classList.remove('show');
                        setTimeout(() => alertBox.remove(), 500);
                    }, 5000);
                }
                
                // Uncheck all checkboxes
                checkedBoxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Disable apply button
                applySelectedBtn.disabled = true;
            }
        })
        .catch(error => {
            console.error('Error applying corrections:', error);
            
            // Show error message
            const alertBox = document.createElement('div');
            alertBox.className = 'alert alert-danger alert-dismissible fade show mt-3';
            alertBox.innerHTML = `
                <strong>Error!</strong> Failed to apply corrections. Please try again.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            const alertContainer = document.querySelector('.alert-container');
            if (alertContainer) {
                alertContainer.appendChild(alertBox);
            }
        });
    });
}

// Add entry animations to elements
function addEntryAnimations() {
    // Add fade-in class to main content elements
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
    
    // Add slide-in animation to correction items with delay
    const correctionItems = document.querySelectorAll('.correction-item');
    correctionItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
        item.classList.add('slide-in');
    });
    
    // Add scale-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('scale-in');
    });
}

// Animate progress bars
function animateProgressBars() {
    // Animate overall score circle
    const scoreCircle = document.querySelector('.overall-score-circle');
    if (scoreCircle) {
        // Add a small delay for visual effect
        setTimeout(() => {
            scoreCircle.style.opacity = 1;
        }, 300);
    }
    
    // Animate category score bars
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach((bar, index) => {
        const originalWidth = bar.style.width;
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.width = originalWidth;
        }, 500 + (index * 100));
    });
}

// Setup language toggle
function setupLanguageToggle() {
    const languageButtons = document.querySelectorAll('.language-selector .btn');
    
    if (!languageButtons.length) return;
    
    languageButtons.forEach(button => {
        button.addEventListener('click', function() {
            languageButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Update hidden input value
            const languageInput = document.querySelector('input[name="language"]');
            if (languageInput) {
                languageInput.value = this.getAttribute('data-value');
            }
        });
    });
}

// Setup score tooltips
function setupScoreTooltips() {
    const scoreLabels = {
        'content': 'Measures the quality, relevance, and completeness of your resume content.',
        'format': 'Evaluates the layout, organization, and visual appeal of your resume.',
        'language': 'Assesses grammar, spelling, word choice, and overall writing quality.',
        'conciseness': 'Checks how efficiently you communicate information without unnecessary words.'
    };
    
    const scoreElements = document.querySelectorAll('.category-scores .d-flex span:first-child');
    
    scoreElements.forEach(element => {
        const category = element.textContent.toLowerCase();
        if (scoreLabels[category]) {
            element.classList.add('score-tooltip');
            element.setAttribute('data-tooltip', scoreLabels[category]);
        }
    });
}
